from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Address, ContactMessage, CustomUser, NewsletterSubscriber, Notification,
    Shipment, SupportTicket, TrackingEvent,
)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'get_full_name', 'customer_id', 'account_status', 'is_verified', 'is_staff', 'date_joined')
    list_filter = ('account_status', 'is_verified', 'customer_type', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name', 'customer_id')
    ordering = ('-date_joined',)
    readonly_fields = ('customer_id', 'date_joined', 'last_activity')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number', 'company_name', 'customer_type', 'profile_image')}),
        ('Address', {'fields': ('address_line1', 'address_line2', 'city', 'state', 'country', 'postal_code')}),
        ('Status', {'fields': ('customer_id', 'account_status', 'is_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'last_activity')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )


class TrackingEventInline(admin.TabularInline):
    model = TrackingEvent
    extra = 1


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'user', 'service_type', 'status', 'payment_status', 'shipping_cost', 'created_at')
    list_filter = ('status', 'service_type', 'payment_status')
    search_fields = ('tracking_number', 'user__email', 'recipient_name', 'sender_name')
    inlines = [TrackingEventInline]
    readonly_fields = ('tracking_number', 'created_at', 'updated_at')


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('label', 'contact_name', 'user', 'city', 'country', 'is_default')
    search_fields = ('label', 'contact_name', 'user__email')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'subject', 'user', 'category', 'status', 'priority', 'created_at')
    list_filter = ('status', 'category', 'priority')
    search_fields = ('ticket_number', 'subject', 'user__email')


@admin.register(TrackingEvent)
class TrackingEventAdmin(admin.ModelAdmin):
    list_display = ('shipment', 'status', 'location', 'timestamp')
    list_filter = ('status',)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'topic', 'is_resolved', 'created_at')
    list_filter = ('topic', 'is_resolved')
    search_fields = ('name', 'email', 'message')


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('email',)
