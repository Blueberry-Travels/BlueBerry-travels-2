from django.urls import path
from engine_b2c import (
    views, booking_views, collab_views,
    notification_views,
)
from engine_b2c import views, booking_views, collab_views, notification_views, pdf_views, pdf_views

app_name = 'engine_b2c'

urlpatterns = [
    # Discovery
    path('regions/',                        views.list_regions,                      name='regions'),
    path('activities/',                     views.list_activities,                   name='activities'),
    path('stays/',                          views.get_stays,                         name='stays'),
    path('events/',                         booking_views.get_events,                name='events'),
    path('transport/buses/',                views.search_buses,                      name='search_buses'),
    path('transport/trains/',               views.search_trains,                     name='search_trains'),
    path('packages/',                       views.list_packages,                     name='packages'),
    path('misc-services/',                  views.list_misc_services,                name='misc_services'),


    # Itinerary
    path('itinerary/build/',                views.build_itinerary,                   name='build_itinerary'),

    # Bookings
    path('bookings/',                       booking_views.create_booking,            name='create_booking'),
    path('bookings/history/',               booking_views.booking_list,              name='booking_list'),
    path('bookings/<uuid:booking_id>/',     booking_views.booking_detail,            name='booking_detail'),
    path('bookings/<uuid:booking_id>/verify/',   booking_views.verify_payment,       name='verify_payment'),
    path('bookings/<uuid:booking_id>/fillers/',  booking_views.update_fillers,       name='update_fillers'),
    path('bookings/<uuid:booking_id>/noc/<uuid:line_item_id>/',
                                            booking_views.accept_noc,                name='accept_noc'),

    # Trip Buffer
    path('buffer/<uuid:booking_id>/fund/',    notification_views.fund_buffer,          name='fund_buffer'),
    path('buffer/<uuid:booking_id>/verify/',  notification_views.verify_buffer_payment,name='verify_buffer'),

    # Advance payments (Booking.com hotels)
    path('advance/<uuid:booking_id>/request/',
                                            notification_views.create_advance_request,name='advance_request'),
    path('advance/<uuid:booking_id>/pay/<uuid:advance_id>/',
                                            notification_views.pay_advance,           name='advance_pay'),
    path('advance/<uuid:booking_id>/verify/<uuid:advance_id>/',
                                            notification_views.verify_advance_payment,name='advance_verify'),
    path('advance/<uuid:booking_id>/forward/<uuid:advance_id>/',
                                            notification_views.mark_advance_forwarded,name='advance_forward'),

    # Notifications
    path('notifications/',                  notification_views.notification_list,     name='notification_list'),
    path('notifications/unread-count/',     notification_views.unread_count,          name='unread_count'),
    path('notifications/<uuid:notification_id>/read/',
                                            notification_views.mark_read,             name='mark_read'),
    path('notifications/read-all/',         notification_views.mark_all_read,         name='mark_all_read'),

    # Collab
    path('collab/',                         collab_views.my_groups,                  name='collab_list'),
    path('collab/create/',                  collab_views.create_group,               name='collab_create'),
    path('collab/discover/',                collab_views.discover_groups,            name='collab_discover'),
    path('collab/<uuid:group_id>/',         collab_views.group_detail,               name='collab_detail'),
    path('collab/<uuid:group_id>/respond/', collab_views.respond_to_invite,          name='collab_respond'),
    path('collab/<uuid:group_id>/invite/',  collab_views.invite_member,              name='collab_invite'),
    path('collab/<uuid:group_id>/join/',    collab_views.request_to_join,            name='collab_join'),
    path('collab/<uuid:group_id>/messages/',collab_views.chat_history,              name='collab_messages'),

    # AI Coordinator
    path('coordinator/status/',   booking_views.coordinator_status,  name='coordinator_status'),
    path('coordinator/message/',  booking_views.coordinator_message, name='coordinator_message'),

    # Voucher validation (pre-apply check)
    path('vouchers/validate/',                          booking_views.validate_voucher,        name='voucher_validate'),

    # Vouchers
    path('bookings/<uuid:booking_id>/voucher/apply/',   booking_views.apply_voucher,           name='voucher_apply'),
    path('bookings/<uuid:booking_id>/voucher/remove/',  booking_views.remove_voucher,          name='voucher_remove'),
    # Customer service tickets
    path('bookings/<uuid:booking_id>/tickets/',         pdf_views.download_customer_tickets,   name='customer_tickets'),

    # PDF downloads
    path('bookings/<uuid:booking_id>/pdf/',
                                        pdf_views.download_itinerary,     name='download_itinerary'),
    path('bookings/<uuid:booking_id>/pdf/email/',
                                        pdf_views.trigger_pdf_email,      name='trigger_pdf_email'),
]