# Generated by Django 2.2 on 2019-12-15 06:22

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('apiv1', '0037_auto_20191212_1742'),
    ]

    operations = [
        migrations.CreateModel(
            name='Unit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unit_name', models.CharField(max_length=50, unique=True, verbose_name='unit名称')),
                ('unit_content', django.contrib.postgres.fields.jsonb.JSONField(max_length=800, verbose_name='unit的内容')),
                ('type', models.CharField(max_length=50, verbose_name='unit所属类型')),
            ],
            options={
                'verbose_name_plural': '用例执行单元',
            },
        ),
        migrations.AddField(
            model_name='job',
            name='ui_json_file',
            field=models.FileField(default='', upload_to='ui_json', verbose_name='job编辑完成之后生成的uijson文件'),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='JobResourceFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('type', models.CharField(max_length=50)),
                ('file', models.FileField(upload_to='job_resource_file')),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job_res_file', to='apiv1.Job')),
            ],
            options={
                'verbose_name_plural': '用例资源文件',
                'unique_together': {('job', 'name')},
            },
        ),
    ]