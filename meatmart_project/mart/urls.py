from django.urls import path
from . import views  # This is the correct way to import
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('customer/login/', views.customer_login, name='customer_login'),
    path('shop/login/', views.shop_login, name='shop_login'),
    path('customer/dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('shop/dashboard/', views.shop_dashboard, name='shop_dashboard'),
    path('logout/', views.logout, name='logout'),
    path('register-shop/', views.register_shop, name='register_shop'),
    path('shop/<int:shop_id>/', views.shop_detail, name='shop_detail'),  # ✅ New
    path('shop/<int:shop_id>/order/', views.place_order, name='place_order'),  # ✅ New
    path('orders/', views.orders, name='orders'),
    path('order/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('delivery/', views.delivery, name='delivery'),
    path('order/<int:order_id>/deliver/', views.deliver_order, name='deliver_order'),
    path('order/<int:order_id>/feedback/', views.submit_feedback, name='submit_feedback'),
    # mart/urls.py (add)
    path('shop/delivery/', views.shop_delivery, name='shop_delivery'),
    path('shop/notifications/', views.shop_notifications, name='shop_notifications'),
    path('shop/feedbacks/', views.shop_feedbacks, name='shop_feedbacks'),
    path('shop/order/<int:order_id>/mark-delivered/', views.shop_mark_delivered, name='shop_mark_delivered'),
    path('api/shop_unread_orders/', views.api_shop_unread_orders, name='api_shop_unread_orders'),
    path('api/mark_orders_seen/', views.mark_orders_seen, name='api_mark_orders_seen'),




]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)