from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='bill',
            name='gateway_link_id',
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name='bill',
            name='gateway_link_url',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='bill',
            name='gateway_payment_id',
            field=models.CharField(blank=True, max_length=64),
        ),
    ]
