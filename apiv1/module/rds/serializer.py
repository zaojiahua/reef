from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import APIException
from rest_framework.fields import JSONField

from apiv1.core.constants import JOB_RESOURCE_FILE_TYPE
from apiv1.core.response import reef_400_response
from apiv1.module.device.models import Device, PhoneModel, RomVersion
from apiv1.module.job.models import Job
from apiv1.module.rds.models import Rds, RdsLog, RdsScreenShot
from apiv1.module.tboard.models import TBoard


class RdsSerializer(serializers.ModelSerializer):
    """
    Generic Serializer
    """
    rds_dict = JSONField(binary=True)

    class Meta:
        model = Rds
        fields = '__all__'


class RdsLogSerializer(serializers.ModelSerializer):
    """
    Generic Serializer
    """

    class Meta:
        model = RdsLog
        fields = '__all__'


class RdsScreenShotSerializer(serializers.ModelSerializer):
    """
    Generic Serializer
    """
    class Meta:
        model = RdsScreenShot
        fields = '__all__'


class RdsCreateOrUpdateSerializer(serializers.ModelSerializer):
    device = serializers.SlugRelatedField(
        queryset=Device.objects.all(),
        slug_field='device_label'
    )
    job = serializers.SlugRelatedField(
        queryset=Job.objects.all(),
        slug_field='job_label'
    )
    start_time = serializers.DateTimeField(
        input_formats=['%Y_%m_%d_%H_%M_%S']
    )
    end_time = serializers.DateTimeField(
        required=False,
        input_formats=['%Y_%m_%d_%H_%M_%S']
    )
    tboard = serializers.SlugRelatedField(
        queryset=TBoard.objects.all(),
        slug_field='id'
    )
    rds_dict = serializers.JSONField(
        required=False,
        binary=True
    )
    typical_job_temp_consumption = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False
    )
    job_duration = serializers.FloatField(
        required=False,
        min_value=0
    )
    original_job_duration = serializers.FloatField(
        required=False,
        min_value=0
    )
    phone_model = serializers.SlugRelatedField(
        queryset=PhoneModel.objects.all(),
        slug_field='phone_model_name',
        required=False
    )
    rom_version = serializers.SlugRelatedField(
        queryset=RomVersion.objects.all(),
        slug_field='version',
        required=False
    )
    start_point = serializers.IntegerField(min_value=0, required=False)
    end_point = serializers.IntegerField(min_value=1, required=False)
    ads_start_point = serializers.IntegerField(min_value=0, required=False)
    ads_end_point = serializers.IntegerField(min_value=1, required=False)
    picture_count = serializers.IntegerField(min_value=1, required=False)
    time_per_unit = serializers.FloatField(min_value=0, required=False)
    rom_version_const = serializers.CharField(required=False)
    app_info = serializers.JSONField(
        required=False,
        binary=True
    )
    start_method = serializers.IntegerField(required=False)
    end_method = serializers.IntegerField(required=False)
    set_fps = serializers.IntegerField(min_value=1, required=False)
    set_shot_time = serializers.FloatField(min_value=0, required=False)
    fps = serializers.IntegerField(min_value=1, required=False)
    frame_data = serializers.JSONField(
        required=False,
        binary=True
    )

    # =======================================================
    class Meta:
        model = Rds
        fields = ('device', 'job', 'start_time', 'end_time', 'tboard', 'rds_dict', 'job_assessment_value',
                  'typical_job_temp_consumption', 'job_duration', 'original_job_duration', 'phone_model', 'filter',
                  'rom_version', 'start_point', 'end_point', 'ads_start_point', 'ads_end_point', 'picture_count', 'time_per_unit',
                  'lose_frame_point', 'rom_version_const', 'app_info', 'start_method', 'end_method',
                  'set_fps', 'set_shot_time', 'fps', 'frame_data')


class UploadRdsLogSerializer(serializers.Serializer):
    """
    Coral上传RdsLog的接口
    """
    job = serializers.SlugRelatedField(
        queryset=Job.objects.all(),
        slug_field='job_label',
    )
    device = serializers.SlugRelatedField(
        queryset=Device.objects.all(),
        slug_field='device_label',
    )
    start_time = serializers.DateTimeField(input_formats=['%Y_%m_%d_%H_%M_%S'])
    log_file = serializers.FileField()
    file_name = serializers.CharField(max_length=100)


