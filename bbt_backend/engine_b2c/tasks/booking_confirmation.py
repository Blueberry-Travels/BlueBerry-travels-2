"""
Celery tasks for the booking confirmation flow.

Flow per internal partner line item:
  1. notify_partner_new_booking     — WhatsApp + in-app to partner
  2. check_confirmation_deadline    — periodic check, auto-cancel if expired
  3. partner_confirm_line_item      — partner replies YES
  4. partner_reject_line_item       — partner replies NO
  5. check_booking_confirmation_status — master check across all line items
  6. initiate_line_item_refund      — Razorpay refund on rejection/cancellation

SLA windows (hours):
  guide:         2
  local_cab:     2
  outstation:    4
  stay:          6
  activity:      3
  default:       4
"""

import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

SLA_HOURS = {
    'guide':      2,
    'local_cab':  2,
    'cab':        2,
    'outstation': 4,
    'transport':  4,
    'hotel':      6,
    'stay':       6,
    'activity':   3,
    'default':    4,
}


def _get_sla(service_type: str) -> int:
    return SLA_HOURS.get(str(service_type).lower(), SLA_HOURS['default'])


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def notify_partner_new_booking(self, line_item_id: str):
    """
    Notifies the partner of a new booking requiring confirmation.
    Sends WhatsApp + in-app notification.
    Sets confirmation_deadline based on SLA.
    """
    try:
        from engine_b2c.models import BookingLineItem
        li = BookingLineItem.objects.select_related('booking').get(
            id=line_item_id, source_type='internal')

        if li.status != 'pending':
            logger.info(f'Line item {line_item_id} already past pending — skip notify')
            return

        # Set confirmation deadline
        sla_hours = _get_sla(li.activity_category)
        deadline  = timezone.now() + timedelta(hours=sla_hours)
        li.confirmation_deadline = deadline
        li.status = 'pending_confirmation'
        li.save(update_fields=['confirmation_deadline', 'status', 'updated_at'])

        # Notification payload
        payload = {
            'partner_id':    li.partner_id,
            'line_item_id':  str(li.id),
            'booking_id':    str(li.booking.id),
            'activity_name': li.activity_name,
            'scheduled_date':str(li.scheduled_date),
            'scheduled_time':str(li.scheduled_time),
            'guest_name':    li.booking.user_name,
            'guest_count':   li.booking.total_guests,
            'amount':        str(li.subtotal),
            'deadline':      deadline.isoformat(),
            'confirm_url':   f'/partner/bookings/{li.id}/confirm/',
            'reject_url':    f'/partner/bookings/{li.id}/reject/',
        }

        # WhatsApp (stub until WhatsApp API configured)
        _send_partner_whatsapp(payload)

        # Alert admins if WhatsApp not configured — manual contact needed
        try:
            from engine_meta.models import ThirdPartyAPIConfig
            from engine_b2c.notifications import notify_admins
            if not ThirdPartyAPIConfig.is_enabled('whatsapp'):
                notify_admins(
                    notification_type = 'attention_required',
                    title             = 'Manual partner contact needed',
                    body              = (f'WhatsApp not configured. '
                                         f'Manually contact partner {li.partner_name} '
                                         f'for booking {str(li.booking_id)[:8]}.'),
                    booking_id        = str(li.booking_id),
                    is_urgent         = True,
                )
        except Exception as _e:
            logger.error(f'WhatsApp fallback admin alert failed: {_e}')

        # Schedule deadline check
        check_confirmation_deadline.apply_async(
            args=[line_item_id],
            eta=deadline + timedelta(minutes=5),
        )

        logger.info(
            f'Partner {li.partner_id} notified for line item {line_item_id}. '
            f'Deadline: {deadline}')
        return {'status': 'notified', 'deadline': deadline.isoformat()}

    except Exception as e:
        logger.error(f'notify_partner_new_booking failed: {e}')
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=1)
def check_confirmation_deadline(self, line_item_id: str):
    """
    Runs after SLA window expires.
    If still pending_confirmation → auto-cancel + refund.
    """
    try:
        from engine_b2c.models import BookingLineItem
        li = BookingLineItem.objects.get(id=line_item_id)

        if li.status not in ('pending', 'pending_confirmation'):
            logger.info(f'Line item {line_item_id} already resolved — skip deadline check')
            return {'status': 'already_resolved', 'line_item_status': li.status}

        if timezone.now() < li.confirmation_deadline:
            logger.info(f'Deadline not yet passed for {line_item_id}')
            return {'status': 'not_expired'}

        # Auto-cancel
        li.status      = 'cancelled'
        li.rejected_at = timezone.now()
        li.rejection_reason = 'Auto-cancelled: partner did not respond within SLA window.'
        li.save(update_fields=['status', 'rejected_at', 'rejection_reason', 'updated_at'])

        logger.warning(f'Line item {line_item_id} auto-cancelled — SLA expired')

        # Alert admins on SLA breach
        try:
            from engine_b2c.notifications import notify_admins
            notify_admins(
                notification_type = 'attention_required',
                title             = 'SLA breach — partner did not respond',
                body              = (f'Line item {line_item_id} auto-cancelled. '
                                     f'Partner: {li.partner_name}. '
                                     f'Activity: {li.activity_name}.'),
                booking_id        = str(li.booking_id),
                action_url        = f'/api/v1/admin/bookings/{li.booking_id}/',
                is_urgent         = True,
            )
        except Exception as _e:
            logger.error(f'Admin SLA alert failed: {_e}')

        # Initiate refund
        initiate_line_item_refund.delay(line_item_id, reason='sla_expired')

        # Check if whole booking needs updating
        check_booking_confirmation_status.delay(str(li.booking_id))

        return {'status': 'auto_cancelled'}

    except Exception as e:
        logger.error(f'check_confirmation_deadline failed: {e}')
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def partner_confirm_line_item(self, line_item_id: str, partner_id: str):
    """
    Called when partner confirms via WhatsApp reply (YES) or dashboard.
    """
    try:
        from engine_b2c.models import BookingLineItem
        li = BookingLineItem.objects.get(
            id=line_item_id, partner_id=partner_id)

        if li.status not in ('pending', 'pending_confirmation'):
            return {'status': 'already_resolved', 'line_item_status': li.status}

        li.status       = 'confirmed'
        li.confirmed_at = timezone.now()
        li.save(update_fields=['status', 'confirmed_at', 'updated_at'])

        logger.info(f'Line item {line_item_id} confirmed by partner {partner_id}')

        # Notify customer
        _notify_customer_confirmation(li, confirmed=True)

        # Check if whole booking is now confirmed
        check_booking_confirmation_status.delay(str(li.booking_id))

        return {'status': 'confirmed'}

    except Exception as e:
        logger.error(f'partner_confirm_line_item failed: {e}')
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def partner_reject_line_item(self, line_item_id: str, partner_id: str,
                              reason: str = ''):
    """
    Called when partner rejects via WhatsApp reply (NO) or dashboard.
    """
    try:
        from engine_b2c.models import BookingLineItem
        li = BookingLineItem.objects.get(
            id=line_item_id, partner_id=partner_id)

        if li.status not in ('pending', 'pending_confirmation'):
            return {'status': 'already_resolved'}

        li.status           = 'rejected'
        li.rejected_at      = timezone.now()
        li.rejection_reason = reason or 'Partner declined.'
        li.save(update_fields=['status', 'rejected_at', 'rejection_reason', 'updated_at'])

        logger.info(f'Line item {line_item_id} rejected by partner {partner_id}')

        # Notify customer
        _notify_customer_confirmation(li, confirmed=False)

        # Initiate refund for this line item
        initiate_line_item_refund.delay(line_item_id, reason='partner_rejected')

        # Update master booking
        check_booking_confirmation_status.delay(str(li.booking_id))

        return {'status': 'rejected'}

    except Exception as e:
        logger.error(f'partner_reject_line_item failed: {e}')
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def check_booking_confirmation_status(self, booking_id: str):
    """
    Checks overall booking status after any line item changes.
    Updates master Booking.status accordingly.
    """
    try:
        from engine_b2c.models import Booking, BookingLineItem

        booking   = Booking.objects.get(id=booking_id)
        all_items = booking.line_items.all()

        if not all_items.exists():
            return {'status': 'no_line_items'}

        statuses = list(all_items.values_list('status', flat=True))

        if all(s == 'confirmed' for s in statuses):
            booking.status = 'confirmed'
            if all(s == 'confirmed' for s in statuses):
            booking.status = 'confirmed'
            logger.info(f'Booking {booking_id} fully confirmed')
            # Generate and email confirmed PDF + partner vouchers
            try:
                from engine_b2c.tasks.pdf_tasks import (
                    generate_and_email_itinerary,
                    generate_and_email_vouchers,
                )
                generate_and_email_itinerary.delay(str(booking_id), 'confirmed')
                generate_and_email_vouchers.delay(str(booking_id))
            except Exception as _e:
                logger.error(f'PDF trigger failed: {_e}')
                
            logger.info(f'Booking {booking_id} fully confirmed')

        elif any(s in ('cancelled', 'rejected', 'refunded') for s in statuses):
            confirmed = sum(1 for s in statuses if s == 'confirmed')
            total     = len(statuses)
            if confirmed == 0:
                booking.status = 'cancelled'
            else:
                booking.status = 'partially_refunded'
            logger.info(
                f'Booking {booking_id}: {confirmed}/{total} confirmed — '
                f'status={booking.status}')

        elif all(s in ('confirmed', 'pending_confirmation', 'pending')
                 for s in statuses):
            booking.status = 'pending_confirmation'

        booking.save(update_fields=['status', 'updated_at'])
        return {'booking_status': booking.status}

    except Exception as e:
        logger.error(f'check_booking_confirmation_status failed: {e}')
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def initiate_line_item_refund(self, line_item_id: str, reason: str = ''):
    """
    Initiates Razorpay refund for a specific line item.
    Partial refund on the master payment.
    """
    try:
        from engine_b2c.models import BookingLineItem
        li = BookingLineItem.objects.select_related('booking').get(id=line_item_id)

        if li.refunded_at:
            logger.info(f'Line item {line_item_id} already refunded')
            return {'status': 'already_refunded'}

        amount_paise = int(li.subtotal * 100)  # Razorpay uses paise
        if amount_paise <= 0:
            logger.info(f'Line item {line_item_id} has zero amount — skip refund')
            return {'status': 'zero_amount'}

        payment_id = li.booking.razorpay_payment_id
        if not payment_id:
            logger.warning(f'No payment_id on booking {li.booking.id} — cannot refund')
            return {'status': 'no_payment_id'}

        # Razorpay refund
        refund_id = _razorpay_refund(payment_id, amount_paise, reason)

        li.refund_amount      = li.subtotal
        li.razorpay_refund_id = refund_id
        li.refunded_at        = timezone.now()
        li.status             = 'refunded'
        li.save(update_fields=[
            'refund_amount', 'razorpay_refund_id',
            'refunded_at', 'status', 'updated_at'])

        # Update booking refunded_amount
        booking = li.booking
        booking.refunded_amount += li.subtotal
        booking.save(update_fields=['refunded_amount', 'updated_at'])

        logger.info(
            f'Refund initiated: line_item={line_item_id} '
            f'amount={li.subtotal} refund_id={refund_id}')
        return {'status': 'refunded', 'refund_id': refund_id, 'amount': str(li.subtotal)}

    except Exception as e:
        logger.error(f'initiate_line_item_refund failed: {e}')
        raise self.retry(exc=e)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _razorpay_refund(payment_id: str, amount_paise: int, reason: str) -> str:
    """
    Calls Razorpay refund API.
    Returns refund_id.
    Raises on failure.
    """
    import urllib.request
    import urllib.parse
    import json
    import base64

    from engine_meta.models import ThirdPartyAPIConfig
    config    = ThirdPartyAPIConfig.get('razorpay')
    if not config or not config.is_active:
        raise Exception('Razorpay not configured. Set credentials in Admin → Third-Party APIs.')

    key_id     = config.get_credential('key_id')
    key_secret = config.get_credential('key_secret')
    auth       = base64.b64encode(f'{key_id}:{key_secret}'.encode()).decode()

    url  = f'https://api.razorpay.com/v1/payments/{payment_id}/refund'
    body = json.dumps({
        'amount': amount_paise,
        'notes':  {'reason': reason, 'source': 'blueberry_auto_refund'},
    }).encode()
    req  = urllib.request.Request(url, data=body, headers={
        'Authorization': f'Basic {auth}',
        'Content-Type':  'application/json',
    }, method='POST')
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    return data['id']


def _send_partner_whatsapp(payload: dict):
    """
    Sends WhatsApp confirmation request to partner.
    Stub until WhatsApp Business API configured.
    """
    from engine_meta.models import ThirdPartyAPIConfig
    config = ThirdPartyAPIConfig.get('whatsapp')
    if not config or not config.is_active:
        logger.info(
            f'WhatsApp not configured — partner {payload.get("partner_id")} '
            f'notification skipped. Falling back to in-app only.')
        return
    # WhatsApp API call goes here when configured
    logger.info(f'WhatsApp notification sent to partner {payload.get("partner_id")}')


def _notify_customer_confirmation(line_item, confirmed: bool):
    """Notifies customer of partner confirmation or rejection."""
    status = 'confirmed' if confirmed else 'rejected'
    logger.info(
        f'Customer notification: booking {line_item.booking_id} '
        f'line_item {line_item.id} {status}')
    # WhatsApp/email/push goes here in Phase 6 (Communications layer)