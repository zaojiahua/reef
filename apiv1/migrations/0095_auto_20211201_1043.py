# Generated by Django 2.2 on 2021-12-01 02:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apiv1', '0094_auto_20211119_1446'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobresourcefile',
            name='file',
            field=models.FileField(upload_to='job_resource_file/%Y_%m_%d', verbose_name='用例资源文件'),
        ),
        migrations.AlterField(
            model_name='rdslog',
            name='log_file',
            field=models.FileField(upload_to='rds_logs/%Y_%m_%d', verbose_name='测试结果日志文件'),
        ),
        migrations.AlterField(
            model_name='rdsscreenshot',
            name='img_file',
            field=models.ImageField(upload_to='screen_shot/%Y_%m_%d', verbose_name='测试结果截图'),
        ),
        migrations.AlterField(
            model_name='rdsscreenshot',
            name='thumbs_file',
            field=models.ImageField(blank=True, null=True, upload_to='screen_shot/%Y_%m_%d', verbose_name='测试结果截压缩图'),
        ),
    ]
