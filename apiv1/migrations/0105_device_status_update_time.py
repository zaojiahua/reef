# Generated by Django 2.2 on 2022-04-25 03:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apiv1', '0104_tboard_test_gather_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='status_update_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='设备状态更新时间'),
        ),
    ]
