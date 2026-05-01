"""
Notification factory and delivery layer.

Single entry point: notify(user_id, type, title, body, **kwargs)

Delivery order:
  1. Persist to Notification table (always)
  2. Push via WebSocket if user connected (immediate)
  3. Send WhatsApp (if configured)
  4. Schedule email fallback (30min for alerts, 24hr for reminders)

All delivery failures are logged but never crash the caller.
"""

import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

# Notification types that get email fallback after 30 minutes
URGENT_TYPES = {
    'booking_rejected', 'booking_cancelled', 'partner_rejected',
    'refund_initiated', 'advance_requested', 'disruption_alert',
    'force_majeure', 'partner_new_booking',
}

# Types that only get 24h reminder email
REMINDER_TYPES = {
    'booking_confirmed', 'payment_success', 'collab_invite',
}

# WhatsApp template names per notification type
WHATSAPP_TEMPLATES = {
    'partner_new_booking':    'partner_booking_request',
    'booking_confirmed':      'customer_booking_confirmed',
    'booking_rejected':       'customer_booking_rejected',
    'booking_cancelled':      'customer_booking_cancelled',
    'advance_requested':      'customer_advance_required',
    'refund_initiated':       'customer_refund_initiated',
    'collab_invite':          'customer_collab_invite',
    'disruption_alert':       'customer_disruption_alert',
    'force_majeure':          'customer_force_majeure',
}


def notify(
    user_id:           str,
    notification_type: str,
    title:             str,
    body:              str,
    booking_id:        str = '',
    action_url:        str = '',
    metadata:          dict = None,
    phone:             str = '',
    email:             str = '',
) -> 'Notification':
    """
    Main entry point. Creates and delivers a notification.
    Returns the Notification instance.
    """
    from engine_b2c.models import Notification

    notif = Notification.objects.create(
        user_id           = str(user_id),
        notification_type = notification_type,
        title             = title,
        body              = body,
        booking_id        = str(booking_id) if booking_id else '',
        action_url        = action_url,
        metadata          = metadata or {},
    )

    # 1. Real-time WebSocket push
    _push_websocket(str(user_id), notif)

    # 2. WhatsApp
    if phone and notification_type in WHATSAPP_TEMPLATES:
        sent = _send_whatsapp(phone, notification_type, title, body, metadata or {})
        if sent:
            notif.sent_whatsapp = True
            notif.save(update_fields=['sent_whatsapp'])

    # 3. Email fallback (scheduled via Celery)
    if email:
        _schedule_email_fallback(notif, email, notification_type)

    return notif


def notify_partner(
    partner_id:        str,
    notification_type: str,
    title:             str,
    body:              str,
    booking_id:        str = '',
    metadata:          dict = None,
):
    """
    Notify a partner. Resolves their user_id, phone, email
    from PartnerProfile before calling notify().
    """
    try:
        from engine_b2b.models import PartnerProfile
        partner = PartnerProfile.objects.select_related('user').get(id=partner_id)
        user    = partner.user
        notify(
            user_id           = str(user.id),
            notification_type = notification_type,
            title             = title,
            body              = body,
            booking_id        = booking_id,
            metadata          = metadata or {},
            phone             = getattr(user, 'mobile', '') or '',
            email             = user.email,
        )
    except Exception as e:
        logger.error(f'notify_partner failed for {partner_id}: {e}')


def mark_read(user_id: str, notification_id: str) -> bool:
    from engine_b2c.models import Notification
    try:
        notif = Notification.objects.get(id=notification_id, user_id=str(user_id))
        if not notif.is_read:
            notif.is_read = True
            notif.read_at = timezone.now()
            notif.save(update_fields=['is_read', 'read_at'])
        return True
    except Notification.DoesNotExist:
        return False


def mark_all_read(user_id: str, booking_id: str = ''):
    from engine_b2c.models import Notification
    qs = Notification.objects.filter(user_id=str(user_id), is_read=False)
    if booking_id:
        qs = qs.filter(booking_id=str(booking_id))
    qs.update(is_read=True, read_at=timezone.now())


# ── WebSocket push ────────────────────────────────────────────────────────────

def _push_websocket(user_id: str, notif):
    """Sends notification to user's personal notification channel."""
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        layer     = get_channel_layer()
        room_name = f'notifications_{user_id.replace("-", "_")}'
        async_to_sync(layer.group_send)(room_name, {
            'type':         'notification_push',
            'notification': notif.to_dict(),
        })
    except Exception as e:
        logger.debug(f'WebSocket push failed for {user_id}: {e}')


# ── WhatsApp ──────────────────────────────────────────────────────────────────

def _send_whatsapp(phone: str, notif_type: str, title: str,
                   body: str, metadata: dict) -> bool:
    """
    Sends a WhatsApp message via Meta Cloud API.
    Returns True if sent, False if not configured or failed.
    """
    try:
        from engine_meta.models import ThirdPartyAPIConfig
        config = ThirdPartyAPIConfig.get('whatsapp')
        if not config or not config.is_active:
            logger.info(f'WhatsApp not configured — skipping for {phone}')
            return False

        import json
        import urllib.request

        phone_number_id = config.get_credential('phone_number_id')
        access_token    = config.get_credential('access_token')
        base_url        = config.get_credential(
            'base_url', 'https://graph.facebook.com/v18.0')

        template_name = WHATSAPP_TEMPLATES.get(notif_type)
        if not template_name:
            return False

        # Normalise phone — WhatsApp needs country code, no +
        phone_clean = phone.replace('+', '').replace(' ', '').replace('-', '')
        if phone_clean.startswith('0'):
            phone_clean = '91' + phone_clean[1:]
        elif not phone_clean.startswith('91') and len(phone_clean) == 10:
            phone_clean = '91' + phone_clean

        payload = {
            'messaging_product': 'whatsapp',
            'to':                phone_clean,
            'type':              'template',
            'template': {
                'name':     template_name,
                'language': {'code': 'en'},
                'components': [
                    {
                        'type':       'body',
                        'parameters': [
                            {'type': 'text', 'text': title},
                            {'type': 'text', 'text': body[:1000]},
                        ]
                    }
                ]
            }
        }

        url  = f'{base_url}/{phone_number_id}/messages'
        data = json.dumps(payload).encode()
        req  = urllib.request.Request(url, data=data, headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type':  'application/json',
        }, method='POST')

        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            logger.info(f'WhatsApp sent to {phone_clean}: {result.get("messages", [{}])[0].get("id")}')
            return True

    except Exception as e:
        logger.error(f'WhatsApp send failed for {phone}: {e}')
        return False


