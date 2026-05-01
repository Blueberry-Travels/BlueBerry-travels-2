from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta


def get_customer_tokens(user):
    refresh = RefreshToken.for_user(user)
    refresh['roles'] = user.roles
    refresh['token_type_custom'] = 'customer'
    refresh['user_id'] = str(user.id)
    refresh['username'] = user.username
    refresh['email'] = user.email
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user_id': str(user.id),
        'roles': user.roles,
        'token_type': 'customer',
    }


def get_partner_tokens(user):
    refresh = RefreshToken.for_user(user)
    refresh.access_token.set_exp(lifetime=timedelta(hours=8))
    refresh['roles'] = user.roles
    refresh['token_type_custom'] = 'partner'
    refresh['user_id'] = str(user.id)
    refresh['username'] = user.username
    refresh['email'] = user.email
    try:
        profile = user.partner_profile
        refresh['partner_id'] = str(profile.id)
        refresh['business_name'] = profile.business_name
        refresh['commission_rate'] = profile.commission_rate
    except Exception:
        refresh['partner_id'] = None
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user_id': str(user.id),
        'roles': user.roles,
        'token_type': 'partner',
    }


def get_admin_tokens(user):
    if not any(r in user.roles for r in ['admin', 'super_admin']):
        raise ValueError('User does not have admin role')
    refresh = RefreshToken.for_user(user)
    refresh.access_token.set_exp(lifetime=timedelta(hours=8))
    refresh['roles'] = user.roles
    refresh['token_type_custom'] = 'admin'
    refresh['user_id'] = str(user.id)
    refresh['email'] = user.email
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user_id': str(user.id),
        'roles': user.roles,
        'token_type': 'admin',
    }