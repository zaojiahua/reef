# Generated by Django 2.2 on 2021-04-25 08:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('apiv1', '0076_auto_20210423_1625'),
    ]

    operations = [
        migrations.AddField(
            model_name='subsidiarydevice',
            name='cabinet',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subsidiarydevice', to='apiv1.Cabinet', verbose_name='机柜'),
        ),
    ]