class UploadScreenShotSerializer(serializers.Serializer):
    """
    Coral创建Rds截图的接口
    """
    device = serializers.SlugRelatedField(
        write_only=True,
        queryset=Device.objects.all(),
        slug_field='device_label',
    )
    job = serializers.SlugRelatedField(
        write_only=True,
        queryset=Job.objects.all(),
        slug_field='job_label'
    )
    start_time = serializers.DateTimeField(write_only=True, input_formats=['%Y_%m_%d_%H_%M_%S'])
    rds_screen_shot = serializers.FileField(write_only=True)
    file_name = serializers.CharField(max_length=100)


class GetRdsStatisticsDataSerializer(serializers.Serializer):

    device = serializers.SlugRelatedField(
        queryset=Device.objects.all(),
        slug_field='device_label',
        required=False
    )
    job = serializers.SlugRelatedField(
        queryset=Job.objects.all(),
        slug_field='job_label',
        required=False
    )
    tboard = serializers.SlugRelatedField(
        queryset= TBoard.objects.all(),
        slug_field='id',
        required=False
    )


class SortRdsScreenShotSerializer(serializers.Serializer):

    rds = serializers.PrimaryKeyRelatedField(
        queryset=Rds.objects.all()
    )

    reverse = serializers.BooleanField(
        required=False,
        default=False
    )


class FilterInvalidRdsSerializer(serializers.Serializer):

    job_id = serializers.PrimaryKeyRelatedField(
        queryset=Job.objects.filter(job_deleted=False),
        required=False
    )

    device_id = serializers.PrimaryKeyRelatedField(
        queryset=Device.objects.all(),
        required=False
    )

    tboard_id = serializers.PrimaryKeyRelatedField(
        queryset=TBoard.objects.all()
    )

    reverse = serializers.BooleanField(
        default=False,
        required=False
    )


class RdsScreenShotFileMultiUploadSerializer(serializers.Serializer):

    files = serializers.ListField(child=serializers.FileField())
    rds = serializers.PrimaryKeyRelatedField(queryset=Rds.objects.all())
    is_resource_file = serializers.BooleanField(default=True, required=False)

    def create(self, validated_data):
        res_list = []
        res_obj = validated_data['rds']
        is_resource_file = validated_data.get('is_resource_file', True)
        try:
            with transaction.atomic():
                for f in validated_data['files']:
                    # 上传文件名为中文时，获取filename后面会多出一个' " '，django处理源码在django.http.multipartparser.py(664行)
                    # 此问题django已修复，但未合并到2.2版本，具体可见: https://code.djangoproject.com/ticket/31293，
                    # 相关连接 https://tools.ietf.org/html/rfc2231#section-4.1
                    file_name = f.name[:-1] if f.name[-1] == '"' else f.name

                    # 验证上传的文件格式
                    file_type = file_name.split('.')[-1]
                    if file_type not in JOB_RESOURCE_FILE_TYPE:
                        raise serializers.ValidationError('Upload file format is incorrect')
                    rds_screen_shot_data = {
                        'file_name': file_name,
                        'img_file': f,
                        'rds': res_obj
                    }
                    if is_resource_file:
                        rds_screen_shot_data['is_resource_file'] = is_resource_file

                    instance = RdsScreenShot.objects.create(
                       **rds_screen_shot_data
                    )
                    res = RdsScreenShotSerializer(instance)
                    res_list.append(res.data)
        except Exception as e:
            reef_400_response(description='上传文件失败！！！', message=f"Exception info: {e}")
        return {"file_list": res_list}


class UploadCoolPadPowerLastSerializer(serializers.Serializer):

    tboard = serializers.PrimaryKeyRelatedField(
        queryset=TBoard.objects.filter(is_to_delete=False)
    )

    device = serializers.PrimaryKeyRelatedField(
        queryset=Device.objects.filter()
    )

    standby_time = serializers.IntegerField(
        min_value=0
    )
