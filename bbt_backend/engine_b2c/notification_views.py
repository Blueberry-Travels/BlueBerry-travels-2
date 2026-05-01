import json
import logging
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_list(request):
    from engine_b2c.models import Notification
    from collections import defaultdict
    user_id = str(request.user.id)
    notifs  = Notification.objects.filter(user_id=user_id).order_by('-created_at')[:100]
    groups  = defaultdict(list)
    for n in notifs:
        groups[n.booking_id].append(n.to_dict())
    total_unread = Notification.objects.filter(user_id=user_id, is_read=False).count()
    result = []
    for booking_id, notif_list in sorted(groups.items(), key=lambda x: (x[0] == '', x[0])):
        unread = sum(1 for n in notif_list if not n['is_read'])
        result.append({'booking_id': booking_id, 'unread_in_group': unread, 'notifications': notif_list})
    return Response({'unread_count': total_unread, 'groups': result})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unread_count(request):
    from engine_b2c.models import Notification
    count = Notification.objects.filter(user_id=str(request.user.id), is_read=False).count()
    return Response({'unread_count': count})


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def mark_read(request, notification_id):
    from engine_b2c.notifications import mark_read as _mark_read
    success = _mark_read(str(request.user.id), str(notification_id))
    if not success:
        return Response({'error': 'Notification not found.'}, status=404)
    return Response({'marked_read': True})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_read(request):
    from engine_b2c.notifications import mark_all_read as _mark_all_read
    booking_id = request.data.get('booking_id', '')
    _mark_all_read(str(request.user.id), booking_id)
    return Response({'marked_read': True})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fund_buffer(request, booking_id):
    from engine_b2c.models import Booking, TripBuffer
    try:
        booking = Booking.objects.get(id=booking_id, user_id=str(request.user.id))
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found.'}, status=404)
    amount = float(request.data.get('amount', 0))
    if amount <= 0:
        return Response({'error': 'Amount must be greater than 0.'}, status=400)
    buffer, _ = TripBuffer.objects.get_or_create(booking=booking)
    try:
        from engine_b2c.razorpay_client import RazorpayClient
        rz = RazorpayClient()
        order = rz.create_order(
            amount_paise=int(amount * 100),
            currency=booking.currency,
            receipt=f'buf_{str(booking_id)[:8]}',
            notes={'booking_id': str(booking_id), 'type': 'trip_buffer'},
        )
        buffer.razorpay_order_id = order['id']
        buffer.loaded_amount     = amount
        buffer.save(update_fields=['razorpay_order_id', 'loaded_amount', 'updated_at'])
        return Response({
            'buffer_id': str(buffer.id),
            'amount': amount,
            'razorpay_order_id': order['id'],
            'razorpay_key_id': _get_key_id(),
        })
    except Exception as e:
        logger.error(f'fund_buffer failed: {e}')
        return Response({'error': 'Payment initiation failed.'}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_buffer_payment(request, booking_id):
    from engine_b2c.models import Booking, TripBuffer
    from engine_b2c.razorpay_client import RazorpayClient
    try:
        booking = Booking.objects.get(id=booking_id, user_id=str(request.user.id))
        buffer  = booking.trip_buffer
    except Exception:
        return Response({'error': 'Not found.'}, status=404)
    order_id   = request.data.get('razorpay_order_id')
    payment_id = request.data.get('razorpay_payment_id')
    signature  = request.data.get('razorpay_signature')
    try:
        rz = RazorpayClient()
        if not rz.verify_payment_signature(order_id, payment_id, signature):
            return Response({'error': 'Invalid signature.'}, status=400)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
    buffer.razorpay_payment_id = payment_id
    buffer.status   = 'funded'
    buffer.funded_at= timezone.now()
    buffer.save(update_fields=['razorpay_payment_id', 'status', 'funded_at', 'updated_at'])
    return Response({'buffer_id': str(buffer.id), 'status': 'funded', 'available': str(buffer.available)})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_advance_request(request, booking_id):
    from engine_b2c.models import Booking, BookingLineItem, AdvancePaymentRequest
    from engine_b2c.notifications import notify
    if not any(r in (request.user.roles or []) for r in ['coordinator', 'admin', 'super_admin']):
        return Response({'error': 'Coordinator access required.'}, status=403)
    try:
        booking   = Booking.objects.get(id=booking_id)
        line_item = BookingLineItem.objects.get(
            id=request.data.get('line_item_id'), booking=booking, source_type='bookingcom')
    except Exception:
        return Response({'error': 'Booking or line item not found.'}, status=404)
    amount     = float(request.data.get('advance_amount', 0))
    no_coord   = bool(request.data.get('no_coordinator', False))
    hotel_name = request.data.get('hotel_name', '')
    reason     = request.data.get('reason', '')
    if amount <= 0:
        return Response({'error': 'advance_amount must be > 0.'}, status=400)
    adv = AdvancePaymentRequest.objects.create(
        booking          = booking,
        line_item        = line_item,
        source           = 'customer_self' if no_coord else 'coordinator',
        coordinator_id   = str(request.user.id) if not no_coord else '',
        coordinator_name = getattr(request.user, 'name', request.user.username) if not no_coord else '',
        hotel_name       = hotel_name,
        advance_amount   = amount,
        currency         = booking.currency,
        reason           = reason,
        no_coordinator   = no_coord,
        customer_message = (
            'Please contact the hotel directly to confirm your booking. '
            'If they require an advance, use the Pay Advance button below.'
            if no_coord else
            f'Your hotel "{hotel_name}" requires an advance payment of '
            f'Rs.{amount:.0f}. Please pay to confirm your booking.'
        ),
    )
    notify(
        user_id=booking.user_id, notification_type='advance_requested',
        title=f'Advance required — {hotel_name}', body=adv.customer_message,
        booking_id=str(booking_id),
        action_url=f'/bookings/{booking_id}/advance/{adv.id}/',
        metadata={'advance_id': str(adv.id), 'hotel_name': hotel_name,
                  'amount': str(amount), 'no_coordinator': no_coord},
    )
    return Response({
        'advance_id': str(adv.id), 'hotel_name': hotel_name,
        'advance_amount': str(amount), 'status': adv.status,
        'customer_message': adv.customer_message,
    }, status=201)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pay_advance(request, booking_id, advance_id):
    from engine_b2c.models import Booking, AdvancePaymentRequest, TripBuffer
    try:
        booking = Booking.objects.get(id=booking_id, user_id=str(request.user.id))
        adv     = AdvancePaymentRequest.objects.get(id=advance_id, booking=booking, status='pending')
    except Exception:
        return Response({'error': 'Not found or already paid.'}, status=404)
    try:
        buffer = booking.trip_buffer
        if buffer.available < adv.advance_amount:
            return Response({
                'error': f'Insufficient buffer. Available: Rs.{buffer.available}.',
                'available': str(buffer.available),
                'required':  str(adv.advance_amount),
                'fund_url':  f'/api/v1/buffer/{booking_id}/fund/',
            }, status=400)
    except TripBuffer.DoesNotExist:
        return Response({
            'error': 'Trip buffer not funded.',
            'fund_url': f'/api/v1/buffer/{booking_id}/fund/',
        }, status=400)
    try:
        buffer.deduct(adv.advance_amount)
    except ValueError as e:
        return Response({'error': str(e)}, status=400)
    try:
        from engine_b2c.razorpay_client import RazorpayClient
        rz    = RazorpayClient()
        order = rz.create_order(
            amount_paise=int(float(adv.advance_amount) * 100),
            currency=booking.currency,
            receipt=f'adv_{str(advance_id)[:8]}',
            notes={'type': 'advance_payment', 'advance_id': str(advance_id), 'hotel': adv.hotel_name},
        )
        adv.razorpay_order_id = order['id']
        adv.save(update_fields=['razorpay_order_id', 'updated_at'])
        return Response({
            'advance_id': str(adv.id), 'amount': str(adv.advance_amount),
            'razorpay_order_id': order['id'], 'razorpay_key_id': _get_key_id(),
            'buffer_remaining': str(buffer.available),
        })
    except Exception as e:
        buffer.used_amount -= adv.advance_amount
        buffer.status = 'funded' if buffer.used_amount == 0 else 'partially_used'
        buffer.save()
        return Response({'error': f'Payment initiation failed: {e}'}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_advance_payment(request, booking_id, advance_id):
    from engine_b2c.models import Booking, AdvancePaymentRequest
    from engine_b2c.razorpay_client import RazorpayClient
    from engine_b2c.notifications import notify
    try:
        booking = Booking.objects.get(id=booking_id, user_id=str(request.user.id))
        adv     = AdvancePaymentRequest.objects.get(id=advance_id, booking=booking)
    except Exception:
        return Response({'error': 'Not found.'}, status=404)
    order_id   = request.data.get('razorpay_order_id')
    payment_id = request.data.get('razorpay_payment_id')
    signature  = request.data.get('razorpay_signature')
    try:
        rz = RazorpayClient()
        if not rz.verify_payment_signature(order_id, payment_id, signature):
            return Response({'error': 'Invalid signature.'}, status=400)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
    adv.razorpay_payment_id = payment_id
    adv.status  = 'paid'
    adv.paid_at = timezone.now()
    adv.save(update_fields=['razorpay_payment_id', 'status', 'paid_at', 'updated_at'])
    notify(
        user_id=booking.user_id, notification_type='advance_paid',
        title=f'Advance paid — {adv.hotel_name}',
        body=f'Rs.{adv.advance_amount} advance paid. Coordinator will forward to hotel.',
        booking_id=str(booking_id), metadata={'advance_id': str(advance_id)},
    )
    return Response({'advance_id': str(adv.id), 'status': 'paid'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_advance_forwarded(request, booking_id, advance_id):
    if not any(r in (request.user.roles or []) for r in ['coordinator', 'admin', 'super_admin']):
        return Response({'error': 'Coordinator access required.'}, status=403)
    from engine_b2c.models import AdvancePaymentRequest
    from engine_b2c.notifications import notify
    try:
        adv = AdvancePaymentRequest.objects.get(id=advance_id, booking_id=booking_id, status='paid')
    except AdvancePaymentRequest.DoesNotExist:
        return Response({'error': 'Not found or not yet paid.'}, status=404)
    adv.status          = 'forwarded'
    adv.forwarded_at    = timezone.now()
    adv.forwarded_by    = getattr(request.user, 'name', request.user.username)
    adv.forwarding_note = request.data.get('note', '')
    adv.save()
    notify(
        user_id=adv.booking.user_id, notification_type='advance_paid',
        title=f'Advance forwarded — {adv.hotel_name}',
        body=f'Your advance of Rs.{adv.advance_amount} has been forwarded to {adv.hotel_name}.',
        booking_id=str(booking_id), metadata={'advance_id': str(advance_id)},
    )
    return Response({'advance_id': str(adv.id), 'status': 'forwarded'})


@csrf_exempt
@require_POST
def whatsapp_webhook(request):
    signature = request.META.get('HTTP_X_HUB_SIGNATURE_256', '')
    if not _verify_whatsapp_signature(request.body, signature):
        logger.warning('WhatsApp webhook signature verification failed')
        return HttpResponse(status=403)
    try:
        payload = json.loads(request.body)
        from engine_b2c.notifications import _parse_whatsapp_reply
        phone, text, wid = _parse_whatsapp_reply(payload)
        if phone and text:
            from engine_b2c.tasks.notifications import process_whatsapp_reply
            process_whatsapp_reply.delay(phone, text)
            logger.info(f'WhatsApp reply queued: {phone} -> {text}')
    except Exception as e:
        logger.error(f'WhatsApp webhook error: {e}')
    return HttpResponse(status=200)


@csrf_exempt
def whatsapp_webhook_verify(request):
    mode      = request.GET.get('hub.mode')
    token     = request.GET.get('hub.verify_token')
    challenge = request.GET.get('hub.challenge')
    try:
        from engine_meta.models import ThirdPartyAPIConfig
        config       = ThirdPartyAPIConfig.get('whatsapp')
        verify_token = config.get_credential('verify_token', 'blueberry_verify') if config else 'blueberry_verify'
    except Exception:
        verify_token = 'blueberry_verify'
    if mode == 'subscribe' and token == verify_token:
        return HttpResponse(challenge, content_type='text/plain')
    return HttpResponse(status=403)


def _verify_whatsapp_signature(body: bytes, signature: str) -> bool:
    try:
        import hmac
        import hashlib
        from engine_meta.models import ThirdPartyAPIConfig
        config     = ThirdPartyAPIConfig.get('whatsapp')
        app_secret = config.get_credential('app_secret', '') if config else ''
        if not app_secret:
            return True
        expected = 'sha256=' + hmac.new(app_secret.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception:
        return True


def _get_key_id() -> str:
    try:
        from engine_meta.models import ThirdPartyAPIConfig
        config = ThirdPartyAPIConfig.get('razorpay')
        return config.get_credential('key_id') if config else ''
    except Exception:
        return ''
