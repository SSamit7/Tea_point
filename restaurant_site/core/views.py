import logging
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import MenuItemForm, TableNotificationSettingForm, RestaurantPaymentSettingsForm
from .models import Category, MenuItem, Table, Order, OrderItem, Bill, RestaurantSettings, TableNotificationSetting

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _cart_key(table_id):
    return f'cart_table_{table_id}'


def _active_order_for(table):
    """The most recent order for this table that hasn't been paid/closed yet."""
    return (Order.objects
            .filter(table=table)
            .exclude(status__in=[Order.STATUS_CART, Order.STATUS_PAID])
            .order_by('-created_at')
            .first())


def _generate_bill(order):
    """Idempotent — returns existing bill if already generated."""
    if hasattr(order, 'bill'):
        return order.bill
    settings_obj = RestaurantSettings.load()
    subtotal = order.subtotal
    tax_amount = (subtotal * settings_obj.tax_percent / Decimal('100')).quantize(Decimal('0.01'))
    total = subtotal + tax_amount
    bill = Bill.objects.create(
        order=order,
        subtotal=subtotal,
        tax_percent=settings_obj.tax_percent,
        tax_amount=tax_amount,
        total=total,
    )
    order.status = Order.STATUS_BILLED
    order.save()
    return bill


def is_staff_user(user):
    return user.is_authenticated and user.is_staff


def is_admin_user(user):
    # Only superusers can change menu, payment, and restaurant configuration.
    return user.is_authenticated and user.is_superuser


@user_passes_test(is_admin_user, login_url='admin_login')
def menu_management(request):
    """Owner dashboard for manually managing customer-facing menu items."""
    items = MenuItem.objects.select_related('category').all()
    form = MenuItemForm()
    return render(request, 'core/menu_management.html', {'items': items, 'form': form})


@user_passes_test(is_admin_user, login_url='admin_login')
@require_POST
def menu_item_add(request):
    form = MenuItemForm(request.POST, request.FILES)
    if form.is_valid():
        item = form.save()
        messages.success(request, f'{item.name} was added to the menu at NPR रु {item.price}.')
        return redirect('menu_management')
    items = MenuItem.objects.select_related('category').all()
    return render(request, 'core/menu_management.html', {'items': items, 'form': form, 'show_add_form': True})


@user_passes_test(is_admin_user, login_url='admin_login')
def menu_item_edit(request, item_id):
    item = get_object_or_404(MenuItem, pk=item_id)
    form = MenuItemForm(request.POST or None, request.FILES or None, instance=item)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'{item.name} was updated. The new price is NPR रु {item.price}.')
        return redirect('menu_management')
    return render(request, 'core/menu_item_form.html', {'form': form, 'item': item, 'editing': True})


@user_passes_test(is_admin_user, login_url='admin_login')
@require_POST
def menu_item_delete(request, item_id):
    item = get_object_or_404(MenuItem, pk=item_id)
    name = item.name
    # Keep historical order records intact; remove the dish from customer menus.
    item.is_available = False
    item.save(update_fields=['is_available'])
    messages.success(request, f'{name} was removed from the customer menu (order history was preserved).')
    return redirect('menu_management')


@user_passes_test(is_admin_user, login_url='admin_login')
def payment_settings(request):
    """Configure the official Fonepay QR issued to this restaurant."""
    settings_obj = RestaurantSettings.load()
    form = RestaurantPaymentSettingsForm(request.POST or None, request.FILES or None, instance=settings_obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Fonepay payment settings saved.')
        return redirect('payment_settings')
    return render(request, 'core/payment_settings.html', {'form': form, 'settings': settings_obj})


# ----------------------------------------------------------------------
# Customer-facing views
# ----------------------------------------------------------------------

def landing(request):
    tables = Table.objects.filter(is_active=True)
    settings_obj = RestaurantSettings.load()
    return render(request, 'core/landing.html', {
        'tables': tables, 'settings': settings_obj,
    })


def scan_table(request, token):
    """Where a table's QR code points to: /t/<token>/"""
    table = get_object_or_404(Table, token=token, is_active=True)
    return redirect('menu', table_id=table.number)


def menu_view(request, table_id):
    table = get_object_or_404(Table, number=table_id, is_active=True)
    categories = Category.objects.filter(items__is_available=True).distinct().prefetch_related('items')
    cart = request.session.get(_cart_key(table.id), {})
    cart_count = sum(cart.values())
    settings_obj = RestaurantSettings.load()
    active_order = _active_order_for(table)

    return render(request, 'core/menu.html', {
        'table': table,
        'categories': categories,
        'cart_count': cart_count,
        'settings': settings_obj,
        'active_order': active_order,
    })


def add_to_cart(request, table_id, item_id):
    table = get_object_or_404(Table, number=table_id, is_active=True)
    item = get_object_or_404(MenuItem, id=item_id, is_available=True)
    key = _cart_key(table.id)
    cart = request.session.get(key, {})
    cart[str(item.id)] = cart.get(str(item.id), 0) + 1
    request.session[key] = cart
    request.session.modified = True

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return HttpResponse(str(sum(cart.values())))
    return redirect('menu', table_id=table.number)


def update_cart(request, table_id, item_id, action):
    table = get_object_or_404(Table, number=table_id, is_active=True)
    key = _cart_key(table.id)
    cart = request.session.get(key, {})
    item_key = str(item_id)

    if item_key in cart:
        if action == 'inc':
            cart[item_key] += 1
        elif action == 'dec':
            cart[item_key] -= 1
            if cart[item_key] <= 0:
                del cart[item_key]
        elif action == 'remove':
            del cart[item_key]

    request.session[key] = cart
    request.session.modified = True
    return redirect('cart', table_id=table.number)


def cart_view(request, table_id):
    table = get_object_or_404(Table, number=table_id, is_active=True)
    cart = request.session.get(_cart_key(table.id), {})

    lines = []
    subtotal = Decimal('0.00')
    for item_id, qty in cart.items():
        try:
            item = MenuItem.objects.get(id=item_id)
        except MenuItem.DoesNotExist:
            continue
        line_total = item.price * qty
        subtotal += line_total
        lines.append({'item': item, 'qty': qty, 'line_total': line_total})

    settings_obj = RestaurantSettings.load()
    tax = (subtotal * settings_obj.tax_percent / Decimal('100')).quantize(Decimal('0.01'))
    total = subtotal + tax
    active_order = _active_order_for(table)

    return render(request, 'core/cart.html', {
        'table': table,
        'lines': lines,
        'subtotal': subtotal,
        'tax': tax,
        'total': total,
        'settings': settings_obj,
        'active_order': active_order,
    })


@require_POST
def place_order(request, table_id):
    table = get_object_or_404(Table, number=table_id, is_active=True)
    key = _cart_key(table.id)
    cart = request.session.get(key, {})

    if not cart:
        messages.error(request, "Your cart is empty — add a few dishes first.")
        return redirect('menu', table_id=table.number)

    available_lines = []
    for item_id, qty in cart.items():
        try:
            item = MenuItem.objects.get(id=item_id, is_available=True)
        except (MenuItem.DoesNotExist, ValueError, TypeError):
            continue
        if qty > 0:
            available_lines.append((item, qty))

    if not available_lines:
        request.session[key] = {}
        request.session.modified = True
        messages.error(request, "Those items are no longer available. Please choose from the current menu.")
        return redirect('menu', table_id=table.number)

    notes = request.POST.get('notes', '').strip()

    # If there's already an active (unbilled) order for this table, append to it
    existing = Order.objects.filter(
        table=table, status__in=[Order.STATUS_PLACED, Order.STATUS_PREPARING]
    ).order_by('-created_at').first()

    order = existing or Order.objects.create(table=table, status=Order.STATUS_PLACED, notes=notes)
    if existing and notes:
        order.notes = (order.notes + " | " + notes).strip(" |")
        order.save()

    for item, qty in available_lines:
        OrderItem.objects.create(order=order, menu_item=item, quantity=qty, price_at_order=item.price)

    request.session[key] = {}
    request.session.modified = True
    messages.success(request, "Order placed! The kitchen has been notified.")
    return redirect('order_status', order_id=order.id)


def order_status(request, order_id):
    order = get_object_or_404(Order.objects.select_related('table'), id=order_id)
    settings_obj = RestaurantSettings.load()
    bill = getattr(order, 'bill', None)
    return render(request, 'core/order_status.html', {
        'order': order, 'settings': settings_obj, 'bill': bill,
    })


def order_status_data(request, order_id):
    """Lightweight polling endpoint; update status without reloading the whole page."""
    order = get_object_or_404(Order, id=order_id)
    bill = getattr(order, 'bill', None)
    return JsonResponse({
        'status': order.status,
        'status_display': order.get_status_display(),
        'paid': bool(bill and bill.is_paid),
        'payment_method': bill.get_payment_method_display() if bill and bill.is_paid else '',
        'bill_ready': bool(bill),
        'payment_requested': bool(bill and bill.payment_requested),
    })


def request_bill(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    _generate_bill(order)
    return redirect('bill_view', order_id=order.id)


def bill_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    bill = _generate_bill(order)
    settings_obj = RestaurantSettings.load()
    return render(request, 'core/bill.html', {
        'order': order,
        'bill': bill,
        'settings': settings_obj,
        'fonepay_ready': bool(settings_obj.fonepay_qr_image),
    })


def confirm_paid(request, order_id):
    """Record a payment notification only; never trust a customer-side success tap."""
    if request.method != 'POST':
        return redirect('bill_view', order_id=order_id)
    order = get_object_or_404(Order, id=order_id)
    bill = _generate_bill(order)
    if not bill.is_paid:
        method = request.POST.get('method', 'fonepay')
        allowed = {'cash', 'fonepay', 'esewa', 'khalti', 'bank'}
        if method not in allowed:
            method = 'fonepay'
        bill.payment_requested = True
        bill.payment_requested_method = method
        bill.payment_requested_at = timezone.now()
        bill.save(update_fields=['payment_requested', 'payment_requested_method', 'payment_requested_at'])
        messages.info(request, "Your payment notification was sent. The bill will remain unpaid until staff manually confirms receipt.")
    return redirect('order_status', order_id=order.id)


# ----------------------------------------------------------------------
# Staff-facing views
# ----------------------------------------------------------------------

@user_passes_test(is_admin_user, login_url='admin_login')
def notification_settings(request):
    """Admin screen to configure independent staff/kitchen alerts for each table."""
    tables = Table.objects.all()
    if request.method == 'POST':
        table = get_object_or_404(Table, pk=request.POST.get('table_id'))
        setting, _ = TableNotificationSetting.objects.get_or_create(table=table)
        form = TableNotificationSettingForm(request.POST, request.FILES, instance=setting)
        if form.is_valid():
            form.save()
            messages.success(request, f'Notification settings saved for Table {table.number}.')
        else:
            messages.error(request, 'Please correct the notification settings and try again.')
        return redirect('notification_settings')
    rows = []
    for table in tables:
        setting, _ = TableNotificationSetting.objects.get_or_create(table=table)
        rows.append({'table': table, 'form': TableNotificationSettingForm(instance=setting)})
    return render(request, 'core/notification_settings.html', {'rows': rows})


@user_passes_test(is_staff_user, login_url='staff_login')
def staff_new_orders(request):
    """Small polling endpoint used by staff screens for new-order alerts."""
    try:
        after_id = max(0, int(request.GET.get('after', 0)))
    except (TypeError, ValueError):
        after_id = 0
    new_orders = (Order.objects.filter(id__gt=after_id, status=Order.STATUS_PLACED)
                  .select_related('table').order_by('id'))
    payload = []
    for order in new_orders:
        setting, _ = TableNotificationSetting.objects.get_or_create(table=order.table)
        payload.append({
            'id': order.id, 'table': order.table.number, 'created': order.created_at.isoformat(),
            'staff_enabled': setting.staff_enabled, 'kitchen_enabled': setting.kitchen_enabled,
            'staff_sound': setting.staff_sound, 'kitchen_sound': setting.kitchen_sound,
            'staff_audio': setting.staff_custom_audio.url if setting.staff_custom_audio else '',
            'kitchen_audio': setting.kitchen_custom_audio.url if setting.kitchen_custom_audio else '',
        })
    return JsonResponse({'orders': payload})


@user_passes_test(is_staff_user, login_url='staff_login')
def staff_dashboard(request):
    active_orders = (Order.objects
                      .exclude(status__in=[Order.STATUS_CART, Order.STATUS_PAID])
                      .select_related('table', 'bill')
                      .prefetch_related('items__menu_item'))
    tables = Table.objects.all()
    recent_paid = (Order.objects.filter(status=Order.STATUS_PAID)
                   .select_related('table', 'bill').order_by('-updated_at')[:10])
    payment_requests = (Bill.objects.filter(is_paid=False)
                        .select_related('order__table').order_by('-generated_at'))
    return render(request, 'core/staff_dashboard.html', {
        'orders': active_orders, 'tables': tables, 'recent_paid': recent_paid,
        'payment_requests': payment_requests,
    })


@user_passes_test(is_staff_user, login_url='staff_login')
def staff_payment_requests(request):
    """Poll pending customer payment claims for staff; this does not verify payment."""
    pending = (Bill.objects.filter(is_paid=False)
               .select_related('order__table').order_by('-generated_at'))
    return JsonResponse({'requests': [{
        'order_id': bill.order_id,
        'table': bill.order.table.number,
        'bill_no': bill.bill_no,
        'amount': str(bill.total),
        'method': bill.payment_requested_method or 'fonepay',
        'payment_requested': bill.payment_requested,
        'requested_at': bill.payment_requested_at.isoformat() if bill.payment_requested_at else '',
    } for bill in pending]})


@user_passes_test(is_staff_user, login_url='kitchen_login')
def kitchen_dashboard(request):
    active_orders = (Order.objects.exclude(status__in=[Order.STATUS_CART, Order.STATUS_PAID])
                     .select_related('table', 'bill').prefetch_related('items__menu_item'))
    tables = Table.objects.all()
    payment_requests = (Bill.objects.filter(is_paid=False)
                        .select_related('order__table').order_by('-generated_at'))
    return render(request, 'core/staff_dashboard.html', {
        'orders': active_orders, 'tables': tables, 'station': 'kitchen',
        'payment_requests': payment_requests,
    })


@user_passes_test(is_staff_user, login_url='staff_login')
@require_POST
def staff_update_status(request, order_id, status):
    order = get_object_or_404(Order, id=order_id)
    valid_statuses = dict(Order.STATUS_CHOICES)
    if status in valid_statuses:
        order.status = status
        order.save()
        messages.success(request, f"Order #{order.id} marked as {valid_statuses[status]}.")
    return redirect('kitchen_dashboard' if request.POST.get('station') == 'kitchen' else 'staff_dashboard')


@user_passes_test(is_staff_user, login_url='staff_login')
@require_POST
def staff_mark_paid(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    bill = _generate_bill(order)
    # Manual staff confirmation only: no wallet, bank, QR, or payment API is called.
    choice = request.POST.get('method', 'cash')
    if choice == 'online':
        requested = bill.payment_requested_method
        method = requested if requested in {'fonepay', 'esewa', 'khalti', 'bank'} else 'fonepay'
    elif choice in {'cash', 'fonepay', 'esewa', 'khalti', 'bank', 'card'}:
        method = choice
    else:
        method = 'cash'
    destination = 'kitchen_dashboard' if request.POST.get('station') == 'kitchen' else 'staff_dashboard'
    if bill.is_paid:
        messages.info(request, f"Bill {bill.bill_no} was already confirmed as paid.")
        return redirect(destination)
    bill.mark_paid(method)
    bill.payment_requested = False
    bill.save(update_fields=['payment_requested'])
    messages.success(request, f"Confirmed NPR रु{bill.total} received for Table {order.table.number} by {bill.get_payment_method_display()}.")
    return redirect(destination)
