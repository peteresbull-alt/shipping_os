from django.urls import path

from app import views

urlpatterns = [
    # ============================================
    # LANDING / PUBLIC
    # ============================================
    path('', views.landing_home, name='landing_home'),
    path('about/', views.about_view, name='about'),
    path('services/', views.services_view, name='services'),
    path('how-it-works/', views.how_it_works_view, name='how_it_works'),
    path('faq/', views.faq_view, name='faq'),
    path('contact/', views.contact_view, name='contact'),
    path('newsletter/subscribe/', views.newsletter_signup_view, name='newsletter_signup'),
    path('track/', views.track_view, name='track'),
    path('track/<str:tracking_number>/', views.track_view, name='track_result'),

    # ============================================
    # AUTHENTICATION
    # ============================================
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # ============================================
    # DASHBOARD
    # ============================================
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # ============================================
    # SHIPMENTS (customer — read-only + payment)
    # ============================================
    path('shipments/', views.shipment_list_view, name='shipment_list'),
    path('shipments/<str:tracking_number>/', views.shipment_detail_view, name='shipment_detail'),
    path('shipments/<str:tracking_number>/pay/', views.shipment_pay_view, name='shipment_pay'),

    # ============================================
    # ADMIN / STAFF — shipment management
    # ============================================
    path('manage/', views.admin_dashboard_view, name='admin_dashboard'),
    path('manage/shipments/', views.admin_shipment_list_view, name='admin_shipment_list'),
    path('manage/shipments/new/', views.admin_shipment_create_view, name='admin_shipment_create'),
    path('manage/shipments/<str:tracking_number>/', views.admin_shipment_detail_view, name='admin_shipment_detail'),

    # ============================================
    # ADDRESS BOOK
    # ============================================
    path('addresses/', views.address_list_view, name='address_list'),
    path('addresses/add/', views.address_add_view, name='address_add'),
    path('addresses/<int:address_id>/edit/', views.address_edit_view, name='address_edit'),
    path('addresses/<int:address_id>/delete/', views.address_delete_view, name='address_delete'),

    # ============================================
    # SUPPORT TICKETS
    # ============================================
    path('support/', views.support_ticket_list_view, name='support_ticket_list'),
    path('support/create/', views.support_ticket_create_view, name='support_ticket_create'),
    path('support/<str:ticket_number>/', views.support_ticket_detail_view, name='support_ticket_detail'),

    # ============================================
    # NOTIFICATIONS
    # ============================================
    path('notifications/', views.notification_list_view, name='notification_list'),
    path('notifications/<int:notification_id>/mark-read/', views.notification_mark_read_view, name='notification_mark_read'),
    path('notifications/mark-all-read/', views.notification_mark_all_read_view, name='notification_mark_all_read'),

    # ============================================
    # PROFILE
    # ============================================
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('profile/change-password/', views.change_password_view, name='change_password'),
]
