# Generated by Django 2.1.7 on 2019-06-10 08:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apiv1', '0018_data_migration_for_0017'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='androidversion',
            options={'verbose_name_plural': '安卓版本'},
        ),
        migrations.AlterModelOptions(
            name='cabinet',
            options={'verbose_name_plural': '机柜'},
        ),
        migrations.AlterModelOptions(
            name='customtag',
            options={'verbose_name_plural': '自定义标签'},
        ),
        migrations.AlterModelOptions(
            name='device',
            options={'verbose_name_plural': '装置'},
        ),
        migrations.AlterModelOptions(
            name='devicechangehistory',
            options={'verbose_name_plural': '装置变更历程'},
        ),
        migrations.AlterModelOptions(
            name='devicecoordinate',
            options={'verbose_name_plural': '装置角点坐标'},
        ),
        migrations.AlterModelOptions(
            name='devicepower',
            options={'verbose_name_plural': '装置电量'},
        ),
        migrations.AlterModelOptions(
            name='devicescreenshot',
            options={'verbose_name_plural': '装置页面截图'},
        ),
        migrations.AlterModelOptions(
            name='devicetemperature',
            options={'verbose_name_plural': '装置温度'},
        ),
        migrations.AlterModelOptions(
            name='job',
            options={'verbose_name_plural': '用例'},
        ),
        migrations.AlterModelOptions(
            name='jobassessment',
            options={'verbose_name_plural': '任务测试评分'},
        ),
        migrations.AlterModelOptions(
            name='jobtestarea',
            options={'verbose_name_plural': '测试用途'},
        ),
        migrations.AlterModelOptions(
            name='manufacturer',
            options={'verbose_name_plural': '制造商'},
        ),
        migrations.AlterModelOptions(
            name='monitorport',
            options={'verbose_name_plural': '相机编号'},
        ),
        migrations.AlterModelOptions(
            name='phonemodel',
            options={'verbose_name_plural': '装置型号'},
        ),
        migrations.AlterModelOptions(
            name='powerport',
            options={'verbose_name_plural': '电量端口'},
        ),
        migrations.AlterModelOptions(
            name='rds',
            options={'verbose_name_plural': '测试结果'},
        ),
        migrations.AlterModelOptions(
            name='rdslog',
            options={'verbose_name_plural': '测试结果日志文件'},
        ),
        migrations.AlterModelOptions(
            name='rdsscreenshot',
            options={'verbose_name_plural': '测试结果截图'},
        ),
        migrations.AlterModelOptions(
            name='reefuser',
            options={'verbose_name_plural': '系统用户'},
        ),
        migrations.AlterModelOptions(
            name='romversion',
            options={'verbose_name_plural': '装置系统版本号'},
        ),
        migrations.AlterModelOptions(
            name='system',
            options={'verbose_name_plural': '系统'},
        ),
        migrations.AlterModelOptions(
            name='tboard',
            options={'verbose_name_plural': '任务'},
        ),
        migrations.AlterModelOptions(
            name='tempport',
            options={'verbose_name_plural': '温度端口'},
        ),
    ]
