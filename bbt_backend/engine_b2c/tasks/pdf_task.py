"""
Celery tasks for PDF generation and delivery.
"""
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_and_email_itinerary(self, booking_id: str, mode: str = 'confirmed'):
    """
    Generates the itinerary PDF and emails it to the customer.
    Triggered automatically when booking moves to 'confirmed' status.
    """
    try:
        from engine_b2c.models import Booking
        from engine_b2c.pdf_generator import generate_itinerary_pdf
        from django.core.mail import EmailMessage
        from django.conf import settings

        booking = Booking.objects.select_related('region').get(id=booking_id)
        pdf     = generate_itinerary_pdf(booking_id, mode)

        label   = 'Confirmed' if mode == 'confirmed' else 'Draft'
        subject = f'Blueberry — {label} Itinerary: {booking.region.name}'
        body    = (
            f'Dear {booking.user_name},\n\n'
            f'{"Your Blueberry trip is fully confirmed! Find your itinerary attached." if mode == "confirmed" else "Your Blueberry draft itinerary is attached. This will update once all partners confirm."}\n\n'
            f'Booking ref: BBT-{str(booking.id)[:6].upper()}\n'
            f'Destination: {booking.region.name}\n'
            f'Dates: {booking.trip_start_date} → {booking.trip_end_date}\n\n'
            f'For any queries: tech@blueberrytravels.co | +91 80000 00000\n\n'
            f'Safe travels,\nTeam Blueberry'
        )

        email = EmailMessage(
            subject    = subject,
            body       = body,
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@blueberrytravels.co'),
            to         = [booking.user_email],
        )
        filename = f'Blueberry_{"Confirmed" if mode == "confirmed" else "Draft"}_Itinerary_{str(booking.id)[:6].upper()}.pdf'
        email.attach(filename, pdf, 'application/pdf')
        email.send()

        logger.info(f'Itinerary PDF emailed to {booking.user_email} (mode={mode})')
        return {'status': 'sent', 'email': booking.user_email}

    except Exception as e:
        logger.error(f'generate_and_email_itinerary failed: {e}')
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_and_email_vouchers(self, booking_id: str):
    """
    Generates partner voucher PDFs and emails each to the relevant partner.
    Triggered after booking is fully confirmed.
    """
    try:
        from engine_b2c.models import Booking, BookingLineItem
        from engine_b2c.pdf_generator import generate_partner_voucher_pdf
        from engine_b2b.models import PartnerProfile
        from django.core.mail import EmailMessage
        from django.conf import settings

        booking = Booking.objects.select_related('region').get(id=booking_id)
        items   = booking.line_items.filter(
            source_type='internal', status='confirmed')

        sent = 0
        for li in items:
            if not li.partner_id:
                continue
            try:
                partner = PartnerProfile.objects.select_related('user').get(
                    id=li.partner_id)
                partner_email = partner.user.email
                if not partner_email:
                    continue

                pdf = generate_partner_voucher_pdf(str(li.id))
                ref = f'BBT-{str(booking.id)[:6].upper()}'

                email = EmailMessage(
                    subject    = f'Blueberry — Service Voucher: {li.activity_name} ({ref})',
                    body       = (
                        f'Dear {partner.business_name},\n\n'
                        f'You have a confirmed service booking. Please find your voucher attached.\n\n'
                        f'Activity: {li.activity_name}\n'
                        f'Date: {li.scheduled_date}\n'
                        f'Customer: {booking.user_name}\n'
                        f'Guests: {li.quantity}\n\n'
                        f'For any issues on the day: +91 80000 00000\n\n'
                        f'Thank you,\nTeam Blueberry'
                    ),
                    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL',
                                         'noreply@blueberrytravels.co'),
                    to         = [partner_email],
                )
                filename = f'Blueberry_Voucher_{li.activity_name[:20].replace(" ","_")}_{ref}.pdf'
                email.attach(filename, pdf, 'application/pdf')
                email.send()
                sent += 1
                logger.info(f'Voucher sent to {partner_email} for {li.activity_name}')

            except Exception as e:
                logger.error(f'Voucher email failed for line_item {li.id}: {e}')

        return {'status': 'done', 'vouchers_sent': sent}

    except Exception as e:
        logger.error(f'generate_and_email_vouchers failed: {e}')
        raise self.retry(exc=e)