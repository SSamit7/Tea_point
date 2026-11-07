import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='RestaurantSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(default='The Golden Fork', max_length=100)),
                ('tagline', models.CharField(blank=True, default='Fine dining, effortless ordering', max_length=200)),
                ('upi_id', models.CharField(default='restaurant@upi', help_text='Your UPI ID / VPA that receives payments, e.g. restaurant@okicici', max_length=100)),
                ('payee_name', models.CharField(default='Restaurant', max_length=100)),
                ('tax_percent', models.DecimalField(decimal_places=2, default=5.0, max_digits=5)),
                ('address', models.CharField(blank=True, max_length=255)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='branding/')),
            ],
            options={
                'verbose_name': 'Restaurant Settings',
                'verbose_name_plural': 'Restaurant Settings',
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=80)),
                ('slug', models.SlugField(blank=True, unique=True)),
                ('order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name_plural': 'Categories',
                'ordering': ['order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Table',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('number', models.PositiveIntegerField(unique=True)),
                ('capacity', models.PositiveIntegerField(default=2)),
                ('token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['number'],
            },
        ),
        migrations.CreateModel(
            name='MenuItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=120)),
                ('slug', models.SlugField(blank=True)),
                ('description', models.TextField(blank=True)),
                ('price', models.DecimalField(decimal_places=2, max_digits=8)),
                ('image', models.ImageField(blank=True, null=True, upload_to='menu/')),
                ('is_veg', models.BooleanField(default=True, help_text='Vegetarian?')),
                ('is_special', models.BooleanField(default=False, help_text="Chef's special / featured")),
                ('is_available', models.BooleanField(default=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='core.category')),
            ],
            options={
                'ordering': ['category__order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('cart', 'In Cart'), ('placed', 'Placed'), ('preparing', 'Preparing'), ('served', 'Served'), ('billed', 'Bill Generated'), ('paid', 'Paid')], default='placed', max_length=15)),
                ('notes', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('table', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='core.table')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('price_at_order', models.DecimalField(decimal_places=2, max_digits=8)),
                ('notes', models.CharField(blank=True, max_length=200)),
                ('menu_item', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.menuitem')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='core.order')),
            ],
        ),
        migrations.CreateModel(
            name='Bill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('bill_no', models.CharField(blank=True, max_length=30, unique=True)),
                ('subtotal', models.DecimalField(decimal_places=2, max_digits=10)),
                ('tax_percent', models.DecimalField(decimal_places=2, max_digits=5)),
                ('tax_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('discount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('total', models.DecimalField(decimal_places=2, max_digits=10)),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
                ('is_paid', models.BooleanField(default=False)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('payment_method', models.CharField(blank=True, choices=[('upi', 'UPI / Wallet'), ('cash', 'Cash'), ('card', 'Card')], max_length=10)),
                ('order', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='bill', to='core.order')),
            ],
        ),
    ]
