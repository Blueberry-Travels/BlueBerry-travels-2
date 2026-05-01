"""
AI Coordinator — placeholder implementation.

When is_coordinator_active=False in EngineConfig:
  Returns the offline message and logs the session for future analysis.

When is_coordinator_active=True (future):
  Will route to the trained intent classifier.

Data collection stops when storage usage >= 90% of quota.
"""

import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

MAINTENANCE_ESCALATION_MSG = (
    "I've notified our team and a coordinator will reach out to you shortly."
)


def _is_storage_ok() -> bool:
    """
    Returns True if coordinator message storage is below 90% of quota.
    Checks CoordinatorMessage row count against configured quota.
    Quota is in MB — approximated as 1KB per message row = quota_mb * 1000 rows.
    """
    try:
        from blueberry_backend.communications import get_engine_config
        from engine_b2c.models import CoordinatorMessage
        config    = get_engine_config()
        quota_mb  = config.get('coordinator_storage_quota_mb', 500)
        max_rows  = quota_mb * 1000
        current   = CoordinatorMessage.objects.count()
        ok        = current < (max_rows * 0.90)
        if not ok:
            logger.warning(
                f'Coordinator storage at 90%+ quota: {current}/{max_rows} rows.')
        return ok
    except Exception as e:
        logger.debug(f'Storage check failed: {e}')
        return True


def handle_message(
    user_id:    str,
    text:       str,
    booking_id: str = '',
    channel:    str = 'app',
    session_id: str = '',
) -> dict:
    """
    Main entry point for all coordinator messages.

    Returns:
    {
        'reply':       str,
        'escalated':   bool,
        'session_id':  str,
        'is_active':   bool,
    }
    """
    from blueberry_backend.communications import get_engine_config

    config      = get_engine_config()
    is_active   = config.get('is_coordinator_active', False)
    offline_msg = config.get(
        'coordinator_offline_msg',
        'Our AI assistant is currently under maintenance. '
        'A coordinator will reach out to you shortly if needed.'
    )

    # Get or create session
    session = _get_or_create_session(user_id, booking_id, channel, session_id)

    # Log user message if storage permits
    storage_ok = _is_storage_ok()
    if storage_ok:
        _log_message(session, 'user', text)

    # ── Coordinator is offline ────────────────────────────────────────────────
    if not is_active:
        reply = offline_msg
        if storage_ok:
            _log_message(session, 'bot', reply)
        _escalate(session, user_id, booking_id, text, reason='maintenance')
        return {
            'reply':      reply,
            'escalated':  True,
            'session_id': str(session.id),
            'is_active':  False,
        }

    # ── Coordinator is active (future classifier goes here) ──────────────────
    # For now, still returns maintenance message but marked as active=True
    # so frontend knows the system is live when classifier is trained.
    reply = offline_msg
    if storage_ok:
        _log_message(session, 'bot', reply)

    return {
        'reply':      reply,
        'escalated':  False,
        'session_id': str(session.id),
        'is_active':  True,
    }


def get_status() -> dict:
    """Returns coordinator status for frontend display."""
    from blueberry_backend.communications import get_engine_config
    config = get_engine_config()
    return {
        'is_active':    config.get('is_coordinator_active', False),
        'offline_msg':  config.get('coordinator_offline_msg', ''),
        'channel':      'app_and_whatsapp',
    }


def get_analytics() -> dict:
    """
    Returns basic analytics for admin dashboard.
    Used to monitor data collection progress for future training.
    """
    try:
        from engine_b2c.models import CoordinatorSession, CoordinatorMessage
        from blueberry_backend.communications import get_engine_config
        from django.db.models import Count
        from datetime import timedelta

        config   = get_engine_config()
        quota_mb = config.get('coordinator_storage_quota_mb', 500)
        max_rows = quota_mb * 1000

        total_sessions  = CoordinatorSession.objects.count()
        total_messages  = CoordinatorMessage.objects.count()
        escalated       = CoordinatorSession.objects.filter(
                            was_escalated=True).count()
        by_channel      = dict(
                            CoordinatorSession.objects.values('channel')
                            .annotate(n=Count('id'))
                            .values_list('channel', 'n')
                          )
        storage_pct     = round((total_messages / max_rows) * 100, 1) if max_rows else 0
        collecting      = storage_pct < 90.0

        return {
            'total_sessions':     total_sessions,
            'total_messages':     total_messages,
            'escalated_sessions': escalated,
            'by_channel':         by_channel,
            'storage_used_pct':   storage_pct,
            'storage_quota_mb':   quota_mb,
            'collecting_data':    collecting,
            'max_rows':           max_rows,
        }
    except Exception as e:
        logger.error(f'Coordinator analytics failed: {e}')
        return {}


# ── Internal helpers ──────────────────────────────────────────────────────────

def _get_or_create_session(user_id, booking_id, channel, session_id):
    from engine_b2c.models import CoordinatorSession
    if session_id:
        try:
            return CoordinatorSession.objects.get(id=session_id, user_id=user_id)
        except CoordinatorSession.DoesNotExist:
            pass
    return CoordinatorSession.objects.create(
        user_id=user_id, booking_id=booking_id, channel=channel)


def _log_message(session, sender, text):
    try:
        from engine_b2c.models import CoordinatorMessage
        CoordinatorMessage.objects.create(
            session=session, sender=sender, text=text[:2000])
    except Exception as e:
        logger.debug(f'Message log failed: {e}')


def _escalate(session, user_id, booking_id, original_text, reason='maintenance'):
    try:
        session.was_escalated    = True
        session.escalation_reason= reason
        session.ended_at         = timezone.now()
        session.save(update_fields=['was_escalated', 'escalation_reason', 'ended_at'])

        from engine_b2c.notifications import notify_coordinators
        notify_coordinators(
            notification_type = 'attention_required',
            title             = 'Coordinator chatbot escalation',
            body              = (
                f'User {user_id} needs assistance. '
                f'Reason: {reason}. '
                f'Last message: {original_text[:100]}'
            ),
            booking_id        = booking_id,
            is_urgent         = False,
        )
    except Exception as e:
        logger.error(f'Escalation failed: {e}')
