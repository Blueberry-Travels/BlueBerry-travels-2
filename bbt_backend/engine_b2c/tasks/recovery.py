"""
Recovery and failure ladder tasks.
Handles disruptions, force majeure, and failed external API bookings.
"""
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=5, default_retry_delay=300)
def retry_failed_external_booking(self, line_item_id: str):
    """
    Retries a failed external API booking (RedBus, IRCTC, Booking.com).
    Exponential backoff: 5min, 10min, 20min, 40min, 80min.
    After 5 failures → cancel + full refund.
    """
    try:
        from engine_b2c.models import BookingLineItem
        li = BookingLineItem.objects.get(id=line_item_id)

        if li.status in ('confirmed', 'cancelled', 'refunded'):
            return {'status': li.status}

        attempt = self.request.retries + 1
        logger.info(f'Retry {attempt}/5 for line_item {line_item_id} [{li.source_type}]')

        # Attempt re-booking based on source
        success = _attempt_external_rebook(li)

        if success:
            li.status       = 'confirmed'
            li.confirmed_at = timezone.now()
            li.save(update_fields=['status', 'confirmed_at', 'updated_at'])
            logger.info(f'External rebook succeeded: {line_item_id}')
            return {'status': 'confirmed'}
        else:
            raise Exception('Rebook attempt failed')

    except Exception as e:
        if self.request.retries >= self.max_retries - 1:
            logger.error(f'All retries exhausted for {line_item_id} — cancelling')
            _cancel_and_refund(line_item_id, 'external_api_failure')
            return {'status': 'cancelled_after_retries'}
        raise self.retry(
            exc=e,
            countdown=300 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def handle_force_majeure(self, region_id: str, affected_dates: list,
                          reason: str = ''):
    """
    Bulk cancellation for force majeure events (weather, political, disaster).
    Cancels all pending/confirmed bookings in a region for given dates.
    Full refund on all affected line items.
    """
    try:
        from engine_b2c.models import Booking, BookingLineItem
        from engine_meta.tasks import invalidate_engine_config

        affected = Booking.objects.filter(
            region_id=region_id,
            trip_start_date__in=affected_dates,
            status__in=('pending_confirmation', 'confirmed'),
        )

        cancelled_count = 0
        for booking in affected:
            for li in booking.line_items.filter(
                    status__in=('pending', 'pending_confirmation', 'confirmed')):
                li.status           = 'cancelled'
                li.rejection_reason = f'Force majeure: {reason}'
                li.rejected_at      = timezone.now()
                li.save()
                from engine_b2c.tasks.booking_confirmation import initiate_line_item_refund
                initiate_line_item_refund.delay(str(li.id), reason='force_majeure')
                cancelled_count += 1
            booking.status = 'cancelled'
            booking.save(update_fields=['status', 'updated_at'])

        # Set regional disruption flag
        from blueberry_backend.communications import set_disruption
        set_disruption(str(region_id), {
            'severity': 'critical',
            'message':  reason,
            'set_at':   timezone.now().isoformat(),
        }, disruption_type='force_majeure')

        logger.warning(
            f'Force majeure: region={region_id} dates={affected_dates} '
            f'cancelled={cancelled_count} items')
        return {'cancelled_line_items': cancelled_count}

    except Exception as e:
        logger.error(f'handle_force_majeure failed: {e}')
        raise self.retry(exc=e)


def _attempt_external_rebook(line_item) -> bool:
    """Placeholder — full implementation per source_type in Phase 5 completion."""
    return False


def _cancel_and_refund(line_item_id: str, reason: str):
    try:
        from engine_b2c.models import BookingLineItem
        from engine_b2c.tasks.booking_confirmation import initiate_line_item_refund
        li = BookingLineItem.objects.get(id=line_item_id)
        li.status           = 'cancelled'
        li.rejection_reason = reason
        li.rejected_at      = timezone.now()
        li.save()
        initiate_line_item_refund.delay(line_item_id, reason=reason)
    except Exception as e:
        logger.error(f'_cancel_and_refund failed: {e}')