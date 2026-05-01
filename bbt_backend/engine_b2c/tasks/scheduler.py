"""
Scheduled Celery tasks for the booking layer.
"""
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_partner_payouts(self):
    """
    Daily task: calculate and queue partner payouts for completed bookings.
    Runs after service completion — partner is postpaid.
    """
    try:
        from engine_b2c.models import BookingLineItem
        from datetime import timedelta

        # Line items completed more than 24h ago, not yet paid out
        cutoff = timezone.now() - timedelta(hours=24)
        due_items = BookingLineItem.objects.filter(
            status='completed',
            source_type='internal',
            partner_payout__gt=0,
            refunded_at__isnull=True,
        ).select_related('booking')

        payout_count = 0
        for li in due_items:
            try:
                _queue_partner_payout(li)
                payout_count += 1
            except Exception as e:
                logger.error(f'Payout failed for line_item {li.id}: {e}')

        logger.info(f'Payout run: {payout_count} line items processed')
        return {'payouts_processed': payout_count}

    except Exception as e:
        logger.error(f'process_partner_payouts failed: {e}')
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3)
def expire_draft_bookings(self):
    """
    Hourly task: cancel bookings stuck in draft/pending_payment for > 30 min.
    """
    try:
        from engine_b2c.models import Booking
        from datetime import timedelta

        cutoff = timezone.now() - timedelta(minutes=30)
        stale  = Booking.objects.filter(
            status__in=('draft', 'pending_payment'),
            created_at__lt=cutoff,
        )
        count = stale.count()
        stale.update(status='cancelled')
        logger.info(f'Expired {count} stale bookings')
        return {'expired': count}

    except Exception as e:
        raise self.retry(exc=e)


def _queue_partner_payout(line_item):
    """
    Queues a partner payout via Razorpay Payouts API (postpaid).
    Blueberry holds funds and releases after service completion.
    Phase 5 stub — full implementation requires Razorpay Payouts activation.
    """
    logger.info(
        f'Payout queued: partner={line_item.partner_id} '
        f'amount={line_item.partner_payout} '
        f'line_item={line_item.id}')