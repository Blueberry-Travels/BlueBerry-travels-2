import logging
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

logger = logging.getLogger(__name__)


class JWTRoleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if self._is_public(path):
            return self.get_response(request)
        token = self._extract_token(request)
        if token:
            try:
                decoded = AccessToken(token)
                roles = decoded.get('roles', [])
                token_type = decoded.get('token_type_custom', 'customer')
                if token_type == 'partner' and self._is_customer_endpoint(path):
                    return JsonResponse(
                        {'error': 'Access denied. Partner token not valid on this endpoint.'},
                        status=403
                    )
                if token_type == 'customer' and self._is_partner_endpoint(path):
                    return JsonResponse(
                        {'error': 'Access denied. Customer token not valid on this endpoint.'},
                        status=403
                    )
                if self._is_admin_endpoint(path):
                    if 'admin' not in roles and 'super_admin' not in roles:
                        return JsonResponse(
                            {'error': 'Access denied. Admin token required.'},
                            status=403
                        )
                request.token_roles = roles
                request.token_type = token_type
                request.user_id = decoded.get('user_id')
            except (InvalidToken, TokenError):
                pass
        return self.get_response(request)

    def _extract_token(self, request):
        auth = request.META.get('HTTP_AUTHORIZATION', '')
        if auth.startswith('Bearer '):
            return auth.split(' ')[1]
        return None

    def _is_public(self, path):
        return any(path.startswith(p) for p in [
            '/admin/', '/api/v1/auth/', '/api/v1/featured/',
            '/api/v1/activities/', '/api/v1/packages/',
            '/api/v1/regions/', '/api/v1/events/',
            '/api/v1/blogs/', '/api/v1/quiz/',
            '/api/v1/assistant/', '/comm/webhook/',
        ])

    def _is_customer_endpoint(self, path):
        return (path.startswith('/api/v1/') and
                not path.startswith('/api/v1/partner/') and
                not path.startswith('/api/v1/admin/'))

    def _is_partner_endpoint(self, path):
        return path.startswith('/api/v1/partner/')

    def _is_admin_endpoint(self, path):
        return path.startswith('/api/v1/admin/')