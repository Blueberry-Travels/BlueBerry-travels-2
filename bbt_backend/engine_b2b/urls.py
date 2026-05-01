from engine_meta import photo_views as meta_photo_views
from django.urls import path
from engine_b2b import views

app_name = 'engine_b2b'

urlpatterns = [
    # Profile and data consent
    path('profile/',                                    views.PartnerProfileView.as_view(),       name='profile'),
    path('profile/photo/', meta_photo_views.upload_partner_photo, name='upload_partner_photo'),
    path('profile/photo/delete/', meta_photo_views.delete_partner_photo, name='delete_partner_photo'),
    path('consent/',                                    views.DataConsentView.as_view(),           name='consent'),

    # Staff management
    path('staff/',                                      views.StaffListView.as_view(),             name='staff_list'),
    path('staff/<uuid:staff_id>/',                      views.StaffDetailView.as_view(),           name='staff_detail'),
    path('staff/<uuid:staff_id>/leaves/',               views.StaffLeaveView.as_view(),            name='staff_leaves'),
    path('staff/<uuid:staff_id>/salary/',               views.StaffSalaryView.as_view(),           name='staff_salary'),

    # Guest records
    path('guests/',                                     views.GuestRecordListView.as_view(),       name='guest_list'),
    path('guests/<uuid:record_id>/',                    views.GuestRecordDetailView.as_view(),     name='guest_detail'),

    # Rooms
    path('rooms/',                                      views.RoomListView.as_view(),              name='room_list'),
    path('rooms/<uuid:room_id>/',                       views.RoomDetailView.as_view(),            name='room_detail'),
    path('rooms/assign/',                               views.RoomAssignmentView.as_view(),        name='room_assign'),

    # Tasks
    path('tasks/',                                      views.TaskListView.as_view(),              name='task_list'),
    path('tasks/<uuid:task_id>/',                       views.TaskDetailView.as_view(),            name='task_detail'),

    # Vehicles
    path('vehicles/',                                   views.VehicleListView.as_view(),           name='vehicle_list'),
    path('vehicles/<uuid:vehicle_id>/',                 views.VehicleDetailView.as_view(),         name='vehicle_detail'),
    path('vehicles/<uuid:vehicle_id>/drivers/',         views.VehicleDriverLinkView.as_view(),     name='vehicle_drivers'),
    path('trips/',                                      views.TripRecordView.as_view(),            name='trip_list'),

    # Commodities and gear
    path('commodities/',                                views.CommodityListView.as_view(),         name='commodity_list'),
    path('commodities/<uuid:commodity_id>/',            views.CommodityDetailView.as_view(),       name='commodity_detail'),
    path('commodities/assign/',                         views.CommodityAssignmentView.as_view(),   name='commodity_assign'),
    path('commodities/return/<uuid:assignment_id>/',    views.CommodityAssignmentView.as_view(),   name='commodity_return'),

    # Closure dates
    path('closures/',                                   views.ClosureDateView.as_view(),           name='closures'),

    # Activity certifications
    path('certifications/',                             views.ActivityCertificationView.as_view(), name='certifications'),

    # Service assignments (incoming from bookings)
    path('assignments/',                                views.ServiceAssignmentView.as_view(),     name='assignment_list'),
    path('assignments/<uuid:assignment_id>/',           views.ServiceAssignmentView.as_view(),     name='assignment_detail'),
    path('notifications/',                              views.PartnerNotificationView.as_view(),   name='partner_notifications'),

    # Partner booking confirmation
    path('bookings/<uuid:line_item_id>/confirm/', views.PartnerConfirmView.as_view(), name='partner_confirm'),
    path('bookings/<uuid:line_item_id>/reject/',  views.PartnerRejectView.as_view(),  name='partner_reject'),
    path('bookings/pending/',                     views.PartnerPendingView.as_view(),  name='partner_pending'),

]