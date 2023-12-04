# Generated by Django 2.2 on 2021-04-23 01:54

from django.conf import settings
import django.contrib.postgres.fields.jsonb
import django.contrib.postgres.indexes
from django.db import migrations, models
import django.db.models.deletion


# Functions from the following migrations need manual copying.
# Move them and any dependencies into this file, then update the
# RunPython operations to refer to the local versions:
# apiv1.migrations.0067_auto_20201222_1810
from apiv1.core.constants import REEF_DEFAULT_USER


def job_author_null_to_default_user(apps, schema_editor):
    Job = apps.get_model('apiv1', 'Job')
    ReefUser = apps.get_model('apiv1', 'ReefUser')
    default_user = ReefUser.objects.get(username=REEF_DEFAULT_USER)
    Job.objects.filter(author__isnull=True).update(author=default_user.id)
    return


def reverse(apps, editor_schema):
    pass

class Migration(migrations.Migration):

    replaces = [('apiv1', '0063_auto_20200828_1902'), ('apiv1', '0064_auto_20200919_1004'), ('apiv1', '0065_auto_20200924_1500'), ('apiv1', '0066_auto_20201207_1157'), ('apiv1', '0067_auto_20201222_1810'), ('apiv1', '0068_auto_20210104_1613'), ('apiv1', '0069_auto_20210120_1026'), ('apiv1', '0070_auto_20210120_1101'), ('apiv1', '0071_auto_20210329_1115'), ('apiv1', '0072_auto_20210329_1135')]

    dependencies = [
        ('apiv1', '0062_job_inner_job'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='job_second_type',
            field=models.CharField(blank=True, choices=[('TimeJob', 'TimeJob')], max_length=10, null=True, verbose_name='用例二级分类'),
        ),
        migrations.AddField(
            model_name='rds',
            name='job_duration',
            field=models.FloatField(blank=True, null=True, verbose_name='job执行耗时'),
        ),
        migrations.AddField(
            model_name='rds',
            name='phone_model',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='rds', to='apiv1.PhoneModel', verbose_name='设备型号'),
        ),
        migrations.AddField(
            model_name='rds',
            name='rom_version',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='rds', to='apiv1.RomVersion', verbose_name='设备系统版本号'),
        ),
        migrations.AddField(
            model_name='tboard',
            name='tboard_second_type',
            field=models.CharField(blank=True, choices=[('TimeJob', 'TimeJob')], max_length=15, null=True, verbose_name='tboard二级分类'),
        ),
        migrations.AddField(
            model_name='tboard',
            name='tboard_type',
            field=models.CharField(choices=[('Joblib', 'Joblib'), ('PerfJob', 'PerfJob')], default='Joblib', max_length=20, verbose_name='tboard分类'),
        ),
        migrations.AlterField(
            model_name='job',
            name='job_type',
            field=models.CharField(choices=[('UnKnow', 'UnKnow'), ('Sysjob', 'Sysjob'), ('Joblib', 'Joblib'), ('PerfJob', 'PerfJob'), ('Uniq', 'Uniq'), ('InnerJob', 'InnerJob')], max_length=10, verbose_name='用例类型'),
        ),
        migrations.AlterField(
            model_name='abnormitydetail',
            name='describe',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='描述'),
        ),
        migrations.CreateModel(
            name='SubsidiaryDevice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('describe', models.CharField(blank=True, max_length=100, null=True, verbose_name='描述')),
                ('serial_number', models.CharField(max_length=200, unique=True, verbose_name='设备串口号')),
                ('ip_address', models.CharField(max_length=50, verbose_name='ip地址')),
                ('order', models.SmallIntegerField(verbose_name='相对于主设备的编号')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否有效')),
                ('devices', models.ManyToManyField(related_name='subsidiarydevice', to='apiv1.Device', verbose_name='关联主设备')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='device',
            name='subsidiary_device_count',
            field=models.SmallIntegerField(default=0, verbose_name='设备附属设备数量'),
        ),
        migrations.AddField(
            model_name='job',
            name='subsidiary_device_count',
            field=models.SmallIntegerField(default=0, verbose_name='job需要附属设备数量'),
        ),
        migrations.AlterField(
            model_name='job',
            name='job_type',
            field=models.CharField(choices=[('UnKnow', 'UnKnow'), ('Sysjob', 'Sysjob'), ('Joblib', 'Joblib'), ('PerfJob', 'PerfJob'), ('Uniq', 'Uniq'), ('InnerJob', 'InnerJob'), ('MultiDevice', 'MultiDevice')], max_length=10, verbose_name='用例类型'),
        ),
        migrations.AddField(
            model_name='job',
            name='case_number',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='中科创达用例编号'),
        ),
        migrations.AddField(
            model_name='job',
            name='priority',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='中科创达用例的级别'),
        ),
        migrations.AlterField(
            model_name='job',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='job', to=settings.AUTH_USER_MODEL, verbose_name='用户'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='tboard',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='tboard', to=settings.AUTH_USER_MODEL, verbose_name='用户'),
        ),
        migrations.AddField(
            model_name='device',
            name='matching_rule',
            field=django.contrib.postgres.fields.jsonb.JSONField(null=True, verbose_name='device匹配job规则'),
        ),
        migrations.AddField(
            model_name='job',
            name='matching_rule',
            field=django.contrib.postgres.fields.jsonb.JSONField(null=True, verbose_name='job匹配device规则'),
        ),
        migrations.AddIndex(
            model_name='device',
            index=django.contrib.postgres.indexes.GinIndex(fields=['matching_rule'], name='apiv1_devic_matchin_b10638_gin'),
        ),
        migrations.AddField(
            model_name='job',
            name='flow_execute_mode',
            field=models.CharField(choices=[('SingleSplit', 'SingleSplit'), ('MultiSet', 'MultiSet')], default='SingleSplit', max_length=50, verbose_name='job执行流执行模式'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='jobresourcefile',
            name='job',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='job_res_file', to='apiv1.Job', verbose_name='用例'),
        ),
        migrations.CreateModel(
            name='JobFlow',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='用例执行流名称')),
                ('flow_type', models.CharField(choices=[('NormalFlow', 'NormalFlow'), ('InnerFlow', 'InnerFlow')], max_length=10, verbose_name='用例执行流类型')),
                ('ui_json_file', models.FileField(upload_to='ui_json_file', verbose_name='用例执行流文件')),
                ('order', models.IntegerField(verbose_name='用例执行流顺序')),
                ('description', models.TextField(blank=True, verbose_name='用例执行流描述')),
                ('inner_flow', models.ManyToManyField(blank=True, related_name='job_flow', to='apiv1.JobFlow')),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job_flow', to='apiv1.Job', verbose_name='用例')),
            ],
            options={
                'verbose_name_plural': '用例执行流',
                'unique_together': {('job', 'name'), ('job', 'order')},
            },
        ),
        migrations.AddField(
            model_name='jobresourcefile',
            name='job_flow',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='job_res_file', to='apiv1.JobFlow', verbose_name='用例执行流'),
        ),
        migrations.AlterUniqueTogether(
            name='jobresourcefile',
            unique_together={('job_flow', 'name')},
        ),
        migrations.AlterField(
            model_name='rdslog',
            name='file_name',
            field=models.CharField(max_length=100, verbose_name='测试结果日志文件名称'),
        ),
        migrations.AlterField(
            model_name='rdsscreenshot',
            name='file_name',
            field=models.CharField(max_length=100, verbose_name='测试结果截图名称'),
        ),
        migrations.RunPython(
            code=job_author_null_to_default_user,
            reverse_code=reverse
        ),
    ]
