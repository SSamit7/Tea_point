import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class RestaurantSettings(models.Model):
    """Singleton settings row — edit in Django admin."""
    name = models.CharField(max_length=100, default="The Golden Fork")
    tagline = models.CharField(max_length=200, blank=True, default="Fine dining, effortless ordering")
    upi_id = models.CharField(
        max_length=100, default="restaurant@upi",
        help_text="Your UPI ID / VPA that receives payments, e.g. restaurant@okicici"
    )
    payee_name = models.CharField(max_length=100, default="Restaurant")  # legacy field; not used for Nepal Fonepay
    fonepay_merchant_name = models.CharField(max_length=120, blank=True, default="", help_text="Name printed on your Fonepay merchant QR.")
    fonepay_qr_image = models.ImageField(upload_to="payments/fonepay/", blank=True, null=True, help_text="Upload the official QR image issued to your restaurant by Fonepay or your acquiring bank.")
    fonepay_instructions = models.CharField(max_length=255, blank=True, default="Scan this Fonepay QR using your Nepali mobile banking app.")
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("5.00"))
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    logo = models.ImageField(upload_to='branding/', blank=True, null=True)

    class Meta:
        verbose_name = "Restaurant Settings"
        verbose_name_plural = "Restaurant Settings"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.pk = 1  # force singleton
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(
            pk=1, defaults={"upi_id": "restaurant@upi", "payee_name": "Restaurant"}
        )
        return obj


class Category(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    category = models.ForeignKey(Category, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    slug = models.SlugField(blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='menu/', blank=True, null=True)
    is_veg = models.BooleanField(default=True, help_text="Vegetarian?")
    is_special = models.BooleanField(default=False, help_text="Chef's special / featured")
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ['category__order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Table(models.Model):
    number = models.PositiveIntegerField(unique=True)
    capacity = models.PositiveIntegerField(default=2)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['number']

    def __str__(self):
        return f"Table {self.number}"


class TableNotificationSetting(models.Model):
    """Per-table staff and kitchen alert preferences."""
    SOUND_CHOICES = [
        ('chime', 'Chime'),
        ('bell', 'Bell'),
        ('double', 'Double beep'),
        ('urgent', 'Urgent pulse'),
        ('silent', 'Silent'),
    ]
    table = models.OneToOneField(Table, related_name='notification_setting', on_delete=models.CASCADE)
    staff_enabled = models.BooleanField(default=True)
    kitchen_enabled = models.BooleanField(default=True)
    staff_sound = models.CharField(max_length=12, choices=SOUND_CHOICES, default='chime')
    kitchen_sound = models.CharField(max_length=12, choices=SOUND_CHOICES, default='bell')
    staff_custom_audio = models.FileField(upload_to='notification_sounds/', blank=True, null=True, help_text='Optional MP3/WAV file. Overrides the selected staff sound.')
    kitchen_custom_audio = models.FileField(upload_to='notification_sounds/', blank=True, null=True, help_text='Optional MP3/WAV file. Overrides the selected kitchen sound.')

    class Meta:
        verbose_name = 'Table notification setting'
        verbose_name_plural = 'Table notification settings'
        ordering = ['table__number']

    def __str__(self):
        return f'Notification settings — {self.table}'


class Order(models.Model):
    STATUS_CART = 'cart'
    STATUS_PLACED = 'placed'
    STATUS_PREPARING = 'preparing'
    STATUS_SERVED = 'served'
    STATUS_BILLED = 'billed'
    STATUS_PAID = 'paid'
    STATUS_CHOICES = [
        (STATUS_CART, 'In Cart'),
        (STATUS_PLACED, 'Placed'),
        (STATUS_PREPARING, 'Preparing'),
        (STATUS_SERVED, 'Served'),
        (STATUS_BILLED, 'Bill Generated'),
        (STATUS_PAID, 'Paid'),
    ]

    table = models.ForeignKey(Table, related_name='orders', on_delete=models.CASCADE)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=STATUS_PLACED)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} — Table {self.table.number} ({self.get_status_display()})"

    @property
    def subtotal(self):
        total = Decimal('0.00')
        for item in self.items.all():
            total += item.line_total
        return total

    @property
    def item_count(self):
        return sum(i.quantity for i in self.items.all())

    STEPS = [STATUS_PLACED, STATUS_PREPARING, STATUS_SERVED, STATUS_BILLED, STATUS_PAID]

    @property
    def step_index(self):
        try:
            return self.STEPS.index(self.status)
        except ValueError:
            return 0


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price_at_order = models.DecimalField(max_digits=8, decimal_places=2)
    notes = models.CharField(max_length=200, blank=True)

    @property
    def line_total(self):
        return self.price_at_order * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.menu_item.name}"


class Bill(models.Model):
    PAYMENT_METHODS = [
        ('fonepay', 'Fonepay / Bank QR'),
        ('esewa', 'eSewa'),
        ('khalti', 'Khalti'),
        ('bank', 'Mobile Banking'),
        ('upi', 'Legacy UPI / Wallet'),
        ('cash', 'Cash'),
        ('card', 'Card'),
    ]
    order = models.OneToOneField(Order, related_name='bill', on_delete=models.CASCADE)
    bill_no = models.CharField(max_length=30, unique=True, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=2)
    generated_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(blank=True, null=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, blank=True)
    payment_requested = models.BooleanField(default=False)
    payment_requested_method = models.CharField(max_length=12, blank=True, default='')
    payment_requested_at = models.DateTimeField(blank=True, null=True)

    # Legacy gateway fields retained for database migration compatibility; unused.
    # All payments are confirmed manually by staff.
    gateway_link_id = models.CharField(max_length=64, blank=True)
    gateway_link_url = models.URLField(blank=True)
    gateway_payment_id = models.CharField(max_length=64, blank=True)

    def save(self, *args, **kwargs):
        if not self.bill_no:
            today = timezone.now().strftime('%Y%m%d')
            count_today = Bill.objects.filter(bill_no__startswith=f"INV-{today}").count() + 1
            self.bill_no = f"INV-{today}-{count_today:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.bill_no

    def mark_paid(self, method='fonepay'):
        self.is_paid = True
        self.paid_at = timezone.now()
        self.payment_method = method
        self.save()
        self.order.status = Order.STATUS_PAID
        self.order.save()
