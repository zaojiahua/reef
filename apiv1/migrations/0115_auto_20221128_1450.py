# Generated by Django 2.2 on 2022-11-28 06:50

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apiv1', '0114_tboardstatisticsresult'),
    ]

    operations = [
        migrations.AddField(
            model_name='rds',
            name='end_method',
            field=models.IntegerField(blank=True, null=True, verbose_name='终点检测方式'),
        ),
        migrations.AddField(
            model_name='rds',
            name='fps',
            field=models.IntegerField(blank=True, null=True, verbose_name='实际帧率'),
        ),
        migrations.AddField(
            model_name='rds',
            name='frame_data',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, verbose_name='每帧数据'),
        ),
        migrations.AddField(
            model_name='rds',
            name='set_fps',
            field=models.IntegerField(blank=True, null=True, verbose_name='用户设置帧率'),
        ),
        migrations.AddField(
            model_name='rds',
            name='set_shot_time',
            field=models.FloatField(blank=True, null=True, verbose_name='用户设置时间'),
        ),
        migrations.AddField(
            model_name='rds',
            name='start_method',
            field=models.IntegerField(blank=True, null=True, verbose_name='起点检测方式'),
        ),
    ]