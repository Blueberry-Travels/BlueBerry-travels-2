import logging
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

CACHE_KEYS = {
    'engine_config':        'meta:engine_config',
    'region_config':        'meta:region_config:{region_id}',
    'disruption':           'l3:disruption:{region_id}',
    'distance_matrix':      'l1:distance_matrix:{region_id}',
    'partner_availability': 'partner:availability:{partner_id}:{date}',
    'rate_limit':           'rate:{user_id}:{action}',
    'guest_token':          'guest:{token}',
    'notification_status':  'notif:{notification_id}:status',
}

TTL = {
    'engine_config':        3600,
    'region_config':        3600,
    'disruption_weather':   14400,
    'disruption_road':      86400,
    'distance_matrix':      86400,
    'partner_availability': 300,
    'guest_token':          86400,
    'notification_status':  1800,
}


def get_engine_config():
    cache_key = CACHE_KEYS['engine_config']
    config = cache.get(cache_key)
    if config:
        return config
    try:
        from engine_meta.models import EngineConfig
        obj = EngineConfig.objects.get(id=1)
        config = {
            'a': obj.a, 'b': obj.b, 'c': obj.c,
            'path_efficiency_floor':          obj.path_efficiency_floor,
            'engine_shortlist_n':             obj.engine_shortlist_n,
            'yang_buffer_threshold':          obj.yang_buffer_threshold,
            'beam_width':                     obj.beam_width,
            'annealing_timeout_s':            obj.annealing_timeout_s,
            'day_start_time':                 str(obj.day_start_time),
            'rest_trigger_time':              str(obj.rest_trigger_time),
            'dinner_as_node':                 obj.dinner_as_node,
            'high_risk_threshold':            obj.high_risk_threshold,
            'default_guides_per_vehicle':     obj.default_guides_per_vehicle,
            'default_coordinators_per_group': obj.default_coordinators_per_group,
            'bookingcom_enabled':   obj.bookingcom_enabled,
            'is_coordinator_active':       obj.is_coordinator_active,
            'coordinator_offline_msg':     obj.coordinator_offline_msg,
            'coordinator_storage_quota_mb':obj.coordinator_storage_quota_mb,
            'bookingcom_api_key':   obj.bookingcom_api_key,
            'bookingcom_affiliate': obj.bookingcom_affiliate,
            'assistance_tier_fees':           obj.assistance_tier_fees,
            'coverage_floor':                 obj.coverage_floor,
            'custom_coefficients':            obj.custom_coefficients,
        }
        cache.set(cache_key, config, timeout=TTL['engine_config'])
        return config
    except Exception as e:
        logger.error(f'EngineConfig read failed: {e}. Using defaults.')
        return {
            'a': 0.33, 'b': 0.33, 'c': 0.34,
            'path_efficiency_floor': 0.65,
            'engine_shortlist_n': 5,
            'yang_buffer_threshold': 0.5,
            'beam_width': 50,
            'annealing_timeout_s': 30,
            'day_start_time': '07:00:00',
            'rest_trigger_time': '18:00:00',
            'dinner_as_node': False,
            'high_risk_threshold': 0.7,
            'default_guides_per_vehicle': 1,
            'default_coordinators_per_group': 1,
            'assistance_tier_fees': {},
            'coverage_floor': {},
            'custom_coefficients': {},
            'bookingcom_enabled':   True,
            'bookingcom_api_key':   '',
            'bookingcom_affiliate': '',
        }


def get_region_config(region_id):
    cache_key = CACHE_KEYS['region_config'].format(region_id=region_id)
    config = cache.get(cache_key)
    if config:
        return config
    try:
        from engine_meta.models import RegionConfig
        obj = RegionConfig.objects.get(id=region_id)
        config = {
            'w_reward':  obj.w_reward,
            'w_arc':     obj.w_arc,
            'w_novelty': obj.w_novelty,
            'w_weather': obj.w_weather,
            'path_efficiency_floor':          obj.path_efficiency_floor,
            'engine_shortlist_n':             obj.engine_shortlist_n,
            'yang_buffer_threshold':          obj.yang_buffer_threshold,
            'beam_width':                     obj.beam_width,
            'annealing_timeout_s':            obj.annealing_timeout_s,
            'transit_threshold_min':          obj.transit_threshold_min,
            'day_start_time':                 str(obj.day_start_time),
            'rest_trigger_time':              str(obj.rest_trigger_time),
            'dinner_as_node':                 obj.dinner_as_node,
            'high_risk_threshold':            obj.high_risk_threshold,
            'noc_risk_threshold':             obj.noc_risk_threshold,
            'noc_altitude_threshold':         obj.noc_altitude_threshold,
            'rf_n_trees':                     obj.rf_n_trees,
            'rf_max_depth':                   obj.rf_max_depth,
            'rf_min_samples_leaf':            obj.rf_min_samples_leaf,
            'filler_rate_min':                obj.filler_rate_min,
            'filler_rate_max':                obj.filler_rate_max,
            'default_guides_per_vehicle':     obj.default_guides_per_vehicle,
            'default_coordinators_per_group': obj.default_coordinators_per_group,
            'assistance_tier_fees':           obj.assistance_tier_fees,
            'coverage_floor':                 obj.coverage_floor,
            'custom_coefficients':            obj.custom_coefficients,
        }
        cache.set(cache_key, config, timeout=TTL['region_config'])
        return config
    except Exception:
        return {
            'w_reward': 0.400, 'w_arc': 0.250,
            'w_novelty': 0.200, 'w_weather': 0.150,
            'path_efficiency_floor': 0.65,
            'engine_shortlist_n': 5,
            'yang_buffer_threshold': 0.5,
            'beam_width': 50,
            'annealing_timeout_s': 30,
            'transit_threshold_min': 45,
            'day_start_time': '07:00:00',
            'rest_trigger_time': '18:00:00',
            'dinner_as_node': False,
            'high_risk_threshold': 0.7,
            'noc_risk_threshold': 0.65,
            'noc_altitude_threshold': 4000,
            'rf_n_trees': 100,
            'rf_max_depth': 10,
            'rf_min_samples_leaf': 5,
            'filler_rate_min': 0.10,
            'filler_rate_max': 0.18,
            'default_guides_per_vehicle': 1,
            'default_coordinators_per_group': 1,
            'assistance_tier_fees': {},
            'coverage_floor': {},
            'custom_coefficients': {},
        }


def invalidate_engine_config_cache():
    cache.delete(CACHE_KEYS['engine_config'])
    logger.info('EngineConfig cache invalidated')


def get_disruption(region_id):
    cache_key = CACHE_KEYS['disruption'].format(region_id=region_id)
    try:
        return cache.get(cache_key)
    except Exception:
        return None


def set_disruption(region_id, disruption_data, disruption_type='weather'):
    cache_key = CACHE_KEYS['disruption'].format(region_id=region_id)
    ttl = TTL['disruption_weather'] if disruption_type == 'weather' else TTL['disruption_road']
    try:
        cache.set(cache_key, disruption_data, timeout=ttl)
        return True
    except Exception:
        return False


def clear_disruption(region_id):
    cache.delete(CACHE_KEYS['disruption'].format(region_id=region_id))


def get_distance_matrix(region_id):
    try:
        return cache.get(CACHE_KEYS['distance_matrix'].format(region_id=region_id))
    except Exception:
        return None


def set_distance_matrix(region_id, matrix):
    try:
        cache.set(
            CACHE_KEYS['distance_matrix'].format(region_id=region_id),
            matrix, timeout=TTL['distance_matrix']
        )
        return True
    except Exception:
        return False


def get_partner_availability(partner_id, date):
    cache_key = CACHE_KEYS['partner_availability'].format(
        partner_id=partner_id, date=date)
    try:
        val = cache.get(cache_key)
        if val is not None:
            return val
        from engine_b2b.models import PartnerProfile
        partner = PartnerProfile.objects.get(id=partner_id)
        is_available = partner.status == 'active' and partner.failure_count < 3
        cache.set(cache_key, is_available, timeout=TTL['partner_availability'])
        return is_available
    except Exception:
        return False


def set_partner_availability(partner_id, date, is_available):
    try:
        cache.set(
            CACHE_KEYS['partner_availability'].format(
                partner_id=partner_id, date=date),
            is_available, timeout=TTL['partner_availability']
        )
        return True
    except Exception:
        return False


def check_rate_limit(user_id, action, limit, window_seconds):
    cache_key = CACHE_KEYS['rate_limit'].format(user_id=user_id, action=action)
    try:
        current = cache.get(cache_key, 0)
        if current >= limit:
            return False, current, limit
        cache.set(cache_key, current + 1, timeout=window_seconds)
        return True, current + 1, limit
    except Exception:
        return True, 0, limit


def set_notification_status(notification_id, status):
    try:
        cache.set(
            CACHE_KEYS['notification_status'].format(
                notification_id=notification_id),
            {'status': status, 'updated_at': timezone.now().isoformat()},
            timeout=TTL['notification_status']
        )
        return True
    except Exception:
        return False


def get_notification_status(notification_id):
    try:
        return cache.get(
            CACHE_KEYS['notification_status'].format(
                notification_id=notification_id)
        )
    except Exception:
        return None


def store_guest_token(token, data):
    try:
        cache.set(
            CACHE_KEYS['guest_token'].format(token=token),
            data, timeout=TTL['guest_token']
        )
        return True
    except Exception:
        return False


def get_guest_token(token):
    try:
        return cache.get(CACHE_KEYS['guest_token'].format(token=token))
    except Exception:
        return None


def delete_guest_token(token):
    cache.delete(CACHE_KEYS['guest_token'].format(token=token))