# Generated by Django 2.1.7 on 2019-03-29 03:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apiv1', '0004_auto_20190326_1417'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='device_height',
            field=models.PositiveSmallIntegerField(null=True),
        ),
        migrations.AddField(
            model_name='device',
            name='device_width',
            field=models.PositiveSmallIntegerField(null=True),
        ),
    ]
