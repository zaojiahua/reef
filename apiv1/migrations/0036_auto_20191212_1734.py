# Generated by Django 2.2 on 2019-12-12 09:34

from django.db import migrations


def default_cabinet_ip_addr(apps, schema_editor):
    cabinet_cls = apps.get_model('apiv1', 'Cabinet')
    try:
        cabinets = cabinet_cls.objects.filter(ip_address__isnull=True)
        for cabinet in cabinets:
            cabinet.ip_address = '0.0.0.0'
            cabinet.save()
    except cabinet_cls.DoesNotExist:
        pass


def reverse(apps, editor_schema):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('apiv1', '0035_remove_device_instance_port'),
    ]

    operations = [
        migrations.RunPython(
            code=default_cabinet_ip_addr,
            reverse_code=reverse
        )
    ]
