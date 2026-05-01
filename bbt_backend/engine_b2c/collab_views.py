"""
Collab group REST endpoints.
Real-time chat happens over WebSocket — see consumers.py.
"""
import logging
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

logger = logging.getLogger(__name__)


def _user_info(user):
    return {
        'user_id':    str(user.id),
        'username':   user.username,
        'name':       getattr(user, 'name', user.username),
    }


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_group(request):
    """
    POST /api/v1/collab/
    Creates a collab group and adds creator as leader.

    Body:
    {
        "name":           "Rishikesh Gang",
        "region_id":      "uuid",
        "trip_start_date":"2025-12-01",
        "trip_end_date":  "2025-12-03",
        "travel_style":   0.25,
        "season":         "winter",
        "invite_usernames":["alice","bob"]
    }
    """
    from engine_b2c.collab_models import CollabGroup, CollabMember
    from engine_meta.models import User

    data = request.data
    u    = _user_info(request.user)

    group = CollabGroup.objects.create(
        name            = data.get('name', f"{u['name']}'s Group"),
        created_by      = u['user_id'],
        created_by_name = u['name'],
        region_id       = data.get('region_id', ''),
        trip_start_date = data.get('trip_start_date'),
        trip_end_date   = data.get('trip_end_date'),
        travel_style    = float(data.get('travel_style', 0.5)),
        season          = data.get('season', 'summer'),
    )

    # Add creator as leader
    CollabMember.objects.create(
        group        = group,
        user_id      = u['user_id'],
        username     = u['username'],
        display_name = u['name'],
        role         = 'leader',
        status       = 'accepted',
        responded_at = timezone.now(),
    )

    # Send invites
    invited = []
    for username in data.get('invite_usernames', []):
        try:
            invitee = User.objects.get(username=username)
            CollabMember.objects.get_or_create(
                group   = group,
                user_id = str(invitee.id),
                defaults={
                    'username':    invitee.username,
                    'display_name':getattr(invitee, 'name', invitee.username),
                    'role':        'member',
                    'status':      'invited',
                }
            )
            invited.append(username)
        except User.DoesNotExist:
            logger.debug(f'Invite skipped — user not found: {username}')

    return Response({
        'group_id':     str(group.id),
        'name':         group.name,
        'status':       group.status,
        'chat_ws_url':  f'/ws/collab/{group.id}/',
        'invited':      invited,
    }, status=201)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def respond_to_invite(request, group_id):
    """
    POST /api/v1/collab/<group_id>/respond/
    Body: {"accept": true}
    """
    from engine_b2c.collab_models import CollabMember
    u = _user_info(request.user)
    try:
        member = CollabMember.objects.get(
            group_id=group_id, user_id=u['user_id'], status='invited')
    except CollabMember.DoesNotExist:
        return Response({'error': 'Invite not found.'}, status=404)

    accept = bool(request.data.get('accept', True))
    member.status       = 'accepted' if accept else 'declined'
    member.responded_at = timezone.now()
    member.save()

    if accept:
        # Broadcast system message to group
        _broadcast_system(group_id, f'{u["name"]} joined the group.')

    return Response({
        'group_id': group_id,
        'status':   member.status,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def group_detail(request, group_id):
    """GET /api/v1/collab/<group_id>/"""
    from engine_b2c.collab_models import CollabGroup, CollabMember
    u = _user_info(request.user)
    try:
        group = CollabGroup.objects.get(id=group_id)
    except CollabGroup.DoesNotExist:
        return Response({'error': 'Group not found.'}, status=404)

    is_member = CollabMember.objects.filter(
        group_id=group_id, user_id=u['user_id'],
        status='accepted').exists()
    if not is_member:
        return Response({'error': 'Not a member.'}, status=403)

    members = group.members.filter(status='accepted').values(
        'user_id', 'username', 'display_name', 'role', 'booking_id')

    return Response({
        'group_id':         str(group.id),
        'name':             group.name,
        'status':           group.status,
        'region_id':        group.region_id,
        'trip_start_date':  str(group.trip_start_date),
        'trip_end_date':    str(group.trip_end_date),
        'travel_style':     group.travel_style,
        'season':           group.season,
        'member_count':     group.member_count,
        'members':          list(members),
        'chat_ws_url':      f'/ws/collab/{group.id}/',
        'created_at':       group.created_at.isoformat(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_groups(request):
    """GET /api/v1/collab/ — all groups the user is part of."""
    from engine_b2c.collab_models import CollabMember
    u = _user_info(request.user)
    memberships = CollabMember.objects.filter(
        user_id=u['user_id'],
        status__in=('invited', 'accepted'),
    ).select_related('group').order_by('-group__created_at')

    return Response({'groups': [{
        'group_id':     str(m.group.id),
        'name':         m.group.name,
        'status':       m.group.status,
        'my_role':      m.role,
        'my_status':    m.status,
        'member_count': m.group.member_count,
        'region_id':    m.group.region_id,
        'trip_start':   str(m.group.trip_start_date),
        'trip_end':     str(m.group.trip_end_date),
        'chat_ws_url':  f'/ws/collab/{m.group.id}/',
    } for m in memberships]})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def invite_member(request, group_id):
    """POST /api/v1/collab/<group_id>/invite/ — leader invites by username."""
    from engine_b2c.collab_models import CollabGroup, CollabMember
    from engine_meta.models import User
    u = _user_info(request.user)

    try:
        group = CollabGroup.objects.get(id=group_id)
    except CollabGroup.DoesNotExist:
        return Response({'error': 'Group not found.'}, status=404)

    # Only leader can invite
    try:
        CollabMember.objects.get(
            group=group, user_id=u['user_id'],
            role='leader', status='accepted')
    except CollabMember.DoesNotExist:
        return Response({'error': 'Only the group leader can invite.'}, status=403)

    if group.member_count >= group.max_members:
        return Response({'error': f'Group is full (max {group.max_members}).'}, status=400)

    username = request.data.get('username')
    if not username:
        return Response({'error': 'username required.'}, status=400)

    try:
        invitee = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({'error': f'User {username} not found.'}, status=404)

    member, created = CollabMember.objects.get_or_create(
        group=group, user_id=str(invitee.id),
        defaults={
            'username':    invitee.username,
            'display_name':getattr(invitee, 'name', invitee.username),
            'role':        'member',
            'status':      'invited',
        }
    )
    if not created:
        return Response({'error': f'{username} is already in the group.'}, status=400)

    return Response({
        'invited':  username,
        'group_id': str(group.id),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_history(request, group_id):
    """
    GET /api/v1/collab/<group_id>/messages/?before=<uuid>
    Returns up to 50 messages. Use before= for pagination.
    """
    from engine_b2c.collab_models import CollabGroup, CollabMember, CollabMessage
    u = _user_info(request.user)

    is_member = CollabMember.objects.filter(
        group_id=group_id, user_id=u['user_id'], status='accepted').exists()
    if not is_member:
        return Response({'error': 'Not a member.'}, status=403)

    qs = CollabMessage.objects.filter(group_id=group_id)
    before = request.query_params.get('before')
    if before:
        try:
            pivot = CollabMessage.objects.get(id=before)
            qs    = qs.filter(created_at__lt=pivot.created_at)
        except CollabMessage.DoesNotExist:
            pass

    msgs = list(qs.order_by('-created_at')[:50])
    return Response({'messages': [m.to_dict() for m in reversed(msgs)]})


def _broadcast_system(group_id: str, content: str):
    """Sends a system message to a collab channel group via Channels."""
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        room = f'collab_{str(group_id).replace("-", "_")}'
        layer = get_channel_layer()
        async_to_sync(layer.group_send)(room, {
            'type':        'chat_system',
            'content':     content,
            'sender_id':   'system',
            'sender_name': 'System',
        })
    except Exception as e:
        logger.debug(f'Broadcast system failed: {e}')

@api_view(['GET'])
@permission_classes([AllowAny])
def discover_groups(request):
    """
    GET /api/v1/collab/discover/
        ?region_id=<uuid>
        &date_from=YYYY-MM-DD
        &date_to=YYYY-MM-DD
        &style=0.25
    """
    from engine_b2c.collab_models import CollabGroup

    region_id = request.query_params.get('region_id')
    date_from = request.query_params.get('date_from')
    date_to   = request.query_params.get('date_to')
    style     = request.query_params.get('style')

    if not region_id:
        return Response({'error': 'region_id required.'}, status=400)

    qs = CollabGroup.objects.filter(
        region_id=region_id,
        is_public=True,
        status='forming',
    )

    if date_from:
        qs = qs.filter(trip_end_date__gte=date_from)
    if date_to:
        qs = qs.filter(trip_start_date__lte=date_to)
    if style:
        try:
            s  = float(style)
            qs = qs.filter(
                travel_style__gte=max(0.0, s - 0.25),
                travel_style__lte=min(1.0, s + 0.25),
            )
        except ValueError:
            pass

    results = []
    for group in qs.order_by('trip_start_date'):
        accepted = group.members.filter(status='accepted').count()
        spots    = max(0, group.open_spots - (accepted - 1))
        if spots <= 0:
            continue
        results.append({
            'group_id':        str(group.id),
            'name':            group.name,
            'created_by':      group.created_by_name,
            'region_id':       group.region_id,
            'trip_start_date': str(group.trip_start_date),
            'trip_end_date':   str(group.trip_end_date),
            'travel_style':    group.travel_style,
            'season':          group.season,
            'current_members': accepted,
            'open_spots':      spots,
            'public_note':     group.public_note,
        })

    return Response({'results': results, 'count': len(results), 'region_id': region_id})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_to_join(request, group_id):
    """
    POST /api/v1/collab/<group_id>/join/
    Body: {"pickup_region": "...", "pickup_city": "Chandigarh", "message": "..."}
    """
    from engine_b2c.collab_models import CollabGroup, CollabMember
    u = _user_info(request.user)

    try:
        group = CollabGroup.objects.get(id=group_id, is_public=True, status='forming')
    except CollabGroup.DoesNotExist:
        return Response({'error': 'Group not found or not open.'}, status=404)

    if group.created_by == u['user_id']:
        return Response({'error': 'You created this group.'}, status=400)

    accepted = group.members.filter(status='accepted').count()
    if (accepted - 1) >= group.open_spots:
        return Response({'error': 'No open spots remaining.'}, status=400)

    member, created = CollabMember.objects.get_or_create(
        group=group,
        user_id=u['user_id'],
        defaults={
            'username':     u['username'],
            'display_name': u['name'],
            'role':         'member',
            'status':       'invited',
            'pickup_region':request.data.get('pickup_region', ''),
            'pickup_city':  request.data.get('pickup_city', ''),
        }
    )

    if not created:
        return Response({'error': 'You have already requested to join.'}, status=400)

    join_msg = request.data.get('message', '')
    note     = f'{u["name"]} from {request.data.get("pickup_city", "?")} wants to join.'
    if join_msg:
        note += f' "{join_msg}"'
    _broadcast_system(str(group_id), note)

    return Response({
        'group_id': str(group.id),
        'status':   'requested',
        'message':  'Join request sent. Waiting for leader approval.',
    }, status=201)
