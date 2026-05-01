from django.urls import path
from engine_meta import admin_views
from engine_b2c import views as b2c_views

app_name = 'engine_meta_admin'

urlpatterns = [
    path('engine-config/',               admin_views.EngineConfigView.as_view(),       name='engine_config'),
    path('partners/',                    admin_views.PartnerApprovalView.as_view(),    name='partner_list'),
    path('partners/<uuid:service_id>/',  admin_views.PartnerApprovalView.as_view(),    name='partner_approve'),
    path('kyc/verify/<uuid:user_id>/',   admin_views.ManualKYCVerifyView.as_view(),    name='manual_kyc_verify'),
    path('users/',                       admin_views.UserListView.as_view(),            name='user_list'),
    path('users/<uuid:user_id>/deactivate/', admin_views.UserDeactivateView.as_view(), name='user_deactivate'),
    path('disruption/',                  admin_views.DisruptionOverrideView.as_view(),  name='disruption_override'),
    path('create-admin/',                admin_views.CreateAdminUserView.as_view(),     name='create_admin'),
    path('regions/',                     admin_views.RegionManagementView.as_view(),    name='region_list'),
    path('regions/<uuid:region_id>/',    admin_views.RegionManagementView.as_view(),    name='region_detail'),
    path('activities/',                  admin_views.ActivityManagementView.as_view(),  name='activity_list'),
    path('activities/<uuid:activity_id>/',admin_views.ActivityManagementView.as_view(), name='activity_detail'),
    path('ml/status/',                   admin_views.MLModelStatusView.as_view(),       name='ml_status'),
    path('notifications/',               admin_views.AdminNotificationView.as_view(),    name='admin_notifications'),
    path('vouchers/',                    admin_views.VoucherManagementView.as_view(),    name='voucher_list'),
    path('coordinator/analytics/',       admin_views.CoordinatorAnalyticsView.as_view(), name='coordinator_analytics'),
    path('vouchers/<uuid:voucher_id>/',  admin_views.VoucherManagementView.as_view(),   name='voucher_detail'),
    path('api-status/',                  b2c_views.api_status,                          name='api_status'),
]