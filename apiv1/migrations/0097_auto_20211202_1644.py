# Generated by Django 2.2 on 2021-12-02 08:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apiv1', '0096_auto_20211201_1547'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobresourcefile',
            name='file',
            field=models.FileField(upload_to='job_resource_file', verbose_name='用例资源文件'),
        ),
    ]
