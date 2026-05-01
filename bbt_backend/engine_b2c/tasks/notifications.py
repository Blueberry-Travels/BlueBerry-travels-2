"""
Notification Celery tasks.
"""
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_fallback(self, notification_id: str, email: str):
    """
    Sends email if the notification is still unread after the fallback delay.
    Skips if user has already read it (WhatsApp worked).
    """
    try:
        from engine_b2c.models import Notification
        notif = Notification.objects.get(id=notification_id)

        if notif.is_read:
            logger.info(f'Notification {notification_id} already read — skip email')
            return {'status': 'skipped_already_read'}

        _send_email(email, notif.title, notif.body)
        notif.sent_email = True
        notif.save(update_fields=['sent_email'])
        logger.info(f'Email fallback sent to {email} for notification {notification_id}')
        return {'status': 'sent'}

    except Exception as e:
        logger.error(f'send_email_fallback failed: {e}')
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def process_whatsapp_reply(self, phone: str, reply_text: str):
    """
    Processes a YES/NO WhatsApp reply from a partner.
    Looks up the most recent pending line item for this partner's phone.
    Routes to confirm or reject Celery task.
    """
    try:
        from engine_meta.models import User
        from engine_b2c.models import BookingLineItem
        from engine_b2c.tasks.booking_confirmation import (
            partner_confirm_line_item, partner_reject_line_item
        )

        # Find partner by phone
        try:
            user = User.objects.get(mobile=phone)
        except User.DoesNotExist:
            # Try with +91 prefix variations
            cleaned = phone.lstrip('91').lstrip('0')
            try:
                user = User.objects.filter(
                    mobile__endswith=cleaned).first()
                if not user:
                    logger.warning(f'No user found for WhatsApp phone {phone}')
                    return {'status': 'user_not_found'}
            except Exception:
                return {'status': 'user_not_found'}

        partner = getattr(user, 'partner_profile', None)
        if not partner:
            logger.warning(f'User {user.id} has no partner profile')
            return {'status': 'not_a_partner'}

        # Find their most recent pending line item
        li = BookingLineItem.objects.filter(
            partner_id=str(partner.id),
            status='pending_confirmation',
        ).order_by('confirmation_deadline').first()

        if not li:
            logger.info(f'No pending line items for partner {partner.id}')
            return {'status': 'no_pending_items'}

        if reply_text in ('YES', 'Y', 'CONFIRM', 'CONFIRMED', 'HAN', 'HA'):
            partner_confirm_line_item.delay(str(li.id), str(partner.id))
            logger.info(f'WhatsApp YES from {phone} → confirming {li.id}')
            return {'status': 'confirmed', 'line_item': str(li.id)}

        elif reply_text in ('NO', 'N', 'REJECT', 'REJECTED', 'NAHI', 'NAH'):
            partner_reject_line_item.delay(str(li.id), str(partner.id), 'Partner declined via WhatsApp.')
            logger.info(f'WhatsApp NO from {phone} → rejecting {li.id}')
            return {'status': 'rejected', 'line_item': str(li.id)}

        else:
            logger.info(f'Unrecognised WhatsApp reply from {phone}: {reply_text}')
            return {'status': 'unrecognised_reply', 'text': reply_text}

    except Exception as e:
        logger.error(f'process_whatsapp_reply failed: {e}')
        raise self.retry(exc=e)


def _send_email(to: str, subject: str, body: str):
    """Sends email via Django email backend."""
    from django.core.mail import send_mail
    from django.conf import settings
    try:
        send_mail(
            subject      = f'Blueberry — {subject}',
            message      = body,
            from_email   = getattr(settings, 'DEFAULT_FROM_EMAIL',
                                   'noreply@blueberrytravels.co'),
            recipient_list=[to],
            fail_silently= False,
        )
    except Exception as e:
        logger.error(f'Email send failed to {to}: {e}')
        raise