"""
Booking creation and payment flow.

Endpoints:
  POST /api/v1/bookings/                    create booking + Razorpay order
  POST /api/v1/bookings/<id>/verify/        verify payment + trigger confirmation
  GET  /api/v1/bookings/<id>/               booking detail
  GET  /api/v1/bookings/                    user's booking history
  PATCH /api/v1/bookings/<id>/fillers/      user confirms/removes filler nodes
  POST /api/v1/bookings/<id>/noc/           user accepts NOC for an activity
  POST /comm/webhook/razorpay/              Razorpay webhook (public)
"""

import json
import logging
from datetime import date
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


# ── Create Booking ────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_booking(request):
    """
    Creates a booking from a confirmed itinerary.

    Body:
    {
        "region_id":        "uuid",
        "trip_start_date":  "YYYY-MM-DD",
        "trip_end_date":    "YYYY-MM-DD",
        "travel_style":     0.25,
        "season":           "winter",
        "total_guests":     2,
        "currency":         "INR",
        "itinerary_snapshot": { ...pipeline output... },
        "line_items": [
            {
                "source_type":      "internal",
                "activity_id":      "uuid",
                "activity_name":    "Ganga Aarti",
                "activity_category":"cultural",
                "scheduled_date":   "2025-12-01",
                "scheduled_time":   "19:00:00",
                "partner_id":       "uuid",
                "partner_name":     "Ram Ghat Aarti Trust",
                "unit_price":       500,
                "quantity":         2,
                "commission_rate":  0.10,
                "requires_confirmation": true,
                "is_filler":        false,
                "noc_accepted":     false
            },
            {
                "source_type":      "bms_redirect",
                "activity_name":    "Yoga Festival Rishikesh",
                "activity_category":"cultural",
                "scheduled_date":   "2025-12-02",
                "unit_price":       0,
                "quantity":         1,
                "requires_confirmation": false
            }
        ]
    }
    """
    data = request.data

    # ── Validate required fields ──────────────────────────────────────────
    required = ['region_id', 'trip_start_date', 'trip_end_date', 'line_items']
    for field in required:
        if not data.get(field):
            return Response({'error': f'{field} is required.'}, status=400)

    if not data['line_items']:
        return Response({'error': 'At least one line item required.'}, status=400)

    # ── Parse dates ───────────────────────────────────────────────────────
    try:
        start = date.fromisoformat(data['trip_start_date'])
        end   = date.fromisoformat(data['trip_end_date'])
    except ValueError:
        return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

    # ── Calculate total ───────────────────────────────────────────────────
    total = sum(
        float(li.get('unit_price', 0)) * int(li.get('quantity', 1))
        for li in data['line_items']
        if not li.get('is_filler', False)  # fillers are free
    )

    currency = data.get('currency', 'INR')

    # ── Create Booking ────────────────────────────────────────────────────
    from engine_b2c.models import Booking, BookingLineItem, Region

    try:
        region = Region.objects.get(id=data['region_id'])
    except Region.DoesNotExist:
        return Response({'error': 'Region not found.'}, status=404)

    booking = Booking.objects.create(
        user_id             = str(request.user.id),
        user_email          = request.user.email,
        user_name           = getattr(request.user, 'name', request.user.username),
        user_phone          = getattr(request.user, 'mobile', '') or '',
        region              = region,
        travel_style        = float(data.get('travel_style', 0.5)),
        trip_start_date     = start,
        trip_end_date       = end,
        season              = data.get('season', 'summer'),
        total_guests        = int(data.get('total_guests', 1)),
        currency            = currency,
        total_amount        = total,
        status              = 'pending_payment',
        itinerary_snapshot  = data.get('itinerary_snapshot', {}),
        is_collab           = bool(data.get('is_collab', False)),
        collab_group_id     = data.get('collab_group_id', ''),
    )

    # ── Create Line Items ─────────────────────────────────────────────────
    for li_data in data['line_items']:
        BookingLineItem.objects.create(
            booking              = booking,
            source_type          = li_data.get('source_type', 'internal'),
            activity_id          = li_data.get('activity_id', ''),
            activity_name        = li_data.get('activity_name', ''),
            activity_category    = li_data.get('activity_category', ''),
            scheduled_date       = li_data.get('scheduled_date'),
            scheduled_time       = li_data.get('scheduled_time'),
            partner_id           = li_data.get('partner_id', ''),
            partner_name         = li_data.get('partner_name', ''),
            unit_price           = float(li_data.get('unit_price', 0)),
            quantity             = int(li_data.get('quantity', 1)),
            commission_rate      = float(li_data.get('commission_rate', 0.10)),
            requires_confirmation= bool(li_data.get('requires_confirmation', True)),
            is_filler            = bool(li_data.get('is_filler', False)),
            noc_accepted         = bool(li_data.get('noc_accepted', False)),
            noc_accepted_at      = timezone.now() if li_data.get('noc_accepted') else None,
        )

    # ── Create Razorpay Order ─────────────────────────────────────────────
    if total > 0:
        try:
            from engine_b2c.razorpay_client import RazorpayClient, RazorpayNotConfiguredError
            rz = RazorpayClient()
            amount_paise = int(total * 100)
            order = rz.create_order(
                amount_paise = amount_paise,
                currency     = currency,
                receipt      = f'bbt_{str(booking.id)[:8]}',
                notes        = {
                    'booking_id': str(booking.id),
                    'user_email': booking.user_email,
                    'region':     region.name,
                },
            )
            booking.razorpay_order_id = order['id']
            booking.save(update_fields=['razorpay_order_id', 'updated_at'])

        except RazorpayNotConfiguredError as e:
            # Razorpay not set up yet — return booking without order
            # Admin can configure and retry
            logger.warning(f'Razorpay not configured: {e}')
            return Response({
                'booking_id':    str(booking.id),
                'status':        booking.status,
                'total_amount':  str(total),
                'currency':      currency,
                'razorpay_order_id': None,
                'warning': 'Payment gateway not configured. Contact support.',
            }, status=201)

        except Exception as e:
            logger.error(f'Razorpay order creation failed: {e}')
            booking.delete()
            return Response(
                {'error': 'Payment initiation failed. Please try again.'},
                status=500)
    else:
        # Zero-amount booking (all fillers or free activities)
        booking.status = 'pending_confirmation'
        booking.save(update_fields=['status', 'updated_at'])

    return Response({
        'booking_id':        str(booking.id),
        'status':            booking.status,
        'total_amount':      str(total),
        'currency':          currency,
        'razorpay_order_id': booking.razorpay_order_id,
        'razorpay_key_id':   _get_razorpay_key_id(),
        'line_item_count':   booking.line_items.count(),
    }, status=201)


# ── Verify Payment ────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_payment(request, booking_id):
    """
    Called by frontend after Razorpay payment completes.

    Body:
    {
        "razorpay_order_id":   "order_xxx",
        "razorpay_payment_id": "pay_xxx",
        "razorpay_signature":  "sig_xxx"
    }
    """
    from engine_b2c.models import Booking

    try:
        booking = Booking.objects.get(id=booking_id, user_id=str(request.user.id))
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found.'}, status=404)

    if booking.status not in ('pending_payment', 'draft'):
        return Response({
            'error': f'Booking already in status: {booking.status}'
        }, status=400)

    order_id   = request.data.get('razorpay_order_id')
    payment_id = request.data.get('razorpay_payment_id')
    signature  = request.data.get('razorpay_signature')

    if not all([order_id, payment_id, signature]):
        return Response(
            {'error': 'razorpay_order_id, razorpay_payment_id, razorpay_signature required.'},
            status=400)

    # ── Verify signature ──────────────────────────────────────────────────
    try:
        from engine_b2c.razorpay_client import RazorpayClient
        rz = RazorpayClient()
        if not rz.verify_payment_signature(order_id, payment_id, signature):
            logger.warning(
                f'Invalid payment signature for booking {booking_id}')
            return Response({'error': 'Invalid payment signature.'}, status=400)
    except Exception as e:
        logger.error(f'Signature verification failed: {e}')
        return Response({'error': 'Payment verification failed.'}, status=500)

    # ── Mark as paid ──────────────────────────────────────────────────────
    payment = rz.fetch_payment(payment_id)
    booking.razorpay_payment_id = payment_id
    booking.razorpay_signature  = signature
    booking.paid_amount         = float(payment.get('amount', 0)) / 100
    booking.status              = 'pending_confirmation'
    booking.save(update_fields=[
        'razorpay_payment_id', 'razorpay_signature',
        'paid_amount', 'status', 'updated_at'])

    # ── Trigger confirmation flow for internal partners ───────────────────
    from engine_b2c.tasks.booking_confirmation import notify_partner_new_booking
    for li in booking.line_items.filter(
            source_type='internal',
            requires_confirmation=True):
        notify_partner_new_booking.delay(str(li.id))

    logger.info(f'Payment verified for booking {booking_id}')
    return Response({
        'booking_id': str(booking.id),
        'status':     booking.status,
        'paid':       str(booking.paid_amount),
        'message':    'Payment verified. Awaiting partner confirmation.',
    })


