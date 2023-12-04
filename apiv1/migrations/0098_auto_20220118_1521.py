# Generated by Django 2.2 on 2022-01-18 07:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('apiv1', '0097_auto_20211202_1644'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='devicecutcoordinate',
            name='desktop_x',
        ),
        migrations.RemoveField(
            model_name='devicecutcoordinate',
            name='desktop_y',
        ),
        migrations.RemoveField(
            model_name='devicecutcoordinate',
            name='menu_x',
        ),
        migrations.RemoveField(
            model_name='devicecutcoordinate',
            name='menu_y',
        ),
        migrations.RemoveField(
            model_name='devicecutcoordinate',
            name='outside_under_right_x',
        ),
        migrations.RemoveField(
            model_name='devicecutcoordinate',
            name='outside_under_right_y',
        ),
        migrations.RemoveField(
            model_name='devicecutcoordinate',
            name='outside_upper_left_x',
        ),
        migrations.RemoveField(
            model_name='devicecutcoordinate',
            name='outside_upper_left_y',
        ),
        migrations.RemoveField(
            model_name='devicecutcoordinate',
            name='return_x',
        ),
        migrations.RemoveField(
            model_name='devicecutcoordinate',
            name='return_y',
        ),
        migrations.AddField(
            model_name='phonemodel',
            name='height',
            field=models.FloatField(default=None, null=True, verbose_name='设备型号高度'),
        ),
        migrations.AddField(
            model_name='phonemodel',
            name='ply',
            field=models.FloatField(default=None, null=True, verbose_name='设备型号厚度'),
        ),
        migrations.AddField(
            model_name='phonemodel',
            name='width',
            field=models.FloatField(default=None, null=True, verbose_name='设备型号宽度'),
        ),
        migrations.CreateModel(
            name='PhoneModelCustomCoordinate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='属性名称')),
                ('x_coordinate', models.IntegerField(blank=True, null=True, verbose_name='x坐标')),
                ('y_coordinate', models.IntegerField(blank=True, null=True, verbose_name='y坐标')),
                ('z_coordinate', models.IntegerField(blank=True, default=0, null=True, verbose_name='z坐标')),
                ('is_fixed', models.BooleanField(default=True)),
                ('phone_model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='phonemodelcustomcoordinate', to='apiv1.PhoneModel', verbose_name='设备型号')),
            ],
            options={
                'verbose_name_plural': '机型自定义坐标',
                'unique_together': {('phone_model', 'name')},
            },
        ),
    ]
