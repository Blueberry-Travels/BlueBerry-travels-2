"""
Photo upload endpoints.
Kept in a separate file to avoid import conflicts with views.py.

Endpoints:
  POST /api/v1/auth/profile/photo/      customer uploads their own photo
  POST /api/v1/partner/profile/photo/   partner uploads their business photo
"""
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)

ALLOWED_TYPES = ('image/jpeg', 'image/png', 'image/webp')
MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5MB


def _validate_photo(photo):
    """Returns (ok, error_message)."""
    if photo.content_type not in ALLOWED_TYPES:
        return False, 'Only JPEG, PNG, and WEBP are allowed.'
    if photo.size > MAX_SIZE_BYTES:
        return False, 'File too large. Maximum size is 5MB.'
    return True, ''


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_profile_photo(request):
    """
    POST /api/v1/auth/profile/photo/
    Multipart form — field name: photo
    Returns: {"profile_photo_url": "https://..."}
    """
    if 'photo' not in request.FILES:
        return Response({'error': 'photo field required.'}, status=400)

    photo = request.FILES['photo']
    ok, err = _validate_photo(photo)
    if not ok:
        return Response({'error': err}, status=400)

    user = request.user

    # Delete old photo from disk if it exists
    if user.profile_photo:
        try:
            user.profile_photo.delete(save=False)
        except Exception as e:
            logger.debug(f'Old profile photo delete failed: {e}')

    user.profile_photo = photo
    user.save(update_fields=['profile_photo'])

    photo_url = (request.build_absolute_uri(user.profile_photo.url)
                 if user.profile_photo else None)

    return Response({'profile_photo_url': photo_url})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_profile_photo(request):
    """DELETE /api/v1/auth/profile/photo/"""
    user = request.user
    if user.profile_photo:
        user.profile_photo.delete(save=True)
    return Response({'message': 'Profile photo removed.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_partner_photo(request):
    """
    POST /api/v1/partner/profile/photo/
    Multipart form — field name: photo
    Returns: {"business_photo_url": "https://..."}
    """
    if 'photo' not in request.FILES:
        return Response({'error': 'photo field required.'}, status=400)

    photo = request.FILES['photo']
    ok, err = _validate_photo(photo)
    if not ok:
        return Response({'error': err}, status=400)

    try:
        from engine_b2b.models import PartnerProfile
        partner = PartnerProfile.objects.get(user=request.user)
    except PartnerProfile.DoesNotExist:
        return Response({'error': 'Partner profile not found.'}, status=404)

    if partner.business_photo:
        try:
            partner.business_photo.delete(save=False)
        except Exception as e:
            logger.debug(f'Old business photo delete failed: {e}')

    partner.business_photo = photo
    partner.save(update_fields=['business_photo'])

    photo_url = (request.build_absolute_uri(partner.business_photo.url)
                 if partner.business_photo else None)

    return Response({'business_photo_url': photo_url})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_partner_photo(request):
    """DELETE /api/v1/partner/profile/photo/"""
    try:
        from engine_b2b.models import PartnerProfile
        partner = PartnerProfile.objects.get(user=request.user)
        if partner.business_photo:
            partner.business_photo.delete(save=True)
    except PartnerProfile.DoesNotExist:
        return Response({'error': 'Partner profile not found.'}, status=404)
    return Response({'message': 'Business photo removed.'})
