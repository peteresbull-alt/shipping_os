import random
import string
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from .managers import CustomUserManager


# ============================================
# CUSTOM USER MODEL
# ============================================

class CustomUser(AbstractBaseUser, PermissionsMixin):
    """NordFracht Express Delivery customer / staff account."""

    ACCOUNT_STATUS = [
        ('PENDING_VERIFICATION', 'Pending Verification'),
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),
    ]

    CUSTOMER_TYPE = [
        ('INDIVIDUAL', 'Individual'),
        ('BUSINESS', 'Business'),
    ]

    email = models.EmailField('email address', unique=True, db_index=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=30, blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPE, default='INDIVIDUAL')

    customer_id = models.CharField(max_length=20, unique=True, blank=True, null=True, db_index=True)

    # Default location (used to prefill "ship from")
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True, default='United States')
    postal_code = models.CharField(max_length=20, blank=True)

    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)

    account_status = models.CharField(max_length=30, choices=ACCOUNT_STATUS, default='PENDING_VERIFICATION')
    is_verified = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_activity = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
        ordering = ['-date_joined']

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if not self.customer_id:
            self.customer_id = self._generate_customer_id()
        super().save(*args, **kwargs)

    def _generate_customer_id(self):
        code = 'FX' + ''.join(random.choices(string.digits, k=8))
        while CustomUser.objects.filter(customer_id=code).exists():
            code = 'FX' + ''.join(random.choices(string.digits, k=8))
        return code

    @property
    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    @property
    def initials(self):
        a = self.first_name[:1].upper() if self.first_name else ''
        b = self.last_name[:1].upper() if self.last_name else ''
        return (a + b) or self.email[:2].upper()


# ============================================
# ADDRESS BOOK
# ============================================

class Address(models.Model):
    """Saved sender / recipient address for fast checkout."""

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='addresses')

    label = models.CharField(max_length=100, help_text='e.g. Home, Warehouse, HQ')
    contact_name = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200, blank=True)
    phone_number = models.CharField(max_length=30)
    email = models.EmailField(blank=True)

    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='United States')
    postal_code = models.CharField(max_length=20, blank=True)

    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Address'
        verbose_name_plural = 'Addresses'
        ordering = ['-is_default', 'label']

    def __str__(self):
        return f'{self.label} - {self.contact_name}'

    @property
    def one_line(self):
        parts = [self.address_line1, self.address_line2, self.city, self.state, self.postal_code, self.country]
        return ', '.join(p for p in parts if p)


# ============================================
# SHIPMENT
# ============================================

class Shipment(models.Model):
    """A booked shipment / parcel moving through the NordFracht Express Delivery network."""

    SERVICE_TYPES = [
        ('EXPRESS', 'Express Air'),
        ('STANDARD', 'Standard Freight'),
        ('SEA', 'Ocean Freight'),
        ('ROAD', 'Road Freight'),
    ]

    PACKAGE_TYPES = [
        ('PARCEL', 'Parcel'),
        ('DOCUMENT', 'Document'),
        ('PALLET', 'Pallet'),
        ('CONTAINER', 'Container'),
        ('FREIGHT', 'Bulk Freight'),
    ]

    STATUS_CHOICES = [
        ('BOOKED', 'Booked'),
        ('PICKED_UP', 'Picked Up'),
        ('IN_TRANSIT', 'In Transit'),
        ('CUSTOMS', 'Customs Clearance'),
        ('OUT_FOR_DELIVERY', 'Out for Delivery'),
        ('DELIVERED', 'Delivered'),
        ('DELAYED', 'Delayed'),
        ('CANCELLED', 'Cancelled'),
    ]

    PAYMENT_STATUS = [
        ('UNPAID', 'Unpaid'),
        ('PAID', 'Paid'),
        ('REFUNDED', 'Refunded'),
    ]

    tracking_number = models.CharField(max_length=20, unique=True, db_index=True)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='shipments')

    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES, default='STANDARD')
    package_type = models.CharField(max_length=20, choices=PACKAGE_TYPES, default='PARCEL')
    description = models.CharField(max_length=255, blank=True)

    weight_kg = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    length_cm = models.DecimalField(max_digits=6, decimal_places=1, default=Decimal('10.0'))
    width_cm = models.DecimalField(max_digits=6, decimal_places=1, default=Decimal('10.0'))
    height_cm = models.DecimalField(max_digits=6, decimal_places=1, default=Decimal('10.0'))
    declared_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    is_insured = models.BooleanField(default=False)
    is_fragile = models.BooleanField(default=False)

    # Sender (denormalized so a shipment survives an address book edit/delete)
    sender_name = models.CharField(max_length=200)
    sender_phone = models.CharField(max_length=30)
    sender_address = models.CharField(max_length=255)
    sender_city = models.CharField(max_length=100)
    sender_country = models.CharField(max_length=100)
    sender_postal_code = models.CharField(max_length=20, blank=True)

    # Recipient
    recipient_name = models.CharField(max_length=200)
    recipient_phone = models.CharField(max_length=30)
    recipient_address = models.CharField(max_length=255)
    recipient_city = models.CharField(max_length=100)
    recipient_country = models.CharField(max_length=100)
    recipient_postal_code = models.CharField(max_length=20, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='BOOKED')
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='UNPAID')

    current_location = models.CharField(max_length=200, blank=True)
    estimated_delivery = models.DateField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Shipment'
        verbose_name_plural = 'Shipments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tracking_number']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f'{self.tracking_number} ({self.get_status_display()})'

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            self.tracking_number = self._generate_tracking_number()
        super().save(*args, **kwargs)

    def _generate_tracking_number(self):
        code = 'FX' + ''.join(random.choices(string.digits, k=9))
        while Shipment.objects.filter(tracking_number=code).exists():
            code = 'FX' + ''.join(random.choices(string.digits, k=9))
        return code

    @property
    def volumetric_weight_kg(self):
        return (self.length_cm * self.width_cm * self.height_cm) / Decimal('5000')

    @property
    def progress_percent(self):
        order = ['BOOKED', 'PICKED_UP', 'IN_TRANSIT', 'CUSTOMS', 'OUT_FOR_DELIVERY', 'DELIVERED']
        if self.status not in order:
            return 100 if self.status == 'CANCELLED' else 0
        return int((order.index(self.status) + 1) / len(order) * 100)

    @property
    def is_active(self):
        return self.status not in ('DELIVERED', 'CANCELLED')

    def sync_from_latest_event(self):
        """Recompute status/current_location/delivered_at from whichever
        TrackingEvent is chronologically latest right now. Called after any
        event is created, edited or deleted, so admin corrections (fixing a
        typo'd location, deleting a bad entry, editing a timestamp) always
        propagate correctly rather than only the most-recently-saved event
        being trusted."""
        latest = self.events.order_by('-timestamp', '-id').first()
        if not latest:
            return
        self.status = latest.status
        self.current_location = latest.location
        if latest.status == 'DELIVERED':
            if not self.delivered_at:
                self.delivered_at = latest.timestamp
        else:
            self.delivered_at = None
        self.save(update_fields=['status', 'current_location', 'delivered_at', 'updated_at'])

    @property
    def route_points(self):
        """Origin -> distinct waypoints from the tracking history -> destination,
        each flagged reached/current, for the visual route diagram. Built from
        real event locations rather than geocoding, so it's a sequence diagram
        rather than a literal map."""
        origin = f'{self.sender_city}, {self.sender_country}'
        destination = f'{self.recipient_city}, {self.recipient_country}'

        labels = [origin]
        for event in self.events.order_by('timestamp'):
            loc = (event.location or '').strip()
            if loc and loc != labels[-1] and loc != destination:
                labels.append(loc)
        labels.append(destination)

        is_delivered = self.status == 'DELIVERED'
        is_cancelled = self.status == 'CANCELLED'
        reached_count = len(labels) if is_delivered else len(labels) - 1

        points = []
        for i, label in enumerate(labels):
            if i == 0:
                kind = 'origin'
            elif i == len(labels) - 1:
                kind = 'destination'
            else:
                kind = 'waypoint'
            points.append({
                'label': label,
                'kind': kind,
                'reached': i < reached_count,
                'current': (not is_cancelled) and (not is_delivered) and i == reached_count - 1,
            })
        return points


# ============================================
# TRACKING EVENT
# ============================================

class TrackingEvent(models.Model):
    """A single checkpoint in a shipment's journey.

    Saving a new event is how a shipment's status and location actually get
    updated — see `save()` below. This keeps every place that posts an update
    (the booking flow, cancellation, staff in the admin) consistent instead of
    each having to remember to touch the Shipment fields separately.
    """

    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='events')
    status = models.CharField(max_length=20, choices=Shipment.STATUS_CHOICES)
    location = models.CharField(max_length=200)
    note = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Tracking Event'
        verbose_name_plural = 'Tracking Events'
        ordering = ['-timestamp', '-id']

    def __str__(self):
        return f'{self.shipment.tracking_number} - {self.get_status_display()}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.shipment.sync_from_latest_event()


# ============================================
# NOTIFICATION
# ============================================

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('SHIPMENT', 'Shipment'),
        ('DELIVERY', 'Delivery'),
        ('BILLING', 'Billing'),
        ('SECURITY', 'Security'),
        ('SYSTEM', 'System'),
        ('PROMOTIONAL', 'Promotional'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='SYSTEM')
    title = models.CharField(max_length=200)
    message = models.TextField()
    action_url = models.CharField(max_length=500, blank=True)

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    shipment = models.ForeignKey(Shipment, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', 'is_read', '-created_at'])]

    def __str__(self):
        return f'{self.user.email} - {self.title}'


# ============================================
# SUPPORT TICKET
# ============================================

class SupportTicket(models.Model):
    CATEGORIES = [
        ('SHIPMENT', 'Shipment Issue'),
        ('BILLING', 'Billing'),
        ('DAMAGE_CLAIM', 'Damage / Loss Claim'),
        ('CUSTOMS', 'Customs'),
        ('TECHNICAL', 'Technical Issue'),
        ('GENERAL', 'General Inquiry'),
    ]

    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('WAITING_CUSTOMER', 'Waiting for Customer'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    ]

    PRIORITY = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]

    ticket_number = models.CharField(max_length=20, unique=True, blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='support_tickets')
    shipment = models.ForeignKey(Shipment, on_delete=models.SET_NULL, null=True, blank=True)

    category = models.CharField(max_length=20, choices=CATEGORIES, default='GENERAL')
    priority = models.CharField(max_length=10, choices=PRIORITY, default='MEDIUM')

    subject = models.CharField(max_length=200)
    description = models.TextField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Support Ticket'
        verbose_name_plural = 'Support Tickets'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.ticket_number} - {self.subject}'

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = self._generate_ticket_number()
        super().save(*args, **kwargs)

    def _generate_ticket_number(self):
        code = 'TKT-' + ''.join(random.choices(string.digits, k=7))
        while SupportTicket.objects.filter(ticket_number=code).exists():
            code = 'TKT-' + ''.join(random.choices(string.digits, k=7))
        return code


# ============================================
# CONTACT MESSAGE (public "Contact us" form)
# ============================================

class ContactMessage(models.Model):
    TOPICS = [
        ('SALES', 'Sales & Quotes'),
        ('SUPPORT', 'Existing Shipment Support'),
        ('PARTNERSHIP', 'Partnerships'),
        ('PRESS', 'Press & Media'),
        ('OTHER', 'Other'),
    ]

    name = models.CharField(max_length=200)
    email = models.EmailField()
    company_name = models.CharField(max_length=200, blank=True)
    topic = models.CharField(max_length=20, choices=TOPICS, default='SALES')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} — {self.get_topic_display()}'


# ============================================
# NEWSLETTER SUBSCRIBER (public "Stay in the loop" form)
# ============================================

class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Newsletter Subscriber'
        verbose_name_plural = 'Newsletter Subscribers'
        ordering = ['-created_at']

    def __str__(self):
        return self.email
