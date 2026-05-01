import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from engine_meta.models import User, PartnerService, AdminAction

logger = logging.getLogger(__name__)


def is_super_admin(user):
    return 'super_admin' in user.roles

def is_manager_or_above(user):
    return any(r in user.roles for r in ['super_admin', 'admin'])

def is_operator_or_above(user):
    return any(r in user.roles for r in ['super_admin', 'admin', 'operator'])

def log_admin_action(actor, action_type, target_type, target_id,
                     before=None, after=None):
    try:
        AdminAction.objects.create(
            actor=actor, action_type=action_type,
            target_type=target_type, target_id=str(target_id),
            before_state=before, after_state=after,
        )
    except Exception as e:
        logger.error(f'Admin action log failed: {e}')


class EngineConfigView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_manager_or_above(request.user):
            return Response({'error': 'Access denied.'}, status=403)
        from blueberry_backend.communications import get_engine_config
        return Response(get_engine_config())

    def patch(self, request):
        if not is_super_admin(request.user):
            return Response({'error': 'Super-admin only.'}, status=403)
        from engine_meta.models import EngineConfig
        from blueberry_backend.communications import invalidate_engine_config_cache
        config = EngineConfig.objects.get(id=1)
        before = {
            'w_reward': config.w_reward, 'w_arc': config.w_arc,
            'w_novelty': config.w_novelty, 'w_weather': config.w_weather,
        }
        allowed_fields = [
            'w_reward', 'w_arc', 'w_novelty', 'w_weather',
            'path_efficiency_floor', 'engine_shortlist_n',
            'yang_buffer_threshold', 'beam_width',
            'annealing_timeout_s', 'transit_threshold_min',
            'day_start_time', 'rest_trigger_time', 'dinner_as_node',
            'high_risk_threshold', 'noc_risk_threshold', 'noc_altitude_threshold',
            'rf_n_trees', 'rf_max_depth', 'rf_min_samples_leaf',
            'filler_rate_min', 'filler_rate_max',
            'default_guides_per_vehicle', 'default_coordinators_per_group',
            'assistance_tier_fees', 'coverage_floor', 'custom_coefficients',
        ]
        for field in allowed_fields:
            if field in request.data:
                setattr(config, field, request.data[field])
        total = config.w_reward + config.w_arc + config.w_novelty + config.w_weather
        if abs(total - 1.0) > 0.001:
            return Response(
                {'error': f'Push weights must sum to 1.0. Current sum: {total:.3f}'},
                status=400,
            )
        config.save()
        invalidate_engine_config_cache()
        log_admin_action(
            request.user, 'update_engine_config', 'EngineConfig', 1,
            before, {
                'w_reward': config.w_reward, 'w_arc': config.w_arc,
                'w_novelty': config.w_novelty, 'w_weather': config.w_weather,
            }
        )
        return Response({'message': 'Engine config updated.'})

class PartnerApprovalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_manager_or_above(request.user):
            return Response({'error': 'Access denied.'}, status=403)
        status_filter = request.query_params.get('status', 'pending')
        services = PartnerService.objects.filter(
            status=status_filter).select_related('user')
        data = [{
            'service_id': str(s.id),
            'partner_email': s.user.email,
            'partner_name': s.user.name,
            'service_type': s.service_type,
            'status': s.status,
            'license_document': s.license_document,
            'created_at': s.created_at,
            'verified_at': s.verified_at,
        } for s in services]
        return Response({'services': data})

    def patch(self, request, service_id):
        if not is_manager_or_above(request.user):
            return Response({'error': 'Access denied.'}, status=403)
        try:
            service = PartnerService.objects.get(id=service_id)
        except PartnerService.DoesNotExist:
            return Response({'error': 'Service not found.'}, status=404)
        new_status = request.data.get('status')
        if new_status not in ['verified', 'rejected', 'suspended']:
            return Response({'error': 'Invalid status.'}, status=400)
        before = {'status': service.status}
        service.status = new_status
        if new_status == 'verified':
            service.verified_at = timezone.now()
        service.save()
        log_admin_action(request.user, f'partner_service_{new_status}',
                         'PartnerService', service_id,
                         before, {'status': new_status})
        return Response({'message': f'Partner service {new_status}.', 'status': new_status})


class ManualKYCVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        if not is_manager_or_above(request.user):
            return Response({'error': 'Access denied.'}, status=403)
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)
        try:
            from kyc.models import KYCRecord
            kyc, _ = KYCRecord.objects.using('kyc').get_or_create(
                user_id=user_id,
                defaults={'nationality_type': 'indian' if target_user.nationality == 'Indian' else 'foreign'}
            )
            kyc.status = 'manually_verified'
            kyc.aadhaar_verified = True
            kyc.mobile_verified = True
            kyc.verified_at = timezone.now()
            kyc.save(using='kyc')
            # Notify partner their KYC is verified
            try:
                from engine_b2c.notifications import notify
                notify(
                    user_id           = str(user_id),
                    notification_type = 'partner_approved',
                    title             = 'KYC Verified',
                    body              = 'Your KYC has been manually verified. You can now accept bookings.',
                    action_url        = '/partner/dashboard/',
                    metadata          = {'verified_by': request.user.email},
                )
            except Exception as _e:
                logger.error(f'KYC approval notification failed: {_e}')

            log_admin_action(request.user, 'manual_kyc_verify', 'KYCRecord', user_id,
                             None, {'status': 'manually_verified'})
            return Response({'message': 'KYC manually verified.',
                             'warning': 'This is a manual verification — not UIDAI verified.'})
        except Exception as e:
            logger.error(f'Manual KYC verify failed: {e}')
            return Response({'error': 'Manual verification failed.'}, status=500)


class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_manager_or_above(request.user):
            return Response({'error': 'Access denied.'}, status=403)
        users = User.objects.all().order_by('-created_at')[:50]
        data = [{
            'user_id': str(u.id), 'email': u.email, 'name': u.name,
            'username': u.username, 'roles': u.roles,
            'is_active': u.is_active, 'created_at': u.created_at,
        } for u in users]
        return Response({'users': data})


class UserDeactivateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        if not is_super_admin(request.user):
            return Response({'error': 'Super-admin only.'}, status=403)
        try:
            target = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)
        if str(target.id) == str(request.user.id):
            return Response({'error': 'Cannot deactivate your own account.'}, status=400)
        target.is_active = False
        target.save(update_fields=['is_active'])
        log_admin_action(request.user, 'deactivate_user', 'User', user_id,
                         {'is_active': True}, {'is_active': False})
        return Response({'message': 'User deactivated.'})


class DisruptionOverrideView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not is_manager_or_above(request.user):
            return Response({'error': 'Access denied.'}, status=403)
        region_id = request.data.get('region_id')
        severity = request.data.get('severity')
        message = request.data.get('message')
        disruption_type = request.data.get('disruption_type', 'weather')
        if not all([region_id, severity, message]):
            return Response({'error': 'region_id, severity, message required.'}, status=400)
        from blueberry_backend.communications import set_disruption
        set_disruption(region_id, {
            'severity': severity, 'message': message,
            'set_by': request.user.email,
            'set_at': timezone.now().isoformat(),
        }, disruption_type)
        log_admin_action(request.user, 'disruption_override', 'Region', region_id,
                         None, {'severity': severity, 'message': message})
        return Response({'message': 'Disruption override set.', 'region_id': region_id})

    def delete(self, request):
        if not is_manager_or_above(request.user):
            return Response({'error': 'Access denied.'}, status=403)
        region_id = request.data.get('region_id')
        if not region_id:
            return Response({'error': 'region_id required.'}, status=400)
        from blueberry_backend.communications import clear_disruption
        clear_disruption(region_id)
        return Response({'message': 'Disruption cleared.'})


class CreateAdminUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not is_super_admin(request.user):
            return Response({'error': 'Super-admin only.'}, status=403)
        email = request.data.get('email')
        name = request.data.get('name')
        mobile = request.data.get('mobile')
        password = request.data.get('password')
        role = request.data.get('role')
        if role not in ['admin', 'operator']:
            return Response({'error': 'Role must be admin or operator.'}, status=400)
        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already registered.'}, status=400)
        user = User.objects.create_user(
            email=email, password=password, name=name,
            mobile=mobile, roles=[role], is_staff=True,
        )
        log_admin_action(request.user, f'create_{role}', 'User', user.id,
                         None, {'email': email, 'role': role})
        return Response({'message': f'{role} account created.', 'user_id': str(user.id)},
                        status=status.HTTP_201_CREATED)


class RegionManagementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_operator_or_above(request.user):
            return Response({'error': 'Access denied.'}, status=403)
        from engine_b2c.models import Region
        regions = Region.objects.all().order_by('zone', 'name')
        data = [{
            'id': str(r.id), 'name': r.name, 'state': r.state,
            'zone': r.zone, 'description': r.description,
            'image_url': r.image_url, 'lat': r.lat, 'lng': r.lng,
            'is_active': r.is_active,
        } for r in regions]
        return Response({'regions': data})

    def post(self, request):
        if not is_manager_or_above(request.user):
            return Response({'error': 'Access denied.'}, status=403)
        from engine_b2c.models import Region
        for field in ['name', 'state', 'zone']:
            if not request.data.get(field):
                return Response({'error': f'{field} is required.'}, status=400)
        valid_zones = ['uttar', 'poorab', 'pashchim', 'dakshin', 'madhyam']
        if request.data['zone'] not in valid_zones:
            return Response({'error': f'Invalid zone. Choose from: {valid_zones}'}, status=400)
        region = Region.objects.create(
            name=request.data['name'], state=request.data['state'],
            zone=request.data['zone'],
            description=request.data.get('description', ''),
            image_url=request.data.get('image_url', ''),
            lat=request.data.get('lat'), lng=request.data.get('lng'),
            is_active=request.data.get('is_active', True),
        )
        log_admin_action(request.user, 'create_region', 'Region', region.id,
                         None, {'name': region.name, 'zone': region.zone})
        return Response({'message': 'Region created.', 'id': str(region.id)},
                        status=status.HTTP_201_CREATED)

    def patch(self, request, region_id):
        if not is_manager_or_above(request.user):
            return Response({'error': 'Access denied.'}, status=403)
        from engine_b2c.models import Region
        try:
            region = Region.objects.get(id=region_id)
        except Region.DoesNotExist:
            return Response({'error': 'Region not found.'}, status=404)
        before = {'name': region.name, 'is_active': region.is_active}
        for field in ['name', 'state', 'zone', 'description',
                      'image_url', 'lat', 'lng', 'is_active']:
            if field in request.data:
                setattr(region, field, request.data[field])
        region.save()
        log_admin_action(request.user, 'update_region', 'Region', region_id,
                         before, {'name': region.name, 'is_active': region.is_active})
        return Response({'message': 'Region updated.', 'id': str(region.id)})


class ActivityManagementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_operator_or_above(request.user):
            return Response({'error': 'Access denied.'}, status=403)
        from engine_b2c.models import Activity
        status_filter = request.query_params.get('status', 'all')
        qs = Activity.objects.all().order_by('-created_at')
        if status_filter == 'pending':
            qs = qs.filter(content_approved=False)
        elif status_filter == 'approved':
            qs = qs.filter(content_approved=True)
        data = [{
            'id': str(a.id), 'name': a.name, 'region': str(a.region_id),
            'category': a.category, 'node_type': a.node_type,
            'effort_score': a.effort_score, 'reward_score': a.reward_score,
            'tone': a.tone, 'significance_score': a.significance_score,
            'content_approved': a.content_approved, 'is_active': a.is_active,
            'created_at': a.created_at,
        } for a in qs[:50]]
        return Response({'activities': data})

    def post(self, request):
        if not is_manager_or_above(request.user):
            return Response({'error': 'Access denied.'}, status=403)
        from engine_b2c.models import Activity, Region
        from engine_meta.ml.scoring_models import suggest_scores, add_training_sample
        for field in ['name', 'region_id', 'category', 'node_type']:
            if not request.data.get(field):
                return Response({'error': f'{field} is required.'}, status=400)
        try:
            region = Region.objects.get(id=request.data['region_id'])
        except Region.DoesNotExist:
            return Response({'error': 'Region not found.'}, status=404)
        activity_data = {
            'category': request.data.get('category'),
            'node_type': request.data.get('node_type'),
            'duration_hrs': request.data.get('duration_hrs', 1.0),
            'is_fixed_route': request.data.get('is_fixed_route', False),
            'time_of_day_sensitivity': request.data.get('time_of_day_sensitivity', False),
            'risk_tier': request.data.get('risk_tier', 'casual'),
            'tools': request.data.get('tools', []),
            'buffer_before_mins': request.data.get('buffer_before_mins', 15),
            'buffer_after_mins': request.data.get('buffer_after_mins', 15),
            'is_shiftable_anytime': request.data.get('is_shiftable_anytime', False),
        }
        suggestions = suggest_scores(activity_data)
        effort_score = request.data.get('effort_score') or suggestions.get('effort_score') or 0.5
        reward_score = request.data.get('reward_score') or suggestions.get('reward_score') or 0.5
        recovery_coeff = request.data.get('recovery_coeff') or suggestions.get('recovery_coeff') or 0.0
        significance_score = request.data.get('significance_score') or suggestions.get('significance_score') or 0.5
        tone = request.data.get('tone') or suggestions.get('tone') or 'both'
        activity = Activity.objects.create(
            region=region, name=request.data['name'],
            short_desc=request.data.get('short_desc', ''),
            description=request.data.get('description', ''),
            node_type=request.data['node_type'],
            lat=request.data.get('lat'), lng=request.data.get('lng'),
            category=request.data['category'],
            duration_hrs=request.data.get('duration_hrs', 1.0),
            price_from=request.data.get('price_from', 0),
            effort_score=effort_score, reward_score=reward_score,
            reward_score_base=request.data.get('reward_score_base', reward_score),
            reward_score_max=request.data.get('reward_score_max', reward_score),
            tone=tone, recovery_coeff=recovery_coeff,
            significance_score=significance_score,
            risk_tier=request.data.get('risk_tier', 'casual'),
            operating_months=request.data.get('operating_months', []),
            operating_hours=request.data.get('operating_hours', {}),
            preferred_time_windows=request.data.get('preferred_time_windows', []),
            functional_days=request.data.get('functional_days', []),
            holidays=request.data.get('holidays', []),
            allowance_time_mins=request.data.get('allowance_time_mins', 30),
            is_shiftable_anytime=request.data.get('is_shiftable_anytime', False),
            buffer_before_mins=request.data.get('buffer_before_mins', 15),
            buffer_after_mins=request.data.get('buffer_after_mins', 15),
            has_time_exception=request.data.get('has_time_exception', False),
            exception_start_time=request.data.get('exception_start_time'),
            tools=request.data.get('tools', []),
            dietary_support=request.data.get('dietary_support', []),
            is_filler=request.data.get('is_filler', False),
            content_approved=False, is_active=True,
        )
        if request.data.get('effort_score'):
            add_training_sample(activity_data, {
                'effort_score': effort_score, 'reward_score': reward_score,
                'recovery_coeff': recovery_coeff,
                'significance_score': significance_score, 'tone': tone,
            })
        log_admin_action(request.user, 'create_activity', 'Activity', activity.id,
                         None, {'name': activity.name})
        return Response({
            'message': 'Activity created. Pending content approval.',
            'id': str(activity.id), 'ml_suggestions': suggestions,
        }, status=status.HTTP_201_CREATED)

    def patch(self, request, activity_id):
        if not is_manager_or_above(request.user):
            return Response({'error': 'Access denied.'}, status=403)
        from engine_b2c.models import Activity
        from engine_meta.ml.scoring_models import add_training_sample
        try:
            activity = Activity.objects.get(id=activity_id)
        except Activity.DoesNotExist:
            return Response({'error': 'Activity not found.'}, status=404)
        before = {'content_approved': activity.content_approved}
        allowed_fields = [
            'name', 'short_desc', 'description', 'category',
            'effort_score', 'reward_score', 'reward_score_base', 'reward_score_max',
            'tone', 'recovery_coeff', 'significance_score', 'risk_tier',
            'duration_hrs', 'price_from', 'operating_months', 'operating_hours',
            'preferred_time_windows', 'functional_days', 'holidays',
            'allowance_time_mins', 'is_shiftable_anytime',
            'buffer_before_mins', 'buffer_after_mins', 'has_time_exception',
            'exception_start_time', 'tools', 'dietary_support',
            'is_active', 'content_approved', 'is_filler',
        ]
        score_updated = False
        for field in allowed_fields:
            if field in request.data:
                setattr(activity, field, request.data[field])
                if field in ['effort_score', 'reward_score',
                             'recovery_coeff', 'significance_score', 'tone']:
                    score_updated = True
        activity.save()
        if score_updated:
            add_training_sample({
                'category': activity.category, 'node_type': activity.node_type,
                'duration_hrs': activity.duration_hrs,
                'is_fixed_route': activity.is_fixed_route,
                'time_of_day_sensitivity': activity.time_of_day_sensitivity,
                'risk_tier': activity.risk_tier, 'tools': activity.tools,
                'buffer_before_mins': activity.buffer_before_mins,
                'buffer_after_mins': activity.buffer_after_mins,
                'is_shiftable_anytime': activity.is_shiftable_anytime,
            }, {
                'effort_score': activity.effort_score,
                'reward_score': activity.reward_score,
                'recovery_coeff': activity.recovery_coeff,
                'significance_score': activity.significance_score,
                'tone': activity.tone,
            })
        log_admin_action(request.user, 'update_activity', 'Activity', activity_id,
                         before, {'content_approved': activity.content_approved})
        return Response({'message': 'Activity updated.', 'id': str(activity_id)})


class MLModelStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_manager_or_above(request.user):
            return Response({'error': 'Access denied.'}, status=403)
        from engine_meta.models import ScoringModel, ScoringTrainingSample
        from engine_meta.ml.scoring_models import SCORE_MODELS
        total_samples = ScoringTrainingSample.objects.count()
        models = ScoringModel.objects.all()
        trained_types = [m.score_type for m in models]
        data = [{
            'score_type': m.score_type, 'is_trained': m.is_trained,
            'training_samples': m.training_samples,
            'last_trained_at': m.last_trained_at,
        } for m in models]
        for score_type in SCORE_MODELS:
            if score_type not in trained_types:
                data.append({'score_type': score_type, 'is_trained': False,
                             'training_samples': 0, 'last_trained_at': None})
        return Response({
            'total_training_samples': total_samples,
            'samples_needed_to_train': max(0, 10 - total_samples),
            'models': data,
        })

class AdminNotificationView(APIView):
    """
    GET  /api/v1/admin/notifications/           all admin notifications
    GET  /api/v1/admin/notifications/?urgent=1  urgent only
    POST /api/v1/admin/notifications/read-all/  mark all admin notifs read
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_operator_or_above(request.user):
            return Response({'error': 'Access denied.'}, status=403)
        from engine_b2c.models import Notification
        qs = Notification.objects.filter(
            user_id       = str(request.user.id),
            recipient_role= 'admin',
        ).order_by('-created_at')[:50]
        if request.query_params.get('urgent') == '1':
            qs = qs.filter(is_urgent=True)
        unread = Notification.objects.filter(
            user_id       = str(request.user.id),
            recipient_role= 'admin',
            is_read       = False,
        ).count()
        return Response({
            'unread_count':  unread,
            'notifications': [n.to_dict() for n in qs],
        })

    def post(self, request):
        if not is_operator_or_above(request.user):
            return Response({'error': 'Access denied.'}, status=403)
        from engine_b2c.models import Notification
        from django.utils import timezone
        Notification.objects.filter(
            user_id       = str(request.user.id),
            recipient_role= 'admin',
            is_read       = False,
        ).update(is_read=True, read_at=timezone.now())
        return Response({'marked_read': True})


class VoucherManagementView(APIView):
    """
    GET    /api/v1/admin/vouchers/              list all vouchers
    POST   /api/v1/admin/vouchers/              create voucher
    GET    /api/v1/admin/vouchers/<id>/         voucher detail + redemption stats
    PATCH  /api/v1/admin/vouchers/<id>/         update (activate/deactivate)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, voucher_id=None):
        if not is_operator_or_above(request.user):
            return Response({'error': 'Access denied.'}, status=403)
        from engine_b2c.models import PromoVoucher, VoucherRedemption

        if voucher_id:
            try:
                v = PromoVoucher.objects.get(id=voucher_id)
            except PromoVoucher.DoesNotExist:
                return Response({'error': 'Not found.'}, status=404)
            redemptions = VoucherRedemption.objects.filter(
                voucher=v).order_by('-redeemed_at')[:20]
            return Response({
                **_voucher_dict(v),
                'recent_redemptions': [{
                    'booking_id':      str(r.booking_id),
                    'user_id':         r.user_id,
                    'discount':        str(r.discount_applied),
                    'redeemed_at':     r.redeemed_at.isoformat(),
                } for r in redemptions],
            })

        vouchers = PromoVoucher.objects.all().order_by('-created_at')
        if request.query_params.get('active') == '1':
            vouchers = vouchers.filter(is_active=True)
        return Response({'vouchers': [_voucher_dict(v) for v in vouchers]})

    def post(self, request):
        if not is_operator_or_above(request.user):
            return Response({'error': 'Access denied.'}, status=403)
        from engine_b2c.models import PromoVoucher
        from django.utils import timezone

        required = ['code_prefix', 'discount_type', 'discount_value',
                    'valid_from', 'valid_until']
        for field in required:
            if not request.data.get(field):
                return Response({'error': f'{field} is required.'}, status=400)

        try:
            v = PromoVoucher.objects.create(
                code_prefix         = str(request.data['code_prefix']).upper().strip(),
                description         = request.data.get('description', ''),
                discount_type       = request.data['discount_type'],
                discount_value      = request.data['discount_value'],
                max_discount_amount = request.data.get('max_discount_amount', 0),
                min_booking_amount  = request.data.get('min_booking_amount', 0),
                valid_from          = request.data['valid_from'],
                valid_until         = request.data['valid_until'],
                usage_limit_per_day = int(request.data.get('usage_limit_per_day', 0)),
                total_usage_limit   = int(request.data.get('total_usage_limit', 0)),
                restricted_regions  = request.data.get('restricted_regions', []),
                is_active           = True,
                created_by          = str(request.user.id),
            )
            log_admin_action(request.user, 'create_voucher', 'PromoVoucher',
                             str(v.id), None, _voucher_dict(v))
            return Response(_voucher_dict(v), status=201)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    def patch(self, request, voucher_id=None):
        if not is_operator_or_above(request.user):
            return Response({'error': 'Access denied.'}, status=403)
        from engine_b2c.models import PromoVoucher
        try:
            v = PromoVoucher.objects.get(id=voucher_id)
        except PromoVoucher.DoesNotExist:
            return Response({'error': 'Not found.'}, status=404)

        before = _voucher_dict(v)
        allowed = ['is_active', 'description', 'valid_until',
                   'usage_limit_per_day', 'total_usage_limit',
                   'max_discount_amount', 'min_booking_amount']
        for field in allowed:
            if field in request.data:
                setattr(v, field, request.data[field])
        v.save()
        log_admin_action(request.user, 'update_voucher', 'PromoVoucher',
                         str(v.id), before, _voucher_dict(v))
        return Response(_voucher_dict(v))


def _voucher_dict(v) -> dict:
    return {
        'id':                  str(v.id),
        'code':                v.code,
        'code_prefix':         v.code_prefix,
        'description':         v.description,
        'discount_type':       v.discount_type,
        'discount_value':      str(v.discount_value),
        'max_discount_amount': str(v.max_discount_amount),
        'min_booking_amount':  str(v.min_booking_amount),
        'valid_from':          v.valid_from.isoformat(),
        'valid_until':         v.valid_until.isoformat(),
        'usage_limit_per_day': v.usage_limit_per_day,
        'total_usage_limit':   v.total_usage_limit,
        'total_used':          v.total_used,
        'used_today':          v.used_today,
        'restricted_regions':  v.restricted_regions,
        'is_active':           v.is_active,
        'created_at':          v.created_at.isoformat(),
    }


class CoordinatorAnalyticsView(APIView):
    """GET /api/v1/admin/coordinator/analytics/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_operator_or_above(request.user):
            return Response({'error': 'Access denied.'}, status=403)
        from engine_meta.coordinator.placeholder import get_analytics
        return Response(get_analytics())
