# Generated by Django 2.2 on 2020-02-21 03:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apiv1', '0041_auto_20200102_1659'),
    ]

    operations = [
        migrations.AddField(
            model_name='tboard',
            name='is_to_delete',
            field=models.BooleanField(default=False, verbose_name='是否要被删除'),
        ),
    ]