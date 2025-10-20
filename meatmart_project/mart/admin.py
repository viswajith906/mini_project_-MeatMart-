from django.contrib import admin
from .models import User, Shop, Order, Feedback
from .models import Delivery 

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('username', 'email')

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'location', 'phone_number', 'created_at')
    list_filter = ('location', 'created_at')
    search_fields = ('name', 'user__username', 'location')

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('order', 'shop', 'customer', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('customer__username', 'shop__name', 'order__id')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'shop', 'customer', 'quantity', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'shop')
    search_fields = ('shop__name', 'customer__username', 'id')

@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'delivery_status', 'delivery_date')
    list_filter = ('delivery_status',)
    search_fields = ('order__id', 'delivery_address')