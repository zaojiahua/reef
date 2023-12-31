# Generated by Django 2.1.7 on 2019-03-15 11:41
import django.contrib.auth.models
import django.contrib.auth.validators
import django.contrib.postgres.fields.jsonb
import django.utils.timezone
from django.conf import settings
from django.contrib.auth.models import Group
from django.db import migrations, models
from django.utils import timezone

from apiv1.core.constants import REEF_DEFAULT_MANUFACTURER, REEF_DEFAULT_USER, REEF_ADMIN_GROUP_NAME, \
    REEF_MANAGER_GROUP_NAME, REEF_DATA_VIEWER_GROUP_NAME, REEF_TEST_OPERATOR_GROUP_NAME
from apiv1.module.device.models import Manufacturer
from apiv1.module.user.models import ReefUser
from apiv1.module.system.models import System, Cabinet
from apiv1.module.tboard.models import get_tboard_default_name


def create_default_data(apps, schema_editor):
    system = System.objects.create(
        system_name='System{}'.format(timezone.now().strftime('%y%m%d%H%M%S%f')),
        ip_address='192.168.1.100'
    )
    # Cabinet.objects.create(
    #     cabinet_name='cabinet_name_0',
    #     belong_to=system
    # )
    Manufacturer.objects.create(manufacturer_name=REEF_DEFAULT_MANUFACTURER)

    ReefUser.objects.create(username=REEF_DEFAULT_USER)

    admin_user: ReefUser = ReefUser.objects.create_user('admin', None, 'admin',
                                                        is_superuser=True, is_staff=True)
    admin_group = Group.objects.create(name=REEF_ADMIN_GROUP_NAME)
    manager_group = Group.objects.create(name=REEF_MANAGER_GROUP_NAME)
    data_viewer_group = Group.objects.create(name=REEF_DATA_VIEWER_GROUP_NAME)
    test_operator_group = Group.objects.create(name=REEF_TEST_OPERATOR_GROUP_NAME)

    admin_user.groups.add(admin_group)
    admin_user.groups.add(manager_group)
    admin_user.groups.add(data_viewer_group)
    admin_user.groups.add(test_operator_group)


def reverse(apps, editor_schema):
    pass


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('auth', '0009_alter_user_last_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReefUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False,
                                                     help_text='Designates that this user has all permissions without explicitly assigning them.',
                                                     verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'},
                                              help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
                                              max_length=150, unique=True,
                                              validators=[django.contrib.auth.validators.UnicodeUsernameValidator()],
                                              verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False,
                                                 help_text='Designates whether the user can log into this admin site.',
                                                 verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True,
                                                  help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.',
                                                  verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('groups', models.ManyToManyField(blank=True,
                                                  help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
                                                  related_name='user_set', related_query_name='user', to='auth.Group',
                                                  verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.',
                                                            related_name='user_set', related_query_name='user',
                                                            to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='AndroidVersion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Cabinet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cabinet_name', models.CharField(max_length=50)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CustomTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('custom_tag_name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('device_label', models.CharField(db_index=True, max_length=50, unique=True)),
                ('device_name', models.CharField(default='Device', max_length=50)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('cpu_id', models.CharField(max_length=50)),
                ('start_time_key', models.CharField(blank=True, max_length=50, null=True)),
                ('android_version',
                 models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                   related_name='device', to='apiv1.AndroidVersion')),
                ('cabinet', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                              related_name='cabinet', to='apiv1.Cabinet')),
            ],
        ),
        migrations.CreateModel(
            name='DeviceChangeHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('device_label', models.CharField(max_length=50)),
                ('device_name', models.CharField(default='Device', max_length=50)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('cpu_id', models.CharField(blank=True, max_length=50, null=True)),
                ('rom_version_id', models.PositiveIntegerField(blank=True, null=True)),
                ('start_time_key', models.CharField(blank=True, max_length=50, null=True)),
                ('power_port', models.CharField(blank=True, max_length=50, null=True)),
                ('temp_port', models.CharField(blank=True, max_length=50, null=True)),
                ('device_created_time', models.DateTimeField(blank=True, null=True)),
                ('device_updated_time', models.DateTimeField(blank=True, null=True)),
                ('cabinet_id', models.PositiveIntegerField(blank=True, null=True)),
                ('cabinet_cabinet_name', models.CharField(blank=True, max_length=50, null=True)),
                ('cabinet_ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('cabinet_created_time', models.DateTimeField(blank=True, null=True)),
                ('cabinet_updated_time', models.DateTimeField(blank=True, null=True)),
                ('system_id', models.PositiveIntegerField(blank=True, null=True)),
                ('system_system_name', models.CharField(max_length=50)),
                ('system_created_time', models.DateTimeField(blank=True, null=True)),
                ('system_updated_time', models.DateTimeField(blank=True, null=True)),
                ('android_version_id', models.PositiveIntegerField(blank=True, null=True)),
                ('android_version_code_name', models.CharField(blank=True, max_length=50, null=True)),
                ('android_version_version', models.CharField(blank=True, max_length=50, null=True)),
                ('android_version_build', models.CharField(blank=True, max_length=50, null=True)),
                ('android_version_branch', models.CharField(blank=True, max_length=50, null=True)),
                ('android_version_api_level', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('android_version_created_time', models.DateTimeField(blank=True, null=True)),
                ('android_version_time', models.DateTimeField(blank=True, null=True)),
                ('phone_model_id', models.PositiveIntegerField(blank=True, null=True)),
                ('phone_model_phone_model_name', models.CharField(blank=True, max_length=50, null=True)),
                ('phone_model_cpu_name', models.CharField(blank=True, max_length=50, null=True)),
                ('phone_model_created_time', models.DateTimeField(blank=True, null=True)),
                ('phone_model_updated_time', models.DateTimeField(blank=True, null=True)),
                ('manufacturer_id', models.PositiveIntegerField(blank=True, null=True)),
                ('manufacturer_manufacturer_name', models.CharField(blank=True, max_length=50, null=True)),
                ('manufacturer_created_time', models.DateTimeField(blank=True, null=True)),
                ('manufacturer_updated_time', models.DateTimeField(blank=True, null=True)),
                ('device',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='devicechangehistory',
                                   to='apiv1.Device')),
            ],
        ),
        migrations.CreateModel(
            name='DeviceCoordinate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('upper_left_x', models.PositiveSmallIntegerField()),
                ('upper_left_y', models.PositiveSmallIntegerField()),
                ('upper_right_x', models.PositiveSmallIntegerField()),
                ('upper_right_y', models.PositiveSmallIntegerField()),
                ('bottom_left_x', models.PositiveSmallIntegerField()),
                ('bottom_left_y', models.PositiveSmallIntegerField()),
                ('bottom_right_x', models.PositiveSmallIntegerField()),
                ('bottom_right_y', models.PositiveSmallIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='DevicePower',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('record_datetime', models.DateTimeField(default=django.utils.timezone.now)),
                ('battery_level', models.PositiveSmallIntegerField()),
                ('charging', models.BooleanField()),
                ('battery_file', models.FileField(upload_to='device')),
                ('cabinet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='devicepower',
                                              to='apiv1.Cabinet')),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='devicepower',
                                             to='apiv1.Device')),
            ],
        ),
        migrations.CreateModel(
            name='DeviceScreenshot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('snap_timestamp', models.DateTimeField()),
                ('screenshot', models.ImageField(upload_to='device_screenshot')),
                ('device',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='devicescreenshot',
                                   to='apiv1.Device')),
            ],
        ),
        migrations.CreateModel(
            name='DeviceTemperature',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=50)),
                ('record_datetime', models.DateTimeField(default=django.utils.timezone.now)),
                ('temperature', models.DecimalField(decimal_places=2, max_digits=5)),
                ('cabinet',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='devicetemperature',
                                   to='apiv1.Cabinet')),
                ('device',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='devicetemperature',
                                   to='apiv1.Device')),
            ],
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('job_label', models.CharField(db_index=True, max_length=50, unique=True)),
                ('job_name', models.CharField(max_length=50)),
                ('job_type',
                 models.CharField(choices=[('UnKnow', 'UnKnow'), ('Sysjob', 'Sysjob'), ('Joblib', 'Joblib')],
                                  max_length=10)),
                ('description', models.TextField(blank=True)),
                ('job_deleted', models.BooleanField(default=False)),
                ('android_version', models.ManyToManyField(related_name='job', to='apiv1.AndroidVersion')),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                             related_name='job', to=settings.AUTH_USER_MODEL)),
                ('custom_tag', models.ManyToManyField(related_name='job', to='apiv1.CustomTag')),
            ],
        ),
        migrations.CreateModel(
            name='JobAssessment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('value_type', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='JobTestArea',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField(db_index=True, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Manufacturer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('manufacturer_name', models.CharField(db_index=True, max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='MonitorPort',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('port', models.CharField(db_index=True, max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='PhoneModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_model_name', models.CharField(db_index=True, max_length=50, unique=True)),
                ('cpu_name', models.CharField(blank=True, max_length=50, null=True)),
                ('manufacturer',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='phonemodel',
                                   to='apiv1.Manufacturer')),
            ],
        ),
        migrations.CreateModel(
            name='PowerPort',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('port', models.CharField(db_index=True, max_length=50, unique=True)),
                ('device', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                                related_name='powerport', to='apiv1.Device')),
            ],
        ),
        migrations.CreateModel(
            name='Rds',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('end_time', models.DateTimeField(blank=True, null=True)),
                ('job_assessment_value', models.CharField(blank=True, default='', max_length=50)),
                ('rds_dict', django.contrib.postgres.fields.jsonb.JSONField(null=True)),
                ('device',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rds', to='apiv1.Device')),
                ('job',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rds', to='apiv1.Job')),
            ],
        ),
        migrations.CreateModel(
            name='RdsLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('log_file', models.FileField(upload_to='rds_logs')),
                ('file_name', models.CharField(max_length=50)),
                ('rds',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rdslog', to='apiv1.Rds')),
            ],
        ),
        migrations.CreateModel(
            name='RdsScreenShot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('img_file', models.ImageField(upload_to='screen_shot')),
                ('thumbs_file', models.ImageField(blank=True, null=True, upload_to='screen_shot')),
                ('file_name', models.CharField(max_length=50)),
                ('rds', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rdsscreenshot',
                                          to='apiv1.Rds')),
            ],
        ),
        migrations.CreateModel(
            name='RomVersion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.CharField(max_length=50, unique=True)),
                ('manufacturer',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='romversion',
                                   to='apiv1.Manufacturer')),
            ],
        ),
        migrations.CreateModel(
            name='System',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('system_name', models.CharField(max_length=50)),
                ('ip_address', models.GenericIPAddressField()),
            ],
        ),
        migrations.CreateModel(
            name='TBoard',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('repeat_time', models.PositiveSmallIntegerField(default=1)),
                ('board_name', models.CharField(default=get_tboard_default_name, max_length=50)),
                ('finished_flag', models.BooleanField(default=False)),
                ('board_stamp', models.DateTimeField(db_index=True, unique=True)),
                ('end_time', models.DateTimeField(null=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tboard',
                                             to=settings.AUTH_USER_MODEL)),
                ('device', models.ManyToManyField(related_name='tboard', to='apiv1.Device')),
                ('job', models.ManyToManyField(related_name='tboard', to='apiv1.Job')),
            ],
        ),
        migrations.CreateModel(
            name='TempPort',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('port', models.CharField(db_index=True, max_length=50, unique=True)),
                ('description', models.CharField(max_length=50, null=True)),
                ('device', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                             related_name='tempport', to='apiv1.Device')),
            ],
        ),
        migrations.AddField(
            model_name='rds',
            name='tboard',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='rds', to='apiv1.TBoard'),
        ),
        migrations.AddField(
            model_name='job',
            name='job_assessment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='job', to='apiv1.JobAssessment'),
        ),
        migrations.AddField(
            model_name='job',
            name='phone_models',
            field=models.ManyToManyField(related_name='job', to='apiv1.PhoneModel'),
        ),
        migrations.AddField(
            model_name='job',
            name='rom_version',
            field=models.ManyToManyField(related_name='job', to='apiv1.RomVersion'),
        ),
        migrations.AddField(
            model_name='job',
            name='test_area',
            field=models.ManyToManyField(related_name='job', to='apiv1.JobTestArea'),
        ),
        migrations.AddField(
            model_name='devicetemperature',
            name='temp_port',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='devicetemperature',
                                    to='apiv1.TempPort'),
        ),
        migrations.AddField(
            model_name='devicepower',
            name='power_port',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='devicepower',
                                    to='apiv1.PowerPort'),
        ),
        migrations.AddField(
            model_name='device',
            name='coordinate',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                       related_name='device', to='apiv1.DeviceCoordinate'),
        ),
        migrations.AddField(
            model_name='device',
            name='monitor_index',
            field=models.ManyToManyField(related_name='device', to='apiv1.MonitorPort'),
        ),
        migrations.AddField(
            model_name='device',
            name='phone_model',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='device', to='apiv1.PhoneModel'),
        ),
        migrations.AddField(
            model_name='device',
            name='rom_version',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='device',
                                    to='apiv1.RomVersion'),
        ),
        migrations.AddField(
            model_name='cabinet',
            name='belong_to',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='cabinet',
                                    to='apiv1.System'),
        ),
        migrations.AddField(
            model_name='cabinet',
            name='create_time',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间'),
        ),
        migrations.AddField(
            model_name='cabinet',
            name='is_delete',
            field=models.BooleanField(default=False, verbose_name='机柜是否移除'),
        ),
        migrations.AddField(
            model_name='cabinet',
            name='update_time',
            field=models.DateTimeField(auto_now=True, verbose_name='更新时间'),
        ),
        migrations.RunPython(
            code=create_default_data,
            reverse_code=reverse
        )
    ]
