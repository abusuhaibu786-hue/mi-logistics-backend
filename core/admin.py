from django.contrib import admin

from .models import Customer, Feedback, Notification, Shipment, Staff, TrackingEvent


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'phone', 'city', 'status', 'join_date']
    list_filter = ['status', 'city']
    search_fields = ['code', 'name', 'email', 'phone']
    readonly_fields = ['code']


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'role', 'department', 'status', 'rating']
    list_filter = ['status', 'department']
    search_fields = ['code', 'name', 'email', 'phone']
    readonly_fields = ['code']


class TrackingEventInline(admin.TabularInline):
    model = TrackingEvent
    extra = 1


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ['tracking_number', 'customer', 'destination', 'status', 'priority', 'amount', 'booked_date']
    list_filter = ['status', 'priority']
    search_fields = ['tracking_number', 'code', 'customer__name', 'receiver_name']
    readonly_fields = ['code', 'tracking_number']
    inlines = [TrackingEventInline]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'is_read', 'created_at']
    list_filter = ['is_read']


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'mobile', 'created_at']
    search_fields = ['name', 'email', 'mobile']
    readonly_fields = ['created_at']
