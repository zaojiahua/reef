# Generated by Django 2.1.7 on 2019-04-17 09:02

from django.db import migrations


def check_calculated_field(apps, schema_editor):
    pass


def reverse(apps, editor_schema):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('apiv1', '0011_auto_20190413_2126'),
    ]

    operations = [
        migrations.RunPython(
            code=check_calculated_field,
            reverse_code=reverse
        )
    ]