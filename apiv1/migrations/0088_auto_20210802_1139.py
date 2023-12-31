# Generated by Django 2.2 on 2021-08-02 03:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apiv1', '0087_bug_level'),
    ]

    operations = [
        migrations.AlterField(
            model_name='device',
            name='auto_test',
            field=models.BooleanField(default=False, verbose_name='系统是否自动分派任务给该设备'),
        ),
        migrations.AlterField(
            model_name='tboard',
            name='tboard_type',
            field=models.CharField(choices=[('Joblib', 'Joblib'), ('PerfJob', 'PerfJob'), ('PriorJob', 'PriorJob')], default='Joblib', max_length=20, verbose_name='tboard分类'),
        ),
    ]
