from django.urls import path
from engine_meta import views, kyc_views, photo_views

app_name = 'engine_meta'

urlpatterns = [
    path('register/',            views.CustomerRegisterView.as_view(),  name='customer_register'),
    path('login/',               views.LoginView.as_view(),              name='login'),
    path('logout/',              views.LogoutView.as_view(),             name='logout'),
    path('refresh/',             views.TokenRefreshView.as_view(),       name='token_refresh'),
    path('guest/',               views.GuestSessionView.as_view(),       name='guest_session'),
    path('partner/register/',    views.PartnerRegisterView.as_view(),    name='partner_register'),
    path('partner/add-role/',    views.AddPartnerRoleView.as_view(),     name='add_partner_role'),
    path('partner/services/',    views.PartnerServiceView.as_view(),     name='partner_services'),
    path('profile/',             views.UserProfileView.as_view(),        name='user_profile'),
    path('profile/photo/', photo_views.upload_profile_photo, name='upload_profile_photo'),
    path('profile/photo/delete/', photo_views.delete_profile_photo, name='delete_profile_photo'),
    path('kyc/status/',          kyc_views.KYCStatusView.as_view(),      name='kyc_status'),
    path('kyc/otp/send/',        kyc_views.SendOTPView.as_view(),        name='otp_send'),
    path('kyc/otp/verify/',      kyc_views.VerifyOTPView.as_view(),      name='otp_verify'),
    path('kyc/aadhaar/send/',    kyc_views.AadhaarOTPSendView.as_view(), name='aadhaar_otp_send'),
    path('kyc/aadhaar/verify/',  kyc_views.AadhaarOTPVerifyView.as_view(),name='aadhaar_otp_verify'),
    path('kyc/passport/mrz/',    kyc_views.PassportMRZView.as_view(),    name='passport_mrz'),
]