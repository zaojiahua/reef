# Generated by Django 2.1.7 on 2019-06-26 02:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apiv1', '0020_auto_20190611_1050'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='devicechangehistory',
            name='device',
        ),
        migrations.RemoveField(
            model_name='job',
            name='job_assessment',
        ),
        migrations.DeleteModel(
            name='DeviceChangeHistory',
        ),
        migrations.DeleteModel(
            name='JobAssessment',
        ),
    ]
