from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0003_table_notifications')]
    operations = [
        migrations.AddField(
            model_name='restaurantsettings',
            name='fonepay_merchant_name',
            field=models.CharField(blank=True, default='', help_text='Name printed on your Fonepay merchant QR.', max_length=120),
        ),
        migrations.AddField(
            model_name='restaurantsettings',
            name='fonepay_qr_image',
            field=models.ImageField(blank=True, help_text='Upload the official QR image issued to your restaurant by Fonepay or your acquiring bank.', null=True, upload_to='payments/fonepay/'),
        ),
        migrations.AddField(
            model_name='restaurantsettings',
            name='fonepay_instructions',
            field=models.CharField(blank=True, default='Scan this Fonepay QR using your Nepali mobile banking app.', max_length=255),
        ),
    ]
