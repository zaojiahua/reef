# Generated by Django 2.2 on 2021-06-02 02:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apiv1', '0080_auto_20210526_0953'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subsidiarydevice',
            name='custom_name',
            field=models.CharField(max_length=50, null=True),
        ),
    ]