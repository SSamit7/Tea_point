from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0002_bill_gateway_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='TableNotificationSetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('staff_enabled', models.BooleanField(default=True)),
                ('kitchen_enabled', models.BooleanField(default=True)),
                ('staff_sound', models.CharField(choices=[('chime', 'Chime'), ('bell', 'Bell'), ('double', 'Double beep'), ('urgent', 'Urgent pulse'), ('silent', 'Silent')], default='chime', max_length=12)),
                ('kitchen_sound', models.CharField(choices=[('chime', 'Chime'), ('bell', 'Bell'), ('double', 'Double beep'), ('urgent', 'Urgent pulse'), ('silent', 'Silent')], default='bell', max_length=12)),
                ('staff_custom_audio', models.FileField(blank=True, help_text='Optional MP3/WAV file. Overrides the selected staff sound.', null=True, upload_to='notification_sounds/')),
                ('kitchen_custom_audio', models.FileField(blank=True, help_text='Optional MP3/WAV file. Overrides the selected kitchen sound.', null=True, upload_to='notification_sounds/')),
                ('table', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='notification_setting', to='core.table')),
            ],
            options={
                'verbose_name': 'Table notification setting',
                'verbose_name_plural': 'Table notification settings',
                'ordering': ['table__number'],
            },
        ),
    ]