def _parse_whatsapp_reply(payload: dict) -> tuple:
    """
    Parses incoming WhatsApp webhook payload.
    Returns (phone, message_text, wa_message_id) or (None, None, None).
    """
    try:
        entry   = payload.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        value   = changes.get('value', {})
        msgs    = value.get('messages', [])
        if not msgs:
            return None, None, None
        msg  = msgs[0]
        phone= msg.get('from', '')
        text = msg.get('text', {}).get('body', '').strip().upper()
        wid  = msg.get('id', '')
        return phone, text, wid
    except Exception:
        return None, None, None


# ── Email fallback ────────────────────────────────────────────────────────────

def _schedule_email_fallback(notif, email: str, notif_type: str):
    """
    Schedules a Celery task to send email if WhatsApp unread.
    30 minutes for urgent types, 24 hours for reminders.
    """
    try:
        from datetime import timedelta
        from engine_b2c.tasks.notifications import send_email_fallback
        delay_minutes = 30 if notif_type in URGENT_TYPES else 1440
        send_email_fallback.apply_async(
            args=[str(notif.id), email],
            countdown=delay_minutes * 60,
        )
    except Exception as e:
        logger.debug(f'Email fallback scheduling failed: {e}')

def notify_admins(
    notification_type: str,
    title:             str,
    body:              str,
    booking_id:        str = '',
    action_url:        str = '',
    metadata:          dict = None,
    is_urgent:         bool = False,
    roles:             list = None,
):
    from engine_meta.models import User
    target_roles = roles or ['admin', 'super_admin', 'operator']
    try:
        all_users  = User.objects.filter(is_active=True)
        recipients = [
            u for u in all_users
            if any(r in (u.roles or []) for r in target_roles)
        ]
        for user in recipients:
            try:
                from engine_b2c.models import Notification
                notif = Notification.objects.create(
                    user_id           = str(user.id),
                    notification_type = notification_type,
                    title             = title,
                    body              = body,
                    booking_id        = str(booking_id),
                    action_url        = action_url,
                    metadata          = metadata or {},
                    is_urgent         = is_urgent,
                    recipient_role    = 'admin',
                )
                _push_websocket(str(user.id), notif)
                if is_urgent and (getattr(user, 'mobile', '') or ''):
                    _send_whatsapp(
                        user.mobile, notification_type,
                        title, body, metadata or {})
            except Exception as e:
                logger.error(f'notify_admins failed for user {user.id}: {e}')
        logger.info(f'Admin notification sent to {len(recipients)} recipients: {title}')
    except Exception as e:
        logger.error(f'notify_admins broadcast failed: {e}')


def notify_coordinators(
    notification_type: str,
    title:             str,
    body:              str,
    booking_id:        str = '',
    action_url:        str = '',
    metadata:          dict = None,
    is_urgent:         bool = False,
):
    notify_admins(
        notification_type = notification_type,
        title             = title,
        body              = body,
        booking_id        = booking_id,
        action_url        = action_url,
        metadata          = metadata or {},
        is_urgent         = is_urgent,
        roles             = ['coordinator'],
    )


def notify_partner_kyc_submitted(partner_id: str, partner_name: str):
    notify_admins(
        notification_type = 'partner_kyc_pending',
        title             = f'KYC submitted — {partner_name}',
        body              = 'A partner has submitted KYC documents for review.',
        action_url        = f'/api/v1/admin/partners/{partner_id}/',
        metadata          = {'partner_id': partner_id},
        is_urgent         = False,
    )


def notify_no_coordinator(booking_id: str, activity_name: str, scheduled_date: str):
    title = f'No coordinator — {activity_name}'
    body  = (f'Booking {str(booking_id)[:8]} for "{activity_name}" on '
             f'{scheduled_date} has no coordinator assigned. Please assign one.')
    notify_admins(
        notification_type = 'no_coordinator_alert',
        title             = title,
        body              = body,
        booking_id        = str(booking_id),
        action_url        = f'/api/v1/admin/bookings/{booking_id}/',
        metadata          = {'activity_name': activity_name, 'scheduled_date': scheduled_date},
        is_urgent         = True,
        roles             = ['admin', 'super_admin', 'operator', 'coordinator'],
    )


def notify_attention_required(
    booking_id:    str,
    user_name:     str,
    reason:        str,
    contact_phone: str = '',
):
    notify_admins(
        notification_type = 'attention_required',
        title             = f'Attention required — {user_name}',
        body              = reason,
        booking_id        = str(booking_id),
        action_url        = f'/api/v1/admin/bookings/{booking_id}/',
        metadata          = {'user_name': user_name, 'contact_phone': contact_phone},
        is_urgent         = True,
    )