# ── Booking Detail and History ────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def booking_detail(request, booking_id):
    from engine_b2c.models import Booking
    try:
        booking = Booking.objects.prefetch_related('line_items').get(
            id=booking_id, user_id=str(request.user.id))
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found.'}, status=404)
    return Response(_serialise_booking(booking))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def booking_list(request):
    from engine_b2c.models import Booking
    bookings = Booking.objects.filter(
        user_id=str(request.user.id)
    ).order_by('-created_at')[:20]
    return Response({'bookings': [_serialise_booking(b) for b in bookings]})


# ── Filler confirmation ───────────────────────────────────────────────────────

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_fillers(request, booking_id):
    """
    User confirms or removes filler nodes before finalising.

    Body: {"fillers": [{"line_item_id": "uuid", "keep": true}, ...]}
    """
    from engine_b2c.models import Booking, BookingLineItem
    try:
        booking = Booking.objects.get(
            id=booking_id, user_id=str(request.user.id))
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found.'}, status=404)

    fillers = request.data.get('fillers', [])
    for f in fillers:
        try:
            li = booking.line_items.get(id=f['line_item_id'], is_filler=True)
            if f.get('keep', True):
                li.user_confirmed_filler = True
                li.save(update_fields=['user_confirmed_filler', 'updated_at'])
            else:
                li.delete()
        except BookingLineItem.DoesNotExist:
            pass

    # Recalculate total after filler removal
    total = sum(
        float(li.subtotal) for li in booking.line_items.filter(is_filler=False))
    booking.total_amount = total
    booking.save(update_fields=['total_amount', 'updated_at'])

    return Response({
        'booking_id':   str(booking.id),
        'total_amount': str(total),
        'message':      'Filler preferences saved.',
    })


# ── NOC Acceptance ────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_noc(request, booking_id, line_item_id):
    """
    User ticks all NOC checkboxes for a high-risk activity.
    Must be called before booking can be finalised.
    """
    from engine_b2c.models import Booking, BookingLineItem
    try:
        booking = Booking.objects.get(
            id=booking_id, user_id=str(request.user.id))
        li = booking.line_items.get(id=line_item_id)
    except (Booking.DoesNotExist, BookingLineItem.DoesNotExist):
        return Response({'error': 'Not found.'}, status=404)

    checkboxes = request.data.get('checkboxes', [])
    # Expect three checkboxes confirmed
    if len(checkboxes) < 3 or not all(checkboxes):
        return Response(
            {'error': 'All NOC checkboxes must be accepted.'}, status=400)

    li.noc_accepted    = True
    li.noc_accepted_at = timezone.now()
    li.save(update_fields=['noc_accepted', 'noc_accepted_at', 'updated_at'])

    return Response({
        'line_item_id': str(li.id),
        'noc_accepted': True,
        'accepted_at':  li.noc_accepted_at.isoformat(),
    })


# ── Razorpay Webhook ──────────────────────────────────────────────────────────

@csrf_exempt
@require_POST
def razorpay_webhook(request):
    """
    POST /comm/webhook/razorpay/
    Public endpoint — verified by signature before processing.
    """
    payload_body = request.body
    signature    = request.META.get('HTTP_X_RAZORPAY_SIGNATURE', '')

    try:
        from engine_b2c.razorpay_client import RazorpayClient
        rz = RazorpayClient()
        if not rz.verify_webhook_signature(payload_body, signature):
            logger.warning('Webhook signature verification failed')
            return HttpResponse(status=400)
    except Exception as e:
        logger.error(f'Webhook verification error: {e}')
        return HttpResponse(status=500)

    try:
        event = json.loads(payload_body)
        event_type = event.get('event')
        logger.info(f'Razorpay webhook: {event_type}')

        if event_type == 'payment.captured':
            _handle_payment_captured(event)
        elif event_type == 'payment.failed':
            _handle_payment_failed(event)
        elif event_type == 'refund.processed':
            _handle_refund_processed(event)

    except Exception as e:
        logger.error(f'Webhook processing error: {e}')
        return HttpResponse(status=500)

    return HttpResponse(status=200)


# ── Partner confirmation endpoints ────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def partner_confirm(request, line_item_id):
    """Partner confirms a booking line item via dashboard."""
    partner = getattr(request.user, 'partner_profile', None)
    if not partner:
        return Response({'error': 'Partner profile required.'}, status=403)
    from engine_b2c.tasks.booking_confirmation import partner_confirm_line_item
    partner_confirm_line_item.delay(line_item_id, str(partner.id))
    return Response({'message': 'Confirmation queued.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def partner_reject(request, line_item_id):
    """Partner rejects a booking line item via dashboard."""
    partner = getattr(request.user, 'partner_profile', None)
    if not partner:
        return Response({'error': 'Partner profile required.'}, status=403)
    reason = request.data.get('reason', '')
    from engine_b2c.tasks.booking_confirmation import partner_reject_line_item
    partner_reject_line_item.delay(line_item_id, str(partner.id), reason)
    return Response({'message': 'Rejection queued.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def partner_pending_bookings(request):
    """Returns all pending line items for the logged-in partner."""
    partner = getattr(request.user, 'partner_profile', None)
    if not partner:
        return Response({'error': 'Partner profile required.'}, status=403)
    from engine_b2c.models import BookingLineItem
    items = BookingLineItem.objects.filter(
        partner_id=str(partner.id),
        status__in=('pending', 'pending_confirmation'),
    ).select_related('booking').order_by('confirmation_deadline')
    return Response({'pending': [_serialise_line_item(li) for li in items]})


# ── BMS deep link ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def get_events(request):
    """
    GET /api/v1/events/?region_id=<uuid>&date=YYYY-MM-DD

    Returns:
      - Platform-registered events (Activity nodes with category=cultural/heritage)
      - BMS deep link if BMS API not configured
      - BMS API results if configured and active
    """
    from engine_b2c.models import Activity
    from engine_meta.models import ThirdPartyAPIConfig

    region_id  = request.query_params.get('region_id')
    event_date = request.query_params.get('date')

    if not region_id:
        return Response({'error': 'region_id required.'}, status=400)

    # Platform events
    qs = Activity.objects.filter(
        region_id=region_id,
        is_active=True,
        content_approved=True,
        node_type='activity',
    )
    if event_date:
        try:
            d = date.fromisoformat(event_date)
            qs = [a for a in qs if a.is_available_on(d)]
        except ValueError:
            pass

    platform_events = [{
        'source':      'platform',
        'id':          str(a.id),
        'name':        a.name,
        'category':    a.category,
        'description': a.short_desc,
        'duration_hrs':a.duration_hrs,
        'price_from':  str(a.price_from),
        'noc_required':a.noc_required or a.noc_auto_flag(),
    } for a in qs]

    # BMS
    bms_config = ThirdPartyAPIConfig.get('bms')
    bms_active = bms_config and bms_config.is_active and not bms_config.is_coming_soon

    if bms_active:
        # Full BMS API — Phase 5 completion
        bms_events   = []
        powered_by   = 'Powered by BookMyShow'
        coming_soon  = False
    else:
        # Deep link fallback
        bms_city     = _region_to_bms_city(region_id)
        deep_link    = f'https://in.bookmyshow.com/explore/events-{bms_city}'
        if event_date:
            deep_link += f'?date={event_date}'
        bms_events   = [{
            'source':    'bms_redirect',
            'deep_link': deep_link,
            'label':     'See more events on BookMyShow',
            'powered_by':'Powered by BookMyShow',
        }]
        powered_by   = 'Powered by BookMyShow'
        coming_soon  = bms_config.is_coming_soon if bms_config else True

    return Response({
        'platform_events': platform_events,
        'bms_events':      bms_events,
        'bms_powered_by':  powered_by,
        'bms_coming_soon': coming_soon,
    })


# ── Serialisers ───────────────────────────────────────────────────────────────

def _serialise_booking(booking) -> dict:
    return {
        'id':                str(booking.id),
        'status':            booking.status,
        'region_id':         str(booking.region_id),
        'trip_start_date':   str(booking.trip_start_date),
        'trip_end_date':     str(booking.trip_end_date),
        'travel_style':      booking.travel_style,
        'season':            booking.season,
        'total_guests':      booking.total_guests,
        'total_amount':      str(booking.total_amount),
        'paid_amount':       str(booking.paid_amount),
        'refunded_amount':   str(booking.refunded_amount),
        'currency':          booking.currency,
        'razorpay_order_id': booking.razorpay_order_id,
        'is_collab':         booking.is_collab,
        'collab_group_id':   booking.collab_group_id,
        'created_at':        booking.created_at.isoformat(),
        'line_items':        [_serialise_line_item(li)
                              for li in booking.line_items.all()],
    }


def _serialise_line_item(li) -> dict:
    return {
        'id':                    str(li.id),
        'source_type':           li.source_type,
        'activity_name':         li.activity_name,
        'activity_category':     li.activity_category,
        'scheduled_date':        str(li.scheduled_date) if li.scheduled_date else None,
        'scheduled_time':        str(li.scheduled_time) if li.scheduled_time else None,
        'partner_name':          li.partner_name,
        'status':                li.status,
        'subtotal':              str(li.subtotal),
        'requires_confirmation': li.requires_confirmation,
        'confirmation_deadline': li.confirmation_deadline.isoformat()
                                 if li.confirmation_deadline else None,
        'is_filler':             li.is_filler,
        'user_confirmed_filler': li.user_confirmed_filler,
        'noc_accepted':          li.noc_accepted,
        'rejection_reason':      li.rejection_reason,
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _get_razorpay_key_id() -> str:
    try:
        from engine_meta.models import ThirdPartyAPIConfig
        config = ThirdPartyAPIConfig.get('razorpay')
        return config.get_credential('key_id') if config else ''
    except Exception:
        return ''


def _handle_payment_captured(event: dict):
    payload    = event.get('payload', {})
    payment    = payload.get('payment', {}).get('entity', {})
    order_id   = payment.get('order_id')
    payment_id = payment.get('id')
    if not order_id:
        return
    from engine_b2c.models import Booking
    try:
        booking = Booking.objects.get(razorpay_order_id=order_id)
        if booking.status == 'pending_payment':
            booking.razorpay_payment_id = payment_id
            booking.paid_amount = float(payment.get('amount', 0)) / 100
            booking.status = 'pending_confirmation'
            booking.save()
            from engine_b2c.tasks.booking_confirmation import notify_partner_new_booking
            for li in booking.line_items.filter(
                    source_type='internal', requires_confirmation=True):
                notify_partner_new_booking.delay(str(li.id))
    except Booking.DoesNotExist:
        logger.warning(f'Webhook: no booking for order {order_id}')


def _handle_payment_failed(event: dict):
    payload  = event.get('payload', {})
    payment  = payload.get('payment', {}).get('entity', {})
    order_id = payment.get('order_id')
    if not order_id:
        return
    from engine_b2c.models import Booking
    try:
        booking = Booking.objects.get(razorpay_order_id=order_id)
        if booking.status == 'pending_payment':
            booking.status = 'cancelled'
            booking.save(update_fields=['status', 'updated_at'])
    except Booking.DoesNotExist:
        pass


def _handle_refund_processed(event: dict):
    payload   = event.get('payload', {})
    refund    = payload.get('refund', {}).get('entity', {})
    refund_id = refund.get('id')
    logger.info(f'Refund processed: {refund_id}')


def _region_to_bms_city(region_id: str) -> str:
    _MAP = {
        'GHW': 'rishikesh', 'KMN': 'nainital', 'HPS': 'manali',
        'HSD': 'shimla',    'LDK': 'leh',       'RAJ': 'jaipur',
        'PNJ': 'amritsar',  'HRY': 'chandigarh','ASM': 'guwahati',
        'MEG': 'shillong',  'ARP': 'itanagar',  'SKM': 'gangtok',
        'NEM': 'kohima',
    }
    try:
        from engine_b2c.models import Region
        region = Region.objects.get(id=region_id)
        return _MAP.get(region.region_code, 'india')
    except Exception:
        return 'india'

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_voucher(request, booking_id):
    """
    POST /api/v1/bookings/<booking_id>/voucher/apply/
    Body: {"code": "SUMMER25-X7K2"}

    Validates voucher and returns discounted total.
    Does NOT commit — discount applied when booking is created or
    when verify_payment is called. Stored in session/booking.
    """
    from engine_b2c.models import Booking, PromoVoucher

    try:
        booking = Booking.objects.get(
            id=booking_id, user_id=str(request.user.id))
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found.'}, status=404)

    code = str(request.data.get('code', '')).strip().upper()
    if not code:
        return Response({'error': 'Voucher code required.'}, status=400)

    try:
        voucher = PromoVoucher.objects.get(code=code)
    except PromoVoucher.DoesNotExist:
        return Response({'error': 'Invalid voucher code.'}, status=400)

    is_valid, error, discount = voucher.validate(
        float(booking.total_amount),
        str(booking.region_id),
    )

    if not is_valid:
        return Response({'error': error}, status=400)

    discounted_total = float(booking.total_amount) - discount

    # Store voucher on booking metadata for payment step
    booking.itinerary_snapshot = {
        **booking.itinerary_snapshot,
        '_voucher_code':     code,
        '_voucher_id':       str(voucher.id),
        '_discount_amount':  discount,
        '_discounted_total': discounted_total,
    }
    booking.save(update_fields=['itinerary_snapshot', 'updated_at'])

    return Response({
        'voucher_code':     code,
        'description':      voucher.description,
        'discount_type':    voucher.discount_type,
        'discount_value':   str(voucher.discount_value),
        'discount_amount':  discount,
        'original_total':   str(booking.total_amount),
        'discounted_total': discounted_total,
        'currency':         booking.currency,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_voucher(request, booking_id):
    """
    POST /api/v1/bookings/<booking_id>/voucher/remove/
    Removes applied voucher from booking.
    """
    from engine_b2c.models import Booking

    try:
        booking = Booking.objects.get(
            id=booking_id, user_id=str(request.user.id))
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found.'}, status=404)

    snap = booking.itinerary_snapshot or {}
    for key in ['_voucher_code', '_voucher_id',
                '_discount_amount', '_discounted_total']:
        snap.pop(key, None)

    booking.itinerary_snapshot = snap
    booking.save(update_fields=['itinerary_snapshot', 'updated_at'])

    return Response({
        'message':       'Voucher removed.',
        'total_amount':  str(booking.total_amount),
        'currency':      booking.currency,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_voucher(request):
    """
    POST /api/v1/vouchers/validate/
    Body: {"code": "SUMMER25-X7K2", "booking_total": 5000, "region_id": "uuid"}
    Lets frontend check a code before applying it.
    """
    from engine_b2c.models import PromoVoucher
    code  = str(request.data.get('code', '')).strip().upper()
    total = float(request.data.get('booking_total', 0))
    region= str(request.data.get('region_id', ''))

    if not code:
        return Response({'error': 'code required.'}, status=400)

    try:
        voucher = PromoVoucher.objects.get(code=code)
    except PromoVoucher.DoesNotExist:
        return Response({'valid': False, 'error': 'Invalid voucher code.'})

    is_valid, error, discount = voucher.validate(total, region)
    if not is_valid:
        return Response({'valid': False, 'error': error})

    return Response({
        'valid':            True,
        'code':             voucher.code,
        'description':      voucher.description,
        'discount_type':    voucher.discount_type,
        'discount_value':   str(voucher.discount_value),
        'discount_amount':  discount,
        'discounted_total': round(total - discount, 2),
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def coordinator_status(request):
    """GET /api/v1/coordinator/status/ — frontend checks if chatbot is live."""
    from engine_meta.coordinator.placeholder import get_status
    return Response(get_status())


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def coordinator_message(request):
    """
    POST /api/v1/coordinator/message/
    Body: {"text": "...", "booking_id": "...", "session_id": "...", "channel": "app"}
    """
    from engine_meta.coordinator.placeholder import handle_message
    text       = str(request.data.get('text', '')).strip()
    booking_id = str(request.data.get('booking_id', ''))
    session_id = str(request.data.get('session_id', ''))
    channel    = request.data.get('channel', 'app')
    if not text:
        return Response({'error': 'text required.'}, status=400)
    result = handle_message(
        user_id    = str(request.user.id),
        text       = text,
        booking_id = booking_id,
        channel    = channel,
        session_id = session_id,
    )
    return Response(result)
