from django.contrib import admin
from .models import Category, MenuItem, Table, Order, OrderItem, Bill, RestaurantSettings, TableNotificationSetting


@admin.register(RestaurantSettings)
class RestaurantSettingsAdmin(admin.ModelAdmin):
    list_display = ['name', 'fonepay_merchant_name', 'tax_percent']
    exclude = ['upi_id', 'payee_name']

    def has_add_permission(self, request):
        # Singleton — only one settings row allowed
        return not RestaurantSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'is_veg', 'is_special', 'is_available']
    list_filter = ['category', 'is_veg', 'is_special', 'is_available']
    list_editable = ['price', 'is_available']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['number', 'capacity', 'token', 'is_active']
    readonly_fields = ['token']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['line_total']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'table', 'status', 'item_count', 'created_at']
    list_filter = ['status', 'table']
    inlines = [OrderItemInline]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ['bill_no', 'order', 'total', 'is_paid', 'payment_method', 'payment_requested', 'generated_at']
    list_filter = ['is_paid', 'payment_method']
    readonly_fields = ['bill_no', 'generated_at', 'gateway_link_id', 'gateway_link_url', 'gateway_payment_id']


@admin.register(TableNotificationSetting)
class TableNotificationSettingAdmin(admin.ModelAdmin):
    list_display = ['table', 'staff_enabled', 'staff_sound', 'kitchen_enabled', 'kitchen_sound']
    list_filter = ['staff_enabled', 'kitchen_enabled', 'staff_sound', 'kitchen_sound']
