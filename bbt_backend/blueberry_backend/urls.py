from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from engine_b2c import booking_views, notification_views

urlpatterns = [
    path('admin/',                   admin.site.urls),
    path('api/v1/auth/',             include('engine_meta.urls',       namespace='engine_meta')),
    path('api/v1/',                  include('engine_b2c.urls',        namespace='engine_b2c')),
    path('api/v1/partner/',          include('engine_b2b.urls',        namespace='engine_b2b')),
    path('api/v1/admin/',            include('engine_meta.admin_urls', namespace='engine_meta_admin')),
    # Webhooks (public — no namespace)
    path('comm/webhook/razorpay/',   booking_views.razorpay_webhook,              name='razorpay_webhook'),
    path('comm/webhook/whatsapp/',   notification_views.whatsapp_webhook,         name='whatsapp_webhook'),
    path('comm/webhook/whatsapp/verify/', notification_views.whatsapp_webhook_verify, name='whatsapp_verify'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
