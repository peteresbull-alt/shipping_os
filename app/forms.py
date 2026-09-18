from django import forms
from django.contrib.auth.forms import SetPasswordForm

from .models import Address, ContactMessage, CustomUser, NewsletterSubscriber, Shipment, SupportTicket, TrackingEvent

INPUT = (
    'w-full rounded-xl bg-white/5 border border-white/10 px-4 py-3 text-sm text-white '
    'placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-amber-500/40 '
    'focus:border-amber-500/60 transition-all'
)
SELECT = INPUT + ' appearance-none'
TEXTAREA = INPUT + ' resize-none'
CHECKBOX = 'h-4 w-4 rounded border-white/20 bg-white/5 text-amber-500 focus:ring-amber-500/40'


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': INPUT, 'placeholder': 'Create a password'}),
        min_length=8,
    )
    password2 = forms.CharField(
        label='Confirm password',
        widget=forms.PasswordInput(attrs={'class': INPUT, 'placeholder': 'Confirm your password'}),
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'company_name', 'customer_type']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': INPUT, 'placeholder': 'you@company.com'}),
            'phone_number': forms.TextInput(attrs={'class': INPUT, 'placeholder': '+1 (555) 000-0000'}),
            'company_name': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Company name (optional)'}),
            'customer_type': forms.Select(attrs={'class': SELECT}),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get('password1'), cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Passwords do not match.')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            'label', 'contact_name', 'company_name', 'phone_number', 'email',
            'address_line1', 'address_line2', 'city', 'state', 'country', 'postal_code', 'is_default',
        ]
        widgets = {
            'label': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'e.g. Home, Warehouse'}),
            'contact_name': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Full name'}),
            'company_name': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Company (optional)'}),
            'phone_number': forms.TextInput(attrs={'class': INPUT, 'placeholder': '+1 (555) 000-0000'}),
            'email': forms.EmailInput(attrs={'class': INPUT, 'placeholder': 'email@example.com'}),
            'address_line1': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Street address'}),
            'address_line2': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Apt, suite, unit (optional)'}),
            'city': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'State / Province'}),
            'country': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Country'}),
            'postal_code': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Postal code'}),
            'is_default': forms.CheckboxInput(attrs={'class': CHECKBOX}),
        }


class ShipmentForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = [
            'service_type', 'package_type', 'description',
            'weight_kg', 'length_cm', 'width_cm', 'height_cm', 'declared_value',
            'is_insured', 'is_fragile',
            'sender_name', 'sender_phone', 'sender_address', 'sender_city', 'sender_country', 'sender_postal_code',
            'recipient_name', 'recipient_phone', 'recipient_address', 'recipient_city', 'recipient_country', 'recipient_postal_code',
        ]
        widgets = {
            'service_type': forms.Select(attrs={'class': SELECT}),
            'package_type': forms.Select(attrs={'class': SELECT}),
            'description': forms.TextInput(attrs={'class': INPUT, 'placeholder': "What's inside? (e.g. Electronics, Documents)"}),
            'weight_kg': forms.NumberInput(attrs={'class': INPUT, 'step': '0.1', 'placeholder': '0.0'}),
            'length_cm': forms.NumberInput(attrs={'class': INPUT, 'step': '0.1', 'placeholder': '10'}),
            'width_cm': forms.NumberInput(attrs={'class': INPUT, 'step': '0.1', 'placeholder': '10'}),
            'height_cm': forms.NumberInput(attrs={'class': INPUT, 'step': '0.1', 'placeholder': '10'}),
            'declared_value': forms.NumberInput(attrs={'class': INPUT, 'step': '0.01', 'placeholder': '0.00'}),
            'is_insured': forms.CheckboxInput(attrs={'class': CHECKBOX}),
            'is_fragile': forms.CheckboxInput(attrs={'class': CHECKBOX}),

            'sender_name': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Full name'}),
            'sender_phone': forms.TextInput(attrs={'class': INPUT, 'placeholder': '+1 (555) 000-0000'}),
            'sender_address': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Street address'}),
            'sender_city': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'City'}),
            'sender_country': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Country'}),
            'sender_postal_code': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Postal code'}),

            'recipient_name': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Full name'}),
            'recipient_phone': forms.TextInput(attrs={'class': INPUT, 'placeholder': '+1 (555) 000-0000'}),
            'recipient_address': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Street address'}),
            'recipient_city': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'City'}),
            'recipient_country': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Country'}),
            'recipient_postal_code': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Postal code'}),
        }


class CustomerChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f'{obj.get_full_name} — {obj.email}'


class AdminShipmentForm(ShipmentForm):
    """Staff-only: books a shipment on behalf of a chosen customer."""

    customer = CustomerChoiceField(
        queryset=CustomUser.objects.filter(is_staff=False).order_by('first_name', 'last_name'),
        widget=forms.Select(attrs={'class': SELECT}),
        label='Customer',
        empty_label='Select a customer…',
    )


class AdminShipmentEditForm(ShipmentForm):
    """Staff-only: full edit of an existing shipment's details — everything
    except who it belongs to and its tracking number. Payment status and
    estimated delivery are editable here too, on top of the package/sender/
    recipient fields ShipmentForm already covers."""

    class Meta(ShipmentForm.Meta):
        fields = ShipmentForm.Meta.fields + ['payment_status', 'estimated_delivery']
        widgets = {
            **ShipmentForm.Meta.widgets,
            'payment_status': forms.Select(attrs={'class': SELECT}),
            'estimated_delivery': forms.DateInput(attrs={'class': INPUT, 'type': 'date'}),
        }


class TrackingEventForm(forms.ModelForm):
    """Staff-only: posts a new checkpoint, which is how a shipment's status
    and location actually get updated (see TrackingEvent.save())."""

    class Meta:
        model = TrackingEvent
        fields = ['status', 'location', 'note']
        widgets = {
            'status': forms.Select(attrs={'class': SELECT}),
            'location': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'e.g. Hong Kong International Hub'}),
            'note': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Optional note for this checkpoint'}),
        }


class TrackingEventEditForm(TrackingEventForm):
    """Staff-only: edits an existing checkpoint, including backdating/
    correcting its timestamp (which determines whether it's treated as the
    shipment's current stage — see Shipment.sync_from_latest_event())."""

    class Meta(TrackingEventForm.Meta):
        fields = TrackingEventForm.Meta.fields + ['timestamp']
        widgets = {
            **TrackingEventForm.Meta.widgets,
            'timestamp': forms.DateTimeInput(attrs={'class': INPUT, 'type': 'datetime-local', 'step': '1'}, format='%Y-%m-%dT%H:%M:%S'),
        }


class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['category', 'priority', 'shipment', 'subject', 'description']
        widgets = {
            'category': forms.Select(attrs={'class': SELECT}),
            'priority': forms.Select(attrs={'class': SELECT}),
            'shipment': forms.Select(attrs={'class': SELECT}),
            'subject': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Briefly describe the issue'}),
            'description': forms.Textarea(attrs={'class': TEXTAREA, 'rows': 5, 'placeholder': 'Give us the full details...'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['shipment'].queryset = user.shipments.all()
        self.fields['shipment'].required = False


class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'phone_number', 'company_name',
            'address_line1', 'address_line2', 'city', 'state', 'country', 'postal_code', 'profile_image',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': INPUT}),
            'last_name': forms.TextInput(attrs={'class': INPUT}),
            'phone_number': forms.TextInput(attrs={'class': INPUT}),
            'company_name': forms.TextInput(attrs={'class': INPUT}),
            'address_line1': forms.TextInput(attrs={'class': INPUT}),
            'address_line2': forms.TextInput(attrs={'class': INPUT}),
            'city': forms.TextInput(attrs={'class': INPUT}),
            'state': forms.TextInput(attrs={'class': INPUT}),
            'country': forms.TextInput(attrs={'class': INPUT}),
            'postal_code': forms.TextInput(attrs={'class': INPUT}),
            'profile_image': forms.FileInput(attrs={'class': 'text-sm text-white/60'}),
        }


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': (
                    'flex-1 rounded-full bg-white/5 border border-white/10 px-6 py-4 text-white '
                    'placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-cargo-500/40 '
                    'focus:border-cargo-500/60 transition-all'
                ),
                'placeholder': 'you@company.com',
            }),
        }


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'company_name', 'topic', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Full name'}),
            'email': forms.EmailInput(attrs={'class': INPUT, 'placeholder': 'you@company.com'}),
            'company_name': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Company (optional)'}),
            'topic': forms.Select(attrs={'class': SELECT}),
            'message': forms.Textarea(attrs={'class': TEXTAREA, 'rows': 5, 'placeholder': 'How can we help?'}),
        }


class ChangePasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({'class': INPUT, 'placeholder': 'New password'})
        self.fields['new_password2'].widget.attrs.update({'class': INPUT, 'placeholder': 'Confirm new password'})
