# Generated by Django 2.1.7 on 2019-04-13 13:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apiv1', '0010_auto_20190410_1038'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='ai_occupy',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='device',
            name='device_id',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='device',
            name='status',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]