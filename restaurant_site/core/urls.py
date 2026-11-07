from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import AdminAuthenticationForm, KitchenAuthenticationForm

urlpatterns = [
    path('', views.landing, name='landing'),
    path('t/<uuid:token>/', views.scan_table, name='scan_table'),

    path('table/<int:table_id>/menu/', views.menu_view, name='menu'),
    path('table/<int:table_id>/cart/', views.cart_view, name='cart'),
    path('table/<int:table_id>/cart/add/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('table/<int:table_id>/cart/<int:item_id>/<str:action>/', views.update_cart, name='update_cart'),
    path('table/<int:table_id>/order/place/', views.place_order, name='place_order'),

    path('order/<int:order_id>/status/', views.order_status, name='order_status'),
    path('order/<int:order_id>/status/data/', views.order_status_data, name='order_status_data'),
    path('order/<int:order_id>/bill/request/', views.request_bill, name='request_bill'),
    path('order/<int:order_id>/bill/', views.bill_view, name='bill_view'),
    path('order/<int:order_id>/confirm-paid/', views.confirm_paid, name='confirm_paid'),


    path('staff/login/', auth_views.LoginView.as_view(template_name='core/staff_login.html'), name='staff_login'),
    path('admin/login/', auth_views.LoginView.as_view(template_name='core/staff_login.html', form_class=AdminAuthenticationForm, extra_context={'login_role': 'Admin'}), name='admin_login'),
    path('kitchen/login/', auth_views.LoginView.as_view(template_name='core/staff_login.html', form_class=KitchenAuthenticationForm, extra_context={'login_role': 'Kitchen'}), name='kitchen_login'),
    path('staff/logout/', auth_views.LogoutView.as_view(next_page='landing'), name='staff_logout'),
    path('staff/', views.staff_dashboard, name='staff_dashboard'),
    path('kitchen/', views.kitchen_dashboard, name='kitchen_dashboard'),
    path('manage/menu/', views.menu_management, name='menu_management'),
    path('manage/menu/add/', views.menu_item_add, name='menu_item_add'),
    path('manage/menu/<int:item_id>/edit/', views.menu_item_edit, name='menu_item_edit'),
    path('manage/menu/<int:item_id>/delete/', views.menu_item_delete, name='menu_item_delete'),
    path('staff/new-orders/', views.staff_new_orders, name='staff_new_orders'),
    path('staff/payment-requests/', views.staff_payment_requests, name='staff_payment_requests'),
    path('manage/notifications/', views.notification_settings, name='notification_settings'),
    path('manage/payment/', views.payment_settings, name='payment_settings'),
    path('staff/order/<int:order_id>/status/<str:status>/', views.staff_update_status, name='staff_update_status'),
    path('staff/order/<int:order_id>/mark-paid/', views.staff_mark_paid, name='staff_mark_paid'),
]
