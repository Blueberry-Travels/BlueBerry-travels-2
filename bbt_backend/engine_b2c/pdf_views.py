import logging
from django.http import HttpResponse, Http404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_itinerary(request, booking_id):
    from engine_b2c.models import Booking
    from engine_b2c.pdf_generator import generate_itinerary_pdf
    mode = request.query_params.get('mode', 'confirmed')
    if mode not in ('confirmed', 'draft'):
        mode = 'confirmed'
    try:
        is_admin = any(r in (request.user.roles or [])
                       for r in ['admin', 'super_admin', 'operator', 'coordinator'])
        booking  = Booking.objects.get(id=booking_id) if is_admin else \
                   Booking.objects.get(id=booking_id, user_id=str(request.user.id))
    except Booking.DoesNotExist:
        raise Http404
    try:
        pdf      = generate_itinerary_pdf(str(booking_id), mode)
        label    = 'Confirmed' if mode == 'confirmed' else 'Draft'
        filename = f'Blueberry_{label}_Itinerary_BBT-{str(booking_id)[:6].upper()}.pdf'
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        logger.error(f'PDF generation failed: {e}')
        return Response({'error': 'PDF generation failed.'}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_pdf_email(request, booking_id):
    if not any(r in (request.user.roles or [])
               for r in ['admin', 'super_admin', 'operator', 'coordinator']):
        return Response({'error': 'Admin access required.'}, status=403)
    mode = request.data.get('mode', 'confirmed')
    from engine_b2c.tasks.pdf_tasks import generate_and_email_itinerary
    generate_and_email_itinerary.delay(str(booking_id), mode)
    return Response({'message': f'PDF email queued (mode={mode}).'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_customer_tickets(request, booking_id):
    from engine_b2c.models import Booking
    from engine_b2c.pdf_generator import generate_customer_tickets_pdf
    try:
        booking = Booking.objects.get(
            id=booking_id, user_id=str(request.user.id))
    except Booking.DoesNotExist:
        raise Http404
    try:
        pdf      = generate_customer_tickets_pdf(str(booking_id))
        filename = f'Blueberry_Tickets_BBT-{str(booking_id)[:6].upper()}.pdf'
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        logger.error(f'Customer tickets PDF failed: {e}')
        return Response({'error': 'Ticket generation failed.'}, status=500)
