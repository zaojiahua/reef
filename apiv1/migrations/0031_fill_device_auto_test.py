# Generated by Django 2.2 on 2019-10-08 07:58

from django.db import migrations
from django.db.models import Q


# 將现有Device.auto_test值调整为True if status in (idle/busy)
def auto_fill_device_auto_test(apps, schema_editor):
    device_cls = apps.get_model("apiv1", "Device")
    devices = device_cls.objects.filter(Q(status='idle') | Q(status='busy'))
    for device in devices:
        device.auto_test = True
        device.save()


def reverse(apps, editor_schema):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('apiv1', '0030_auto_20190927_1029'),
    ]

    operations = [
        migrations.RunPython(
            code=auto_fill_device_auto_test,
            reverse_code=reverse
        )
    ]
