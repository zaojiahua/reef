# Generated by Django 2.2 on 2019-09-27 02:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apiv1', '0029_device_auto_test'),
    ]

    operations = [
        migrations.AlterField(
            model_name='device',
            name='auto_test',
            field=models.BooleanField(default=True, verbose_name='系统是否自动分派任务给该设备'),
        ),
    ]
