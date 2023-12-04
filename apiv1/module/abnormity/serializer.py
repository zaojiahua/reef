from django.db import transaction
from rest_framework import serializers

from apiv1.core.constants import JOB_RESOURCE_FILE_TYPE
from apiv1.core.response import reef_400_response
from apiv1.module.abnormity.models import AbnormityType, AbnormityPolicy, Abnormity, AbnormityDetail, AbnormityLog
from apiv1.module.device.models import Device
from apiv1.module.tboard.models import TBoard
from apiv1.module.device.serializer import DeviceSerializer


class BaseAbnormityTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = AbnormityType
        fields = '__all__'


class AbnormityPolicySerializer(serializers.ModelSerializer):

    class Meta:
        model = AbnormityPolicy
        fields = '__all__'


class AbnormitySerializer(serializers.ModelSerializer):

    class Meta:
        model = Abnormity
        fields = '__all__ '


class AbnormityDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = AbnormityDetail
        fields = '__all__ '


class GetAbnormityCountSerializer(serializers.Serializer):

    devices = serializers.PrimaryKeyRelatedField(
        queryset=Device.objects.all(),
        many=True,
        required=False
    )
    tboard = serializers.PrimaryKeyRelatedField(
        queryset=TBoard.objects.all(),
        required=False
    )
    start_time = serializers.DateTimeField(
        input_formats=['%Y_%m_%d_%H_%M_%S', '%Y-%m-%d %H:%M:%S'],
        required=False
    )
    end_time = serializers.DateTimeField(
        input_formats=['%Y_%m_%d_%H_%M_%S', '%Y-%m-%d %H:%M:%S'],
        required=False
    )


class AbnormityListSerializer(serializers.Serializer):

    abnormity_type = serializers.SlugRelatedField(
        slug_field='code',
        queryset=AbnormityType.objects.filter(is_active=True)
    )
    start_time = serializers.DateTimeField(
        input_formats=['%Y_%m_%d_%H_%M_%S', '%Y-%m-%d %H:%M:%S'],
        required=False
    )
    end_time = serializers.DateTimeField(
        input_formats=['%Y_%m_%d_%H_%M_%S', '%Y-%m-%d %H:%M:%S'],
        required=False
    )
    devices = serializers.PrimaryKeyRelatedField(
        queryset=Device.objects.all(),
        required=False,
        many=True,
    )
    tboard = serializers.PrimaryKeyRelatedField(
        queryset=TBoard.objects.all(),
        required=False
    )


class PowerAbnormityChartSerializer(serializers.Serializer):

    abnormity = serializers.PrimaryKeyRelatedField(
        queryset=Abnormity.objects.all()
    )


class GetAbnormityDetailData(serializers.Serializer):


    class Meta:
        model = AbnormityDetail
        fields = ('time', 'result_data')


class CreateExceptionSerializer(serializers.Serializer):

    files = serializers.ListField(child=serializers.FileField())
    abnormity_type = serializers.SlugRelatedField(
        slug_field='code',
        queryset=AbnormityType.objects.filter(is_active=True)
    )
    device = serializers.SlugRelatedField(
        slug_field='device_label',
        queryset=Device.objects.all()
    )
    start_time = serializers.DateTimeField(
        input_formats=['%Y_%m_%d_%H_%M_%S', '%Y-%m-%d %H:%M:%S']
    )
    tboard = serializers.PrimaryKeyRelatedField(
        queryset=TBoard.objects.all(),
        required=False
    )
    result_data = serializers.JSONField(binary=True)

    def save(self, **kwargs):
        files = self.validated_data.pop('files')
        result_data = self.validated_data.pop('result_data')
        result = []
        try:
            with transaction.atomic():
                abn_obj = Abnormity.objects.create(**self.validated_data)
                abn_detail_obj = AbnormityDetail.objects.create(abnormity=abn_obj, result_data=result_data,
                                                                time=self.validated_data['start_time'])
                for file in files:
                    # 上传文件名为中文时，获取filename后面会多出一个' " '，django处理源码在django.http.multipartparser.py(664行)
                    # 此问题django已修复，但未合并到2.2版本，具体可见: https://code.djangoproject.com/ticket/31293，
                    # 相关连接 https://tools.ietf.org/html/rfc2231#section-4.1
                    file_name = file.name[:-1] if file.name[-1] == '"' else file.name

                    # 验证上传的文件格式
                    file_type = file_name.split('.')[-1]
                    if file_type not in JOB_RESOURCE_FILE_TYPE:
                        raise serializers.ValidationError('Upload file format is incorrect')

                    instance = AbnormityLog.objects.create(
                        name=file_name,
                        type=file_type,
                        file=file,
                        abnormity_detail=abn_detail_obj
                    )
                    result.append(instance.file.path)
        except Exception as e:
            return reef_400_response(description='上传异常日志错误', message=f"exception: {e}")
        return result





