import hashlib
import logging
import uuid
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

logger = logging.getLogger(__name__)

DUMMY_UIDAI_WARNING = (
    'UIDAI_STUB: This is a dummy response. '
    'Real UIDAI API not connected. Do not use in production.'
)


def hash_aadhaar(aadhaar_number):
    return hashlib.sha256(aadhaar_number.encode()).hexdigest()


class SendOTPView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        mobile = request.data.get('mobile')
        purpose = request.data.get('purpose', 'kyc')
        if not mobile:
            return Response({'error': 'Mobile number required.'}, status=400)
        from django.core.cache import cache
        otp = str(uuid.uuid4().int)[:6]
        cache.set(f'otp:{request.user.id}:{purpose}',
                  {'otp': otp, 'mobile': mobile}, timeout=300)
        return Response({
            'message': 'OTP sent successfully.',
            'stub_warning': DUMMY_UIDAI_WARNING,
            'dev_otp': otp,
        })


class VerifyOTPView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        otp_entered = request.data.get('otp')
        purpose = request.data.get('purpose', 'kyc')
        if not otp_entered:
            return Response({'error': 'OTP required.'}, status=400)
        from django.core.cache import cache
        cached = cache.get(f'otp:{request.user.id}:{purpose}')
        if not cached:
            return Response({'error': 'OTP expired. Please request a new one.'}, status=400)
        if cached['otp'] != otp_entered:
            return Response({'error': 'Invalid OTP.'}, status=400)
        try:
            from kyc.models import KYCRecord
            kyc, _ = KYCRecord.objects.using('kyc').get_or_create(
                user_id=request.user.id,
                defaults={
                    'nationality_type': 'indian' if request.user.nationality == 'Indian' else 'foreign',
                    'mobile': cached['mobile'],
                }
            )
            kyc.mobile_verified = True
            kyc.mobile = cached['mobile']
            kyc.save(using='kyc')
            cache.delete(f'otp:{request.user.id}:{purpose}')
            return Response({'message': 'Mobile verified.', 'mobile_verified': True})
        except Exception as e:
            logger.error(f'KYC update failed: {e}')
            return Response({'error': 'Verification failed.'}, status=500)


class AadhaarOTPSendView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        aadhaar_number = request.data.get('aadhaar_number')
        if not aadhaar_number or len(aadhaar_number) != 12 or not aadhaar_number.isdigit():
            return Response({'error': 'Valid 12-digit Aadhaar number required.'}, status=400)
        aadhaar_hash = hash_aadhaar(aadhaar_number)
        from kyc.models import KYCRecord
        if KYCRecord.objects.using('kyc').filter(
                aadhaar_hash=aadhaar_hash).exclude(
                user_id=request.user.id).exists():
            return Response(
                {'error': 'This Aadhaar is already linked to another account.'}, status=400)
        from django.core.cache import cache
        cache.set(f'aadhaar_pending:{request.user.id}',
                  {'aadhaar_hash': aadhaar_hash, 'stub_otp': '123456'}, timeout=300)
        del aadhaar_number
        return Response({
            'message': 'OTP sent to Aadhaar-linked mobile.',
            'stub_warning': DUMMY_UIDAI_WARNING,
            'dev_otp': '123456',
        })


class AadhaarOTPVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        otp = request.data.get('otp')
        if not otp:
            return Response({'error': 'OTP required.'}, status=400)
        from django.core.cache import cache
        pending = cache.get(f'aadhaar_pending:{request.user.id}')
        if not pending:
            return Response({'error': 'Session expired. Restart Aadhaar verification.'}, status=400)
        if otp != pending['stub_otp']:
            return Response({'error': 'Invalid OTP.'}, status=400)
        try:
            from kyc.models import KYCRecord
            kyc, _ = KYCRecord.objects.using('kyc').get_or_create(
                user_id=request.user.id,
                defaults={'nationality_type': 'indian'}
            )
            kyc.aadhaar_hash = pending['aadhaar_hash']
            kyc.aadhaar_verified = True
            kyc.name_as_on_aadhaar = request.user.name
            kyc.is_partner_kyc = 'partner' in request.user.roles
            if kyc.mobile_verified:
                kyc.status = 'dummy_verified'
                kyc.verified_at = timezone.now()
            kyc.save(using='kyc')
            cache.delete(f'aadhaar_pending:{request.user.id}')
            return Response({
                'message': 'Aadhaar verified.',
                'aadhaar_verified': True,
                'kyc_complete': kyc.mobile_verified,
                'stub_warning': DUMMY_UIDAI_WARNING,
            })
        except Exception as e:
            logger.error(f'KYC update failed: {e}')
            return Response({'error': 'Verification failed.'}, status=500)


class PassportMRZView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        mrz_line1 = request.data.get('mrz_line1')
        mrz_line2 = request.data.get('mrz_line2')
        if not mrz_line1 or not mrz_line2:
            return Response({'error': 'Both MRZ lines required.'}, status=400)
        try:
            from mrz.checker.td3 import TD3CodeChecker
            checker = TD3CodeChecker(mrz_line1 + mrz_line2)
            if not checker.valid:
                return Response({'error': 'Invalid MRZ format.'}, status=400)
            fields = checker.fields()
            name = f'{fields.name} {fields.surname}'.strip()
            from kyc.models import KYCRecord
            kyc, _ = KYCRecord.objects.using('kyc').get_or_create(
                user_id=request.user.id,
                defaults={'nationality_type': 'foreign'}
            )
            kyc.mrz_line1 = mrz_line1
            kyc.mrz_line2 = mrz_line2
            kyc.name_as_on_passport = name
            kyc.passport_ref = fields.document_number
            kyc.passport_verified = False
            kyc.save(using='kyc')
            return Response({
                'message': 'Passport MRZ parsed. Pending admin review.',
                'name_on_passport': name,
                'passport_verified': False,
            })
        except ImportError:
            return Response(
                {'error': 'MRZ library not installed. Run: pip install mrz'}, status=500)
        except Exception as e:
            logger.error(f'MRZ parsing failed: {e}')
            return Response({'error': 'MRZ parsing failed.'}, status=500)


class KYCStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from kyc.models import KYCRecord
            kyc = KYCRecord.objects.using('kyc').get(user_id=request.user.id)
            return Response({
                'kyc_status': kyc.status,
                'mobile_verified': kyc.mobile_verified,
                'aadhaar_verified': kyc.aadhaar_verified,
                'passport_verified': kyc.passport_verified,
                'nationality_type': kyc.nationality_type,
                'verified_at': kyc.verified_at,
            })
        except Exception:
            return Response({
                'kyc_status': 'not_started',
                'mobile_verified': False,
                'aadhaar_verified': False,
                'passport_verified': False,
            })