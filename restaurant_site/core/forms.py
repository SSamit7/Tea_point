from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from .models import MenuItem


class MenuItemForm(forms.ModelForm):
    """Menu prices are always entered explicitly by the restaurant owner."""
    price = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        min_value=0.01,
        required=True,
        label='Selling price',
        help_text='Enter the exact price customers should pay. No price is generated automatically.',
        widget=forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'min': '0.01', 'placeholder': 'e.g. 250.00'}),
    )

    class Meta:
        model = MenuItem
        fields = ['category', 'name', 'description', 'price', 'image', 'is_veg', 'is_special', 'is_available']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-input'}),
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Food item name'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Description (optional)'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-input'}),
        }


from .models import TableNotificationSetting


class TableNotificationSettingForm(forms.ModelForm):
    class Meta:
        model = TableNotificationSetting
        fields = ['staff_enabled', 'staff_sound', 'staff_custom_audio', 'kitchen_enabled', 'kitchen_sound', 'kitchen_custom_audio']
        widgets = {
            'staff_sound': forms.Select(attrs={'class': 'form-input'}),
            'kitchen_sound': forms.Select(attrs={'class': 'form-input'}),
            'staff_custom_audio': forms.ClearableFileInput(attrs={'class': 'form-input', 'accept': 'audio/*'}),
            'kitchen_custom_audio': forms.ClearableFileInput(attrs={'class': 'form-input', 'accept': 'audio/*'}),
        }


from .models import RestaurantSettings


class RestaurantPaymentSettingsForm(forms.ModelForm):
    class Meta:
        model = RestaurantSettings
        fields = ['fonepay_merchant_name', 'fonepay_qr_image', 'fonepay_instructions']
        widgets = {
            'fonepay_merchant_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Merchant name shown on Fonepay'}),
            'fonepay_qr_image': forms.ClearableFileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
            'fonepay_instructions': forms.TextInput(attrs={'class': 'form-input'}),
        }


class AdminAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_superuser:
            raise ValidationError('This account does not have Admin access.', code='no_admin_access')


class KitchenAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            raise ValidationError('This account does not have Kitchen access.', code='no_kitchen_access')
