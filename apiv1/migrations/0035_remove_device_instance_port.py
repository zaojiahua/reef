# Generated by Django 2.2 on 2019-12-06 03:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apiv1', '0034_change_default_manufactur'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='device',
            name='instance_port',
        ),
    ]
