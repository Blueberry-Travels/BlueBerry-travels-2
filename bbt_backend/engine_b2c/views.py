import logging
from datetime import date, timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def build_itinerary(request):
    """
    POST /api/v1/itinerary/build/

    Body:
    {
        "region_id":       "uuid",
        "travel_style":    0.25,
        "trip_days":       3,
        "trip_dates":      ["2025-12-01", "2025-12-02", "2025-12-03"],
        "primary_ids":     ["uuid1", "uuid2"],
        "season":          "winter",
        "user_gear_class": 0,
        "user_has_permit": false
    }

    trip_dates is optional — if omitted, engine uses today + trip_days.
    season is optional — if omitted, inferred from first trip_date month.
    """
    data = request.data

    # ── Validate required fields ──────────────────────────────────────────
    region_id = data.get('region_id')
    if not region_id:
        return Response({'error': 'region_id is required.'}, status=400)

    try:
        travel_style = float(data.get('travel_style', 0.5))
        if not (0.0 <= travel_style <= 1.0):
            raise ValueError
    except (TypeError, ValueError):
        return Response({'error': 'travel_style must be 0.0–1.0.'}, status=400)

    try:
        trip_days = int(data.get('trip_days', 2))
        if not (1 <= trip_days <= 14):
            raise ValueError
    except (TypeError, ValueError):
        return Response({'error': 'trip_days must be 1–14.'}, status=400)

    # ── Parse trip dates ──────────────────────────────────────────────────
    raw_dates = data.get('trip_dates', [])
    trip_dates = []
    if raw_dates:
        try:
            for ds in raw_dates:
                y, m, d = map(int, str(ds).split('-'))
                trip_dates.append(date(y, m, d))
        except Exception:
            return Response(
                {'error': 'trip_dates must be ISO format strings: YYYY-MM-DD.'},
                status=400)
    else:
        today = date.today()
        trip_dates = [today + timedelta(days=i) for i in range(trip_days)]

    # ── Infer season if not provided ──────────────────────────────────────
    season = data.get('season')
    if not season:
        month = trip_dates[0].month if trip_dates else date.today().month
        if month in (11, 12, 1, 2):
            season = 'winter'
        elif month in (6, 7, 8, 9):
            season = 'monsoon'
        else:
            season = 'summer'

    # ── Calendar flags ────────────────────────────────────────────────────
    first_date = trip_dates[0] if trip_dates else date.today()
    is_weekend  = first_date.isoweekday() in (6, 7)
    # is_holiday: simple check — extend later with a holiday DB
    is_holiday  = bool(data.get('is_holiday', False))

    # ── Build request dict for pipeline ───────────────────────────────────
    pipeline_request = {
        'region_id':       region_id,
        'travel_style':    travel_style,
        'trip_days':       trip_days,
        'trip_dates':      trip_dates,
        'primary_ids':     data.get('primary_ids', []),
        'season':          season,
        'user_gear_class': int(data.get('user_gear_class', 0)),
        'user_has_permit': bool(data.get('user_has_permit', False)),
        'is_holiday':      is_holiday,
        'is_weekend':      is_weekend,
    }

    # ── Run pipeline ───────────────────────────────────────────────────────
    try:
        from engine_meta.graph.pipeline import build_itinerary as _build
        result = _build(pipeline_request)
    except Exception as e:
        logger.error(f'Pipeline error: {e}', exc_info=True)
        return Response(
            {'error': 'Itinerary generation failed.', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ── Serialise result ───────────────────────────────────────────────────
    nodes_out = []
    for node in result.nodes:
        act = node.activity
        nodes_out.append({
            'day':             node.day,
            'position':        node.position,
            'slot_time':       node.slot_time,
            'is_transit':      node.is_transit,
            'is_filler':       node.is_filler,
            'is_locked':       node.is_locked,
            'user_can_remove': node.user_can_remove,
            'predicted_reward':round(node.predicted_reward, 3),
            'activity': {
                'id':           str(getattr(act, 'id', '')),
                'name':         getattr(act, 'name', ''),
                'category':     getattr(act, 'category', ''),
                'tone':         getattr(act, 'tone', ''),
                'effort_score': getattr(act, 'effort_score', 0),
                'duration_hrs': getattr(act, 'duration_hrs', 0),
                'node_type':    getattr(act, 'node_type', 'transit'),
                'noc_required': getattr(act, 'noc_required', False),
                'fitness_note': getattr(act, 'fitness_note', ''),
                # Transit-specific
                'travel_time_min':    getattr(act, 'travel_time_min', None),
                'transport_options':  getattr(act, 'transport_options', None),
            }
        })

    return Response({
        'region_id':        result.region_id,
        'travel_style':     result.travel_style,
        'season':           result.season,
        'trip_days':        result.days,
        'total_activities': result.total_activities,
        'filler_count':     result.filler_count,
        'transit_count':    result.transit_count,
        'noc_required':     result.noc_required,
        'warnings':         result.warnings,
        'nodes':            nodes_out,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def list_regions(request):
    """GET /api/v1/regions/ — public, used by frontend region picker."""
    from engine_b2c.models import Region
    regions = Region.objects.filter(is_active=True).order_by('zone', 'name')
    data = [{
        'id':          str(r.id),
        'name':        r.name,
        'state':       r.state,
        'zone':        r.zone,
        'description': r.description,
        'image_url':   r.image_url,
        'lat':         r.lat,
        'lng':         r.lng,
    } for r in regions]
    return Response({'regions': data})


@api_view(['GET'])
@permission_classes([AllowAny])
def list_activities(request):
    """
    GET /api/v1/activities/?region_id=<uuid>&style=<float>

    Returns approved activities for a region, sorted by relevance
    to the given style. Used by the frontend activity picker.
    """
    from engine_b2c.models import Activity
    from engine_meta.graph.style_scorer import style_fit

    region_id = request.query_params.get('region_id')
    if not region_id:
        return Response({'error': 'region_id required.'}, status=400)

    try:
        style = float(request.query_params.get('style', 0.5))
    except (TypeError, ValueError):
        style = 0.5

    activities = Activity.objects.filter(
        region_id=region_id,
        is_active=True,
        content_approved=True,
        is_filler=False,
        node_type='activity',
    ).select_related('region')

    data = []
    for a in activities:
        sf = style_fit(a.tone, style)
        # Surface score: style_fit × reward_score × significance
        surface_score = round(sf * a.reward_score * a.significance_score, 4)
        data.append({
            'id':               str(a.id),
            'name':             a.name,
            'short_desc':       a.short_desc,
            'category':         a.category,
            'tone':             a.tone,
            'effort_score':     a.effort_score,
            'duration_hrs':     a.duration_hrs,
            'price_from':       str(a.price_from),
            'risk_tier':        a.risk_tier,
            'noc_required':     a.noc_required or a.noc_auto_flag(),
            'fitness_note':     a.fitness_note,
            'significance_score': a.significance_score,
            'surface_score':    surface_score,
        })

    # Sort by surface score descending — most relevant first
    data.sort(key=lambda x: -x['surface_score'])
    return Response({'activities': data, 'count': len(data)})



@api_view(['GET'])
@permission_classes([AllowAny])
def get_stays(request):
    """
    GET /api/v1/stays/?region_id=<uuid>&checkin=YYYY-MM-DD&checkout=YYYY-MM-DD&adults=2&rooms=1

    Returns stays from platform first.
    Falls back to Booking.com if no platform hotels exist.
    Admin can disable Booking.com fallback via EngineConfig.bookingcom_enabled.
    """
    from engine_b2c.bookingcom import get_hotels_for_region

    region_id = request.query_params.get('region_id')
    checkin   = request.query_params.get('checkin')
    checkout  = request.query_params.get('checkout')

    if not all([region_id, checkin, checkout]):
        return Response(
            {'error': 'region_id, checkin, checkout are required.'}, status=400)

    try:
        adults = int(request.query_params.get('adults', 2))
        rooms  = int(request.query_params.get('rooms', 1))
    except ValueError:
        adults, rooms = 2, 1

    result = get_hotels_for_region(
        region_id=region_id,
        checkin=checkin,
        checkout=checkout,
        adults=adults,
        rooms=rooms,
    )
    return Response(result)


@api_view(['GET'])
@permission_classes([AllowAny])
def search_buses(request):
    """
    GET /api/v1/transport/buses/
        ?origin_id=...&dest_id=...&date=DD-MMM-YYYY
    """
    from engine_b2c.abhibus import get_bus_client
    from engine_b2c.redbus import RedBusDisabledError

    origin_id   = request.query_params.get('origin_id')
    dest_id     = request.query_params.get('dest_id')
    travel_date = request.query_params.get('date')

    if not all([origin_id, dest_id, travel_date]):
        return Response(
            {'error': 'origin_id, dest_id, date required.'}, status=400)

    try:
        client = get_bus_client()
        buses  = client.search_buses(origin_id, dest_id, travel_date)
        return Response({'buses': buses, 'count': len(buses)})
    except RedBusDisabledError as e:
        return Response({'available': False, 'message': str(e)}, status=503)
    except Exception as e:
        logger.error(f'Bus search failed: {e}')
        return Response({'error': 'Bus search failed.', 'detail': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def search_trains(request):
    """
    GET /api/v1/transport/trains/
        ?src=NDLS&dst=LKO&date=20251215&class=SL&quota=GN

    Returns coming_soon response if IRCTC not configured.
    """
    from engine_b2c.irctc import (
        IRCTCClient, IRCTCNotAvailableError,
        IRCTCComingSoonError, IRCTCConfigError,
        IRCTCAPIError, get_coming_soon_response,
    )

    src   = request.query_params.get('src')
    dst   = request.query_params.get('dst')
    date  = request.query_params.get('date')
    quota = request.query_params.get('quota', 'GN')

    if not all([src, dst, date]):
        return Response({'error': 'src, dst, date required.'}, status=400)

    try:
        client = IRCTCClient()
        trains = client.search_trains(src, dst, date, quota)
        return Response({'trains': trains, 'count': len(trains)})
    except (IRCTCNotAvailableError, IRCTCComingSoonError):
        return Response(get_coming_soon_response(), status=200)
    except IRCTCConfigError as e:
        return Response({'available': False, 'message': str(e)}, status=503)
    except IRCTCAPIError as e:
        logger.error(f'IRCTC search failed: {e}')
        return Response({'error': 'Train search failed.', 'detail': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_status(request):
    """
    GET /api/v1/admin/api-status/
    Returns live status of all third-party APIs.
    Used by admin dashboard.
    """
    from engine_meta.models import ThirdPartyAPIConfig
    configs = ThirdPartyAPIConfig.objects.all().order_by('api_key')
    data = [{
        'api_key':         c.api_key,
        'display_name':    c.display_name,
        'is_active':       c.is_active,
        'is_coming_soon':  c.is_coming_soon,
        'coming_soon_note':c.coming_soon_note,
        'status':          c.status,
        'last_checked_at': c.last_checked_at,
        'last_error':      c.last_error,
        'docs_url':        c.docs_url,
        'has_credentials': bool(c.credentials and any(
            v for v in c.credentials.values() if v)),
    } for c in configs]
    return Response({'apis': data})