from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .decorators import staff_required
from .forms import (
    AddressForm, AdminShipmentForm, ChangePasswordForm, ContactForm, NewsletterForm,
    ProfileForm, RegisterForm, SupportTicketForm, TrackingEventForm,
)
from .models import (
    Address, ContactMessage, CustomUser, NewsletterSubscriber, Notification,
    Shipment, SupportTicket, TrackingEvent,
)

# ============================================
# RATE CARD
# ============================================
SERVICE_BASE_RATE = {'EXPRESS': 28.00, 'STANDARD': 14.00, 'SEA': 9.00, 'ROAD': 11.00}
SERVICE_PER_KG = {'EXPRESS': 5.20, 'STANDARD': 2.60, 'SEA': 1.10, 'ROAD': 1.65}
SERVICE_ETA_DAYS = {'EXPRESS': 2, 'STANDARD': 5, 'SEA': 21, 'ROAD': 9}
INSURANCE_RATE = Decimal('0.015')  # 1.5% of declared value


def calculate_shipping_cost(service_type, weight_kg, length_cm, width_cm, height_cm, declared_value, is_insured):
    weight_kg = Decimal(weight_kg or 0)
    volumetric = (Decimal(length_cm or 10) * Decimal(width_cm or 10) * Decimal(height_cm or 10)) / Decimal('5000')
    chargeable = max(weight_kg, volumetric)

    base = Decimal(str(SERVICE_BASE_RATE.get(service_type, 14.00)))
    per_kg = Decimal(str(SERVICE_PER_KG.get(service_type, 2.60)))

    cost = base + (per_kg * chargeable)
    insurance_fee = Decimal('0.00')
    if is_insured and declared_value:
        insurance_fee = (Decimal(declared_value) * INSURANCE_RATE).quantize(Decimal('0.01'))
        cost += insurance_fee

    return cost.quantize(Decimal('0.01')), chargeable.quantize(Decimal('0.01')), insurance_fee


# ============================================
# LANDING / PUBLIC
# ============================================

FAQS = [
    ('How fast is Express Air delivery?', 'Most Express Air shipments arrive within 48 hours door-to-door, depending on origin and destination customs processing.'),
    ('Do you offer real-time tracking?', 'Yes — every shipment gets a tracking number with live checkpoint updates from pickup to final delivery, visible to you at every step.'),
    ('What happens if my package is delayed?', "We proactively flag delays on your dashboard and notify you immediately, with our support team on standby to help re-route or expedite."),
    ('Can I insure high-value cargo?', 'Yes, optional insurance is available at booking for a small percentage of the declared value, covering loss or damage in transit.'),
    ('Do you handle customs clearance?', 'Our in-house brokerage manages documentation and clearance for international shipments so your cargo keeps moving without delay.'),
    ('How is my shipping cost calculated?', "We price by service type plus chargeable weight — the greater of actual weight and volumetric weight (L x W x H / 5000). Optional insurance adds a small percentage of your declared value."),
    ('Can I ship internationally to any country?', 'We currently serve 150+ countries across air, ocean and road networks. If your destination isn’t listed at checkout, reach out to our team and we’ll confirm availability.'),
    ('What items can’t be shipped?', "Hazardous materials, illegal goods, and live animals are restricted on our network. Fragile and high-value items are welcome — just flag them at booking so we can handle them with care."),
    ('How do I pay for a shipment?', "Once you book a shipment, a 'Pay Now' action appears on the shipment detail page. Payment is confirmed instantly and your package moves to pickup."),
    ('Can I cancel a shipment after booking?', "Yes, shipments can be cancelled from the shipment detail page as long as they haven't yet been picked up by a courier."),
]


def landing_home(request):
    if request.user.is_authenticated:
        return redirect('admin_dashboard' if request.user.is_staff else 'dashboard')
    return render(request, 'landing/home.html', {'title': 'Home', 'faqs': FAQS[:5]})


def about_view(request):
    return render(request, 'pages/about.html', {'title': 'About Us'})


def services_view(request):
    return render(request, 'pages/services.html', {'title': 'Services'})


def how_it_works_view(request):
    return render(request, 'pages/how_it_works.html', {'title': 'How It Works'})


def faq_view(request):
    return render(request, 'pages/faq.html', {'title': 'FAQ', 'faqs': FAQS})


def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thanks for reaching out — we'll get back to you within one business day.")
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'pages/contact.html', {'title': 'Contact', 'form': form})


def newsletter_signup_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        form = NewsletterForm(request.POST)
        if form.is_valid():
            NewsletterSubscriber.objects.get_or_create(email=form.cleaned_data['email'])
        # Always show success, even for an existing subscriber or a bad email —
        # don't leak whether an address is already on the list.
        messages.success(request, "You're on the list — we'll keep you posted.")
    return redirect(request.META.get('HTTP_REFERER', 'landing_home'))


def track_view(request, tracking_number=None):
    tracking_number = (tracking_number or request.GET.get('t', '')).strip().upper()
    shipment = None
    events = []
    searched = bool(tracking_number)

    if tracking_number:
        shipment = Shipment.objects.filter(tracking_number=tracking_number).first()
        if shipment:
            events = shipment.events.all()
        else:
            messages.error(request, f'No shipment found with tracking number "{tracking_number}".')

    return render(request, 'track/track.html', {
        'title': 'Track Shipment',
        'shipment': shipment,
        'events': events,
        'tracking_number': tracking_number,
        'searched': searched,
    })


# ============================================
# AUTHENTICATION
# ============================================

def register_view(request):
    if request.user.is_authenticated:
        return redirect('admin_dashboard' if request.user.is_staff else 'dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Notification.objects.create(
                user=user,
                notification_type='SYSTEM',
                title='Welcome to Fracht Express',
                message='Your account has been created. Book your first shipment to get started.',
            )
            login(request, user)
            messages.success(request, f'Welcome aboard, {user.first_name}! Your account is ready.')
            return redirect('dashboard')
    else:
        form = RegisterForm()

    return render(request, 'auth/register.html', {'title': 'Create Account', 'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('admin_dashboard' if request.user.is_staff else 'dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next')
            if not next_url:
                next_url = 'admin_dashboard' if user.is_staff else 'dashboard'
            return redirect(next_url)
        messages.error(request, 'Invalid email or password.')

    return render(request, 'auth/login.html', {'title': 'Sign In'})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You've been signed out securely.")
    return redirect('landing_home')


# ============================================
# DASHBOARD
# ============================================

@login_required
def dashboard_view(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')

    shipments = request.user.shipments.all()
    active_shipments = shipments.exclude(status__in=['DELIVERED', 'CANCELLED'])
    delivered_shipments = shipments.filter(status='DELIVERED')

    total_spent = shipments.filter(payment_status='PAID').aggregate(total=Sum('shipping_cost'))['total'] or Decimal('0.00')

    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    recent_shipments_count = shipments.filter(created_at__gte=thirty_days_ago).count()

    context = {
        'title': 'Dashboard',
        'shipments': shipments[:5],
        'active_count': active_shipments.count(),
        'delivered_count': delivered_shipments.count(),
        'total_shipments': shipments.count(),
        'total_spent': total_spent,
        'recent_shipments_count': recent_shipments_count,
        'in_transit': shipments.filter(status__in=['PICKED_UP', 'IN_TRANSIT', 'CUSTOMS', 'OUT_FOR_DELIVERY']).count(),
        'recent_events': TrackingEvent.objects.filter(shipment__user=request.user).select_related('shipment')[:6],
    }
    return render(request, 'dashboard/dashboard.html', context)


# ============================================
# SHIPMENTS
# ============================================

@login_required
def shipment_list_view(request):
    shipments = request.user.shipments.all()

    status = request.GET.get('status', '')
    if status:
        shipments = shipments.filter(status=status)

    q = request.GET.get('q', '').strip()
    if q:
        shipments = shipments.filter(
            Q(tracking_number__icontains=q) | Q(recipient_name__icontains=q) | Q(recipient_city__icontains=q)
        )

    return render(request, 'shipments/shipment_list.html', {
        'title': 'My Shipments',
        'shipments': shipments,
        'status_choices': Shipment.STATUS_CHOICES,
        'selected_status': status,
        'query': q,
    })


@login_required
def shipment_detail_view(request, tracking_number):
    shipment = get_object_or_404(Shipment, tracking_number=tracking_number, user=request.user)
    return render(request, 'shipments/shipment_detail.html', {
        'title': f'Shipment {shipment.tracking_number}',
        'shipment': shipment,
        'events': shipment.events.all(),
    })


@login_required
def shipment_pay_view(request, tracking_number):
    shipment = get_object_or_404(Shipment, tracking_number=tracking_number, user=request.user)
    if request.method == 'POST' and shipment.payment_status == 'UNPAID':
        shipment.payment_status = 'PAID'
        shipment.save(update_fields=['payment_status'])
        Notification.objects.create(
            user=request.user,
            notification_type='BILLING',
            title='Payment received',
            message=f'Payment of ${shipment.shipping_cost} for shipment {shipment.tracking_number} was confirmed.',
            shipment=shipment,
        )
        messages.success(request, 'Payment confirmed. Your shipment will be picked up shortly.')
    return redirect('shipment_detail', tracking_number=shipment.tracking_number)


# ============================================
# ADMIN / STAFF — shipment management
# ============================================
# Only staff can create shipments or post status/location updates. Customers
# get a read-only view of their own shipments (plus payment) via the views
# above; everything below requires @staff_required.

@staff_required
def admin_dashboard_view(request):
    shipments = Shipment.objects.select_related('user').all()
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)

    total_revenue = shipments.filter(payment_status='PAID').aggregate(total=Sum('shipping_cost'))['total'] or Decimal('0.00')

    context = {
        'title': 'Admin Dashboard',
        'total_shipments': shipments.count(),
        'in_transit': shipments.filter(status__in=['PICKED_UP', 'IN_TRANSIT', 'CUSTOMS', 'OUT_FOR_DELIVERY']).count(),
        'delivered_count': shipments.filter(status='DELIVERED').count(),
        'unpaid_count': shipments.filter(payment_status='UNPAID').count(),
        'total_revenue': total_revenue,
        'new_this_month': shipments.filter(created_at__gte=thirty_days_ago).count(),
        'open_tickets': SupportTicket.objects.exclude(status__in=['RESOLVED', 'CLOSED']).count(),
        'new_contact_messages': ContactMessage.objects.filter(is_resolved=False).count(),
        'total_customers': CustomUser.objects.filter(is_staff=False).count(),
        'recent_shipments': shipments[:8],
    }
    return render(request, 'manage/dashboard.html', context)


@staff_required
def admin_shipment_list_view(request):
    shipments = Shipment.objects.select_related('user').all()

    status = request.GET.get('status', '')
    if status:
        shipments = shipments.filter(status=status)

    payment = request.GET.get('payment', '')
    if payment:
        shipments = shipments.filter(payment_status=payment)

    q = request.GET.get('q', '').strip()
    if q:
        shipments = shipments.filter(
            Q(tracking_number__icontains=q) | Q(recipient_name__icontains=q) |
            Q(user__email__icontains=q) | Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q)
        )

    return render(request, 'manage/shipment_list.html', {
        'title': 'All Shipments',
        'shipments': shipments,
        'status_choices': Shipment.STATUS_CHOICES,
        'selected_status': status,
        'selected_payment': payment,
        'query': q,
    })


@staff_required
def admin_shipment_detail_view(request, tracking_number):
    shipment = get_object_or_404(Shipment.objects.select_related('user'), tracking_number=tracking_number)

    if request.method == 'POST':
        event_form = TrackingEventForm(request.POST)
        if event_form.is_valid():
            event = event_form.save(commit=False)
            event.shipment = shipment
            event.save()  # syncs shipment.status/current_location automatically
            Notification.objects.create(
                user=shipment.user,
                notification_type='DELIVERY' if event.status == 'DELIVERED' else 'SHIPMENT',
                title=f'Shipment {event.get_status_display().lower()}',
                message=f'Your shipment {shipment.tracking_number} is now "{event.get_status_display()}" ({event.location}).',
                shipment=shipment,
                action_url=f'/shipments/{shipment.tracking_number}/',
            )
            messages.success(request, f'Shipment {shipment.tracking_number} updated to "{event.get_status_display()}".')
            return redirect('admin_shipment_detail', tracking_number=shipment.tracking_number)
    else:
        event_form = TrackingEventForm(initial={'status': shipment.status, 'location': shipment.current_location})

    return render(request, 'manage/shipment_detail.html', {
        'title': shipment.tracking_number,
        'shipment': shipment,
        'events': shipment.events.all(),
        'event_form': event_form,
    })


@staff_required
def admin_shipment_create_view(request):
    if request.method == 'POST':
        form = AdminShipmentForm(request.POST)
        if form.is_valid():
            shipment = form.save(commit=False)
            shipment.user = form.cleaned_data['customer']

            cost, chargeable_weight, insurance_fee = calculate_shipping_cost(
                shipment.service_type, shipment.weight_kg, shipment.length_cm,
                shipment.width_cm, shipment.height_cm, shipment.declared_value, shipment.is_insured,
            )
            shipment.shipping_cost = cost
            shipment.current_location = f'{shipment.sender_city}, {shipment.sender_country}'
            eta_days = SERVICE_ETA_DAYS.get(shipment.service_type, 5)
            shipment.estimated_delivery = (timezone.now() + timezone.timedelta(days=eta_days)).date()
            shipment.save()

            TrackingEvent.objects.create(
                shipment=shipment,
                status='BOOKED',
                location=shipment.current_location,
                note='Shipment booked and awaiting pickup.',
            )
            Notification.objects.create(
                user=shipment.user,
                notification_type='SHIPMENT',
                title='Shipment booked',
                message=f'A new shipment {shipment.tracking_number} to {shipment.recipient_city} has been booked for you.',
                shipment=shipment,
                action_url=f'/shipments/{shipment.tracking_number}/',
            )
            messages.success(request, f'Shipment {shipment.tracking_number} created for {shipment.user.get_full_name}.')
            return redirect('admin_shipment_detail', tracking_number=shipment.tracking_number)
    else:
        form = AdminShipmentForm()

    return render(request, 'manage/shipment_create.html', {
        'title': 'Create Shipment',
        'form': form,
        'rate_card': {
            'base': SERVICE_BASE_RATE, 'per_kg': SERVICE_PER_KG, 'eta': SERVICE_ETA_DAYS,
            'insurance_rate': float(INSURANCE_RATE) * 100,
        },
    })


# ============================================
# ADDRESS BOOK
# ============================================

@login_required
def address_list_view(request):
    return render(request, 'addresses/address_list.html', {
        'title': 'Saved Addresses',
        'addresses': request.user.addresses.all(),
    })


@login_required
def address_add_view(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            if address.is_default:
                request.user.addresses.update(is_default=False)
            address.save()
            messages.success(request, 'Address saved.')
            return redirect('address_list')
    else:
        form = AddressForm()

    return render(request, 'addresses/address_form.html', {'title': 'Add Address', 'form': form, 'is_edit': False})


@login_required
def address_edit_view(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            address = form.save(commit=False)
            if address.is_default:
                request.user.addresses.exclude(id=address.id).update(is_default=False)
            address.save()
            messages.success(request, 'Address updated.')
            return redirect('address_list')
    else:
        form = AddressForm(instance=address)

    return render(request, 'addresses/address_form.html', {'title': 'Edit Address', 'form': form, 'is_edit': True, 'address': address})


@login_required
def address_delete_view(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Address removed.')
        return redirect('address_list')
    return render(request, 'addresses/address_delete.html', {'title': 'Delete Address', 'address': address})


# ============================================
# SUPPORT TICKETS
# ============================================

@login_required
def support_ticket_list_view(request):
    return render(request, 'support/ticket_list.html', {
        'title': 'Support Tickets',
        'tickets': request.user.support_tickets.all(),
    })


@login_required
def support_ticket_detail_view(request, ticket_number):
    ticket = get_object_or_404(SupportTicket, ticket_number=ticket_number, user=request.user)
    return render(request, 'support/ticket_detail.html', {'title': ticket.ticket_number, 'ticket': ticket})


@login_required
def support_ticket_create_view(request):
    if request.method == 'POST':
        form = SupportTicketForm(request.POST, user=request.user)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()
            messages.success(request, f'Ticket {ticket.ticket_number} created. Our team will respond shortly.')
            return redirect('support_ticket_detail', ticket_number=ticket.ticket_number)
    else:
        form = SupportTicketForm(user=request.user, initial={'shipment': request.GET.get('shipment')})

    return render(request, 'support/ticket_create.html', {'title': 'New Support Ticket', 'form': form})


# ============================================
# NOTIFICATIONS
# ============================================

@login_required
def notification_list_view(request):
    return render(request, 'notifications/notification_list.html', {
        'title': 'Notifications',
        'notifications': request.user.notifications.all(),
    })


@login_required
def notification_mark_read_view(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    return redirect(notification.action_url or 'notification_list')


@login_required
def notification_mark_all_read_view(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    messages.success(request, 'All notifications marked as read.')
    return redirect('notification_list')


# ============================================
# PROFILE
# ============================================

@login_required
def profile_view(request):
    return render(request, 'profile/profile.html', {'title': 'Profile'})


@login_required
def profile_edit_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'profile/profile_edit.html', {'title': 'Edit Profile', 'form': form})


@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Password changed successfully.')
            return redirect('profile')
    else:
        form = ChangePasswordForm(request.user)

    return render(request, 'profile/change_password.html', {'title': 'Change Password', 'form': form})
