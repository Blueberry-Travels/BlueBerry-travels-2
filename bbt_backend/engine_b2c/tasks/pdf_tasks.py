import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_and_email_itinerary(self, booking_id, mode='confirmed'):
    try:
        from engine_b2c.models import Booking
        from engine_b2c.pdf_generator import generate_itinerary_pdf
        from django.core.mail import EmailMessage
        from django.conf import settings
        booking  = Booking.objects.select_related('region').get(id=booking_id)
        pdf      = generate_itinerary_pdf(booking_id, mode)
        label    = 'Confirmed' if mode == 'confirmed' else 'Draft'
        filename = f'Blueberry_{label}_Itinerary_BBT-{str(booking_id)[:6].upper()}.pdf'
        email    = EmailMessage(
            subject    = f'Blueberry — {label} Itinerary: {booking.region.name}',
            body       = (
                f'Dear {booking.user_name},\n\n'
                f'{"Your trip is confirmed! Itinerary attached." if mode == "confirmed" else "Your draft itinerary is attached."}\n\n'
                f'Booking ref: BBT-{str(booking_id)[:6].upper()}\n'
                f'Destination: {booking.region.name}\n'
                f'Dates: {booking.trip_start_date} to {booking.trip_end_date}\n\n'
                f'Team Blueberry\ntech@blueberrytravels.co'
            ),
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@blueberrytravels.co'),
            to         = [booking.user_email],
        )
        email.attach(filename, pdf, 'application/pdf')
        email.send()
        logger.info(f'Itinerary emailed to {booking.user_email}')
        return {'status': 'sent'}
    except Exception as e:
        logger.error(f'generate_and_email_itinerary failed: {e}')
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_and_email_vouchers(self, booking_id):
    try:
        from engine_b2c.models import Booking, BookingLineItem
        from engine_b2c.pdf_generator import generate_partner_voucher_pdf
        from engine_b2b.models import PartnerProfile
        from django.core.mail import EmailMessage
        from django.conf import settings
        booking = Booking.objects.select_related('region').get(id=booking_id)
        items   = booking.line_items.filter(source_type='internal', status='confirmed')
        sent    = 0
        for li in items:
            if not li.partner_id:
                continue
            try:
                partner = PartnerProfile.objects.select_related('user').get(id=li.partner_id)
                if not partner.user.email:
                    continue
                pdf      = generate_partner_voucher_pdf(str(li.id))
                ref      = f'BBT-{str(booking_id)[:6].upper()}'
                filename = f'Blueberry_Voucher_{li.activity_name[:20].replace(" ","_")}_{ref}.pdf'
                email    = EmailMessage(
                    subject    = f'Blueberry — Service Voucher: {li.activity_name} ({ref})',
                    body       = (
                        f'Dear {partner.business_name},\n\n'
                        f'Confirmed booking. Voucher attached.\n\n'
                        f'Activity: {li.activity_name}\n'
                        f'Date: {li.scheduled_date}\n'
                        f'Customer: {booking.user_name}\n'
                        f'Ops: +91 80000 00000\n\nTeam Blueberry'
                    ),
                    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@blueberrytravels.co'),
                    to         = [partner.user.email],
                )
                email.attach(filename, pdf, 'application/pdf')
                email.send()
                sent += 1
            except Exception as e:
                logger.error(f'Voucher email failed for {li.id}: {e}')
        return {'status': 'done', 'vouchers_sent': sent}
    except Exception as e:
        logger.error(f'generate_and_email_vouchers failed: {e}')
        raise self.retry(exc=e)
