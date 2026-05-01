import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from engine_meta.serializers import (
    CustomerRegistrationSerializer, PartnerRegistrationSerializer,
    LoginSerializer, UserProfileSerializer, PartnerServiceSerializer,
)
from engine_meta.models import User, PartnerService
from blueberry_backend.jwt_utils import (
    get_customer_tokens, get_partner_tokens, get_admin_tokens,
)
from blueberry_backend.communications import (
    store_guest_token, get_guest_token, delete_guest_token,
)

logger = logging.getLogger(__name__)


class CustomerRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CustomerRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            tokens = get_customer_tokens(user)
            return Response({
                'message': 'Registration successful.',
                'user_id': str(user.id),
                'username': user.username,
                **tokens,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PartnerRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PartnerRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            tokens = get_partner_tokens(user)
            return Response({
                'message': 'Partner registration successful. Please complete KYC.',
                'user_id': str(user.id),
                **tokens,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            context = serializer.validated_data['login_context']
            if context == 'partner':
                tokens = get_partner_tokens(user)
            elif context == 'admin':
                tokens = get_admin_tokens(user)
            else:
                tokens = get_customer_tokens(user)
            guest_token = request.data.get('guest_token')
            if guest_token:
                guest_data = get_guest_token(guest_token)
                if guest_data:
                    delete_guest_token(guest_token)
            return Response({
                'message': 'Login successful.',
                'user_id': str(user.id),
                'username': user.username,
                'roles': user.roles,
                **tokens,
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Logged out successfully.'})
        except TokenError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if not refresh_token:
                return Response({'error': 'Refresh token required.'},
                                status=status.HTTP_400_BAD_REQUEST)
            token = RefreshToken(refresh_token)
            return Response({'access': str(token.access_token)})
        except TokenError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)


class GuestSessionView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        import uuid
        from django.utils import timezone
        token = str(uuid.uuid4())
        store_guest_token(token, {
            'created_at': timezone.now().isoformat(),
            'activity_ids': [],
            'region_id': None,
            'bias_state': {},
        })
        return Response({'guest_token': token, 'expires_in': '24 hours'})


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileSerializer(
            request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PartnerServiceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if 'partner' not in request.user.roles:
            return Response({'error': 'Partner account required.'}, status=403)
        services = PartnerService.objects.filter(user=request.user)
        return Response(PartnerServiceSerializer(services, many=True).data)

    def post(self, request):
        if 'partner' not in request.user.roles:
            return Response({'error': 'Partner account required.'}, status=403)
        service_type = request.data.get('service_type')
        if PartnerService.objects.filter(
                user=request.user, service_type=service_type).exists():
            return Response({'error': 'Already registered for this service type.'}, status=400)
        if PartnerService.objects.filter(user=request.user).count() >= 5:
            return Response({'error': 'Maximum 5 service types allowed.'}, status=400)
        serializer = PartnerServiceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, status='pending')
            return Response({
                'message': 'Service registration submitted. Pending admin approval.',
                **serializer.data,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddPartnerRoleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        business_name = request.data.get('business_name')
        if not business_name:
            return Response({'error': 'Business name required.'}, status=400)
        if 'partner' in user.roles:
            return Response({'error': 'Already a partner.'}, status=400)
        user.roles = list(set(user.roles + ['partner']))
        user.save(update_fields=['roles'])
        from engine_b2b.models import PartnerProfile
        PartnerProfile.objects.get_or_create(
            user=user, defaults={'business_name': business_name})
        tokens = get_partner_tokens(user)
        return Response({
            'message': 'Partner role added. Please complete KYC.',
            'roles': user.roles,
            **tokens,
        })