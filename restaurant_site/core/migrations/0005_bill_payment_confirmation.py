from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0004_fonepay_settings'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bill',
            name='payment_method',
            field=models.CharField(blank=True, choices=[('fonepay', 'Fonepay / Bank QR'), ('esewa', 'eSewa'), ('khalti', 'Khalti'), ('bank', 'Mobile Banking'), ('upi', 'Legacy UPI / Wallet'), ('cash', 'Cash'), ('card', 'Card')], max_length=10),
        ),
        migrations.AddField(
            model_name='bill',
            name='payment_requested',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='bill',
            name='payment_requested_method',
            field=models.CharField(blank=True, default='', max_length=12),
        ),
        migrations.AddField(
            model_name='bill',
            name='payment_requested_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
