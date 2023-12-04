import json
import os
from collections import OrderedDict
from io import StringIO

from django.apps import apps
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import APIException
from rest_framework.validators import UniqueTogetherValidator

from apiv1.core.constants import JOB_RESOURCE_FILE_TYPE, REEF_ADMIN_GROUP_NAME, CABINET_TYPE_LIST, INNER_JOB_FLOW
from apiv1.core.response import reef_400_response
from apiv1.core.view.generic import CustomStrField
from apiv1.module.job.models import Job, CustomTag, JobTestArea, Unit, JobResourceFile, JobFlow, TestGather, \
    TestProject, Unit_EN
from apiv1.module.device.models import AndroidVersion, PhoneModel, RomVersion, Device
from apiv1.module.job.error import ValidationError
from apiv1.module.tboard.models import TBoard
from apiv1.module.user.models import ReefUser


class CustomTagSerializer(serializers.ModelSerializer):
    """
    Generic Serializer
    """

    class Meta:
        model = CustomTag
        fields = '__all__'


class JobSerializer(serializers.ModelSerializer):
    """
    Generic Serializer
    """
    test_area = serializers.PrimaryKeyRelatedField(many=True, queryset=JobTestArea.objects.all(), required=False,
                                                   allow_empty=True)
    android_version = serializers.PrimaryKeyRelatedField(many=True, queryset=AndroidVersion.objects.all(),
                                                         required=False, allow_empty=True)
    custom_tag = serializers.PrimaryKeyRelatedField(many=True, queryset=CustomTag.objects.all(), required=False,
                                                    allow_empty=True)
    phone_models = serializers.PrimaryKeyRelatedField(many=True, queryset=PhoneModel.objects.all(), required=False,
                                                      allow_empty=True)
    rom_version = serializers.PrimaryKeyRelatedField(many=True, queryset=RomVersion.objects.all(), required=False,
                                                     allow_empty=True)
    ui_json_file = serializers.JSONField(write_only=True)

    def validate(self, data: OrderedDict):
        """job、innerjob 都不受manufacturer限制，可以适用于不同的厂商，所以先把校验去掉"""
        # """Job的rom_version和phone_model应来自于同一个manufacturer"""
        # phone_models = data.get("phone_models",
        #                         [] if self.instance is None else list(PhoneModel.objects.filter(job=self.instance)))
        # rom_version = data.get("rom_version",
        #                        [] if self.instance is None else list(RomVersion.objects.filter(job=self.instance)))
        #
        # manufacturers = {
        #     p.manufacturer_id for p in phone_models
        # }.union({
        #     r.manufacturer_id for r in rom_version
        # })
        #
        # if len(manufacturers) > 1:
        #     raise ValidationError("Job的所有rom version, phone model 应来自于同一个manufacturer")

        # Job 不能关联具有 Admin 权限的用户
        if 'author' in data:
            author = data['author']
            if REEF_ADMIN_GROUP_NAME in list(author.groups.all().values_list('name', flat=True)):
                raise ValidationError("Job 不能关联具有 Admin 权限的用户")

        # ui_json 以json格式传入，转成可上传的文件
        if 'ui_json_file' in data:
            f = StringIO()
            f.write(json.dumps(data['ui_json_file']))
            up_file = InMemoryUploadedFile(f, None, "ui.json", None, None, None, None)
            data['ui_json_file'] = up_file

        return data

    class Meta:
        model = Job
        fields = '__all__'


class JobTestAreaSerializer(serializers.ModelSerializer):
    """
    Generic Serializer
    """

    class Meta:
        model = JobTestArea
        fields = '__all__'


class UnionJobSerializer(serializers.ModelSerializer):
    custom_tags = serializers.SlugRelatedField(
        slug_field='custom_tag_name',
        many=True,
        read_only=True,
        source='custom_tag'
    )
    job_test_areas = serializers.SlugRelatedField(
        slug_field='description',
        many=True,
        read_only=True,
        source='test_area'
    )

    class Meta:
        model = Job
        fields = ('id', 'job_label', 'job_name', 'custom_tags', 'job_test_areas')


class UnitLibSerializer(serializers.ModelSerializer):
    """
    Generic Serializer
    """

    def validate(self, attrs):
        unit_content = attrs.get('unit_content', None)
        if unit_content:
            if type(unit_content) is not dict:
                raise serializers.ValidationError({'error': 'unit_content is not json'})
        return attrs

    class Meta:
        model = Unit
        fields = '__all__'


class UnitENLibSerializer(serializers.ModelSerializer):
    """
    Generic Serializer
    """

    def validate(self, attrs):
        unit_content = attrs.get('unit_content', None)
        if unit_content:
            if type(unit_content) is not dict:
                raise serializers.ValidationError({'error': 'unit_content is not json'})
        return attrs

    class Meta:
        model = Unit_EN
        fields = '__all__'


class JobResourceFileSerializer(serializers.ModelSerializer):
    """
      Generic Serializer
    """

    name = serializers.CharField(read_only=True)
    type = serializers.CharField(read_only=True)

    def validate(self, attrs):
        file = attrs.get('file', None)
        if file:
            attrs['name'] = attrs['file'].name
            attrs['type'] = attrs['file'].name.split('.')[-1]
        return attrs

    class Meta:
        model = JobResourceFile
        fields = '__all__'


class JobMultiResourceFileSerializer(serializers.Serializer):
    file = serializers.ListField(child=serializers.FileField())
    name = serializers.CharField(read_only=True)
    type = serializers.CharField(read_only=True)
    job_flow = serializers.PrimaryKeyRelatedField(queryset=JobFlow.objects.all())

    def create(self, validated_data):
        res_list = []
        old_res_file_list = []
        job_flow = validated_data['job_flow']
        try:
            with transaction.atomic():
                for res_file in job_flow.job_res_file.all():
                    old_res_file_list.append(res_file.file.path)
                    res_file.delete()
                for f in validated_data['file']:
                    # 上传文件名为中文时，获取filename后面会多出一个' " '，django处理源码在django.http.multipartparser.py(664行)
                    # 此问题django已修复，但未合并到2.2版本，具体可见: https://code.djangoproject.com/ticket/31293，
                    # 相关连接 https://tools.ietf.org/html/rfc2231#section-4.1
                    file_name = f.name[:-1] if f.name[-1] == '"' else f.name

                    # 验证上传的文件格式
                    file_type = file_name.split('.')[-1]
                    if file_type not in JOB_RESOURCE_FILE_TYPE:
                        raise serializers.ValidationError('Upload file format is incorrect')

                    instance = JobResourceFile.objects.create(
                        name=file_name,
                        type=file_type,
                        file=f,
                        job_flow=job_flow
                    )
                    res = JobResourceFileSerializer(instance, context=self.context)
                    res_list.append(res.data)

                job_flow.job.updated_time = timezone.now()
                job_flow.job.save()
        except Exception as e:
            raise APIException(detail=f'except message: {e}')
        else:
            _ = [
                os.remove(old_res_file)
                for old_res_file in old_res_file_list if os.path.exists(old_res_file)
            ]
        return {"res_file": res_list}


class JobFlowInfoSerializer(serializers.ModelSerializer):
    """
    Generic Serializer
    """
    job_res_file = JobResourceFileSerializer(many=True)

    class Meta:
        model = JobFlow
        fields = '__all__'


class ExportJobJobFlowInfoSerializer(serializers.ModelSerializer):
    """
    Generic Serializer
    """
    job_res_file = JobResourceFileSerializer(many=True)
    #  该字段用于记录导入用例时，非inner flow关联哪些inner flow, 由于跨系统job flow没有唯一标识，inner job
    #  与inner flow 一对一关系，所以记录可以作为唯一标识的job label。
    inner_flow = serializers.SerializerMethodField()

    def get_inner_flow(self, obj):
        if obj.flow_type == INNER_JOB_FLOW:
            return []
        inner_job_label = []
        for inner_flow in obj.inner_flow.all():
            inner_job_label.append(inner_flow.job.job_label)
        return inner_job_label

    class Meta:
        model = JobFlow
        fields = '__all__'


class JobExportSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(queryset=ReefUser.objects.all())
    job_ids = serializers.PrimaryKeyRelatedField(many=True, queryset=Job.objects.filter(job_deleted=False))


class JobExecuteImportSerializer(serializers.Serializer):
    dir_name = serializers.CharField()
    job_name_list = serializers.ListField(required=False)
    inner_job_name_list = serializers.ListField(required=False)


class JobInfoSerializer(serializers.ModelSerializer):
    job_flow = ExportJobJobFlowInfoSerializer(many=True)

    class Meta:
        model = Job
        depth = 2
        fields = '__all__'


class JobImportSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(queryset=ReefUser.objects.all())
    file = serializers.FileField()


class JobResFileExportSerializer(serializers.ModelSerializer):
    job_flow = JobFlowInfoSerializer(many=True)

    class Meta:
        model = Job
        fields = ('job_label', 'job_flow')
        depth = 2


class JobFlowSerializer(serializers.ModelSerializer):
    """
    Generic Serializer
    """
    ui_json_file = serializers.JSONField(write_only=True)

    def validate(self, attr):
        # innerflow 不能内嵌inner_flow
        if self.partial:
            if self.instance.flow_type == 'InnerFlow':
                if 'inner_flow' in attr:
                    raise ValidationError('inner_flow cannot related other flow')
            if 'ui_json_file' not in attr:
                return attr

        else:
            if attr['flow_type'] == 'InnerFlow':
                if 'inner_flow' in attr:
                    raise ValidationError('inner_flow cannot related other flow')

        # ui_json 以JSON格式传入，转成可上传的文件
        f = StringIO()
        f.write(json.dumps(attr['ui_json_file']))
        up_file = InMemoryUploadedFile(f, None, "ui.json", None, None, None, None)
        attr['ui_json_file'] = up_file
        return attr

    class Meta:
        model = JobFlow
        fields = '__all__'


class JobFlowOrderUpdateSerializer(serializers.Serializer):
    job = serializers.PrimaryKeyRelatedField(queryset=Job.objects.all())
    flows = serializers.PrimaryKeyRelatedField(many=True, queryset=JobFlow.objects.all())


class JobFlowCopySerializer(serializers.Serializer):
    flow = serializers.PrimaryKeyRelatedField(queryset=JobFlow.objects.all())
    job = serializers.PrimaryKeyRelatedField(queryset=Job.objects.all())
    name = serializers.CharField(required=False)

    class Meta:
        validators = [
            UniqueTogetherValidator(
                queryset=JobFlow.objects.all(),
                fields=['job', 'name']
            )
        ]


class JobCopySerializer(serializers.Serializer):
    job_id = serializers.PrimaryKeyRelatedField(queryset=Job.objects.all())
    job_name = serializers.CharField()
    job_label = serializers.CharField()
    author_id = serializers.PrimaryKeyRelatedField(queryset=ReefUser.objects.all())


class JobBindResourceSerializer(serializers.Serializer):
    job_label = serializers.SlugRelatedField(
        slug_field='job_label',
        queryset=Job.objects.filter(job_deleted=False),
    )

    resource_data = serializers.ListField()


class TestGatherSerializer(serializers.ModelSerializer):
    testproject = serializers.ManyRelatedField(
        serializers.PrimaryKeyRelatedField(
            queryset=TestProject.objects.all(),
        ),
        required=False
    )

    class Meta:
        model = TestGather
        read_only_fields = ('job_count', 'duration_time', 'cabinet_version')
        exclude = ('job',)
        # fields = ('job_count', 'duration_time', 'cabinet_version', 'testproject', 'name')


class UpdateTestGatherSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=TestGather.objects.all()
    )
    job_ids = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=Job.objects.all()
        ),
        min_length=1,
    )
    operate = serializers.ChoiceField(
        choices=[
            ('add', 'add'),
            ('delete', 'delete')
        ]
    )


class MergeTestGatherSerializer(serializers.Serializer):
    test_gathers = serializers.ListSerializer(
        child=serializers.PrimaryKeyRelatedField(
            queryset=TestGather.objects.all()
        )
    )


class JobLabelOrderSerializer(serializers.Serializer):
    label_name = serializers.ChoiceField(
        choices=[
            ('CustomTag', 'custom_tag_name'),
            ('JobTestArea', 'description')
        ]
    )


class SearchJobSerializer(serializers.Serializer):
    job = serializers.SlugRelatedField(
        queryset=Job.objects.filter(job_deleted=False),
        slug_field='job_label'
    )
    job_list = serializers.ListSerializer(
        child=serializers.SlugRelatedField(
            queryset=Job.objects.filter(job_deleted=False),
            slug_field='job_label'
        ),
        required=False
    )


class CheckTBoardSerializer(serializers.Serializer):
    tboard = serializers.PrimaryKeyRelatedField(
        queryset=TBoard.objects.filter(is_to_delete=False),
        required=False
    )

    test_gather = serializers.PrimaryKeyRelatedField(
        queryset=TestGather.objects.all(),
        required=False
    )


class DataViewJobFilterSerializer(CheckTBoardSerializer):
    device = serializers.PrimaryKeyRelatedField(
        queryset=Device.objects.all(),
        required=False
    )

    job = serializers.PrimaryKeyRelatedField(
        queryset=Job.objects.all(),
        required=False
    )

    author__in = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=ReefUser.objects.all()
        ),
        required=False
    )

    cabinet_type__in = serializers.ListField(
        child=serializers.ChoiceField(
            choices=CABINET_TYPE_LIST
        ),
        required=False
    )

    phone_models__in = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=PhoneModel.objects.all()
        ),
        required=False
    )

    android_version__in = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=AndroidVersion.objects.all()
        ),
        required=False
    )

    rom_version__in = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=RomVersion.objects.all()
        ),
        required=False
    )

    custom_tag__in = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=CustomTag.objects.all()
        ),
        required=False
    )

    test_area__in = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=JobTestArea.objects.all()
        ),
        required=False
    )

    contains = serializers.CharField(required=False)

    order = serializers.ChoiceField(
        choices=[
            ('success_num', 'success_num'),
            ('success_rate', 'success_rate'),
            ('fail_num', 'fail_num'),
            ('fail_rate', 'fail_rate'),
            ('invalid_rate', 'invalid_rate'),
            ('invalid_num', 'invalid_num')
        ]
    )

    reverse = serializers.BooleanField(
        required=False,
        default=False
    )

    limit = serializers.IntegerField(min_value=0, required=False)
    offset = serializers.IntegerField(min_value=0, required=False)

    filter_condition = serializers.ChoiceField(
        choices=[
            ('job', 'job_prior_filter'),
            ('device', 'device_prior_filter')
        ]
    )


class CheckModelSerializer(serializers.Serializer):
    CustomTag = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=CustomTag.objects.all(),
        ),
        required=False
    )

    JobTestArea = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=JobTestArea.objects.all(),
        ),
        required=False
    )


class DeleteTagSerializer(serializers.Serializer):
    module = serializers.ChoiceField(
        choices=(
            ('CustomTag', 'CustomTag'),
            ('JobTestArea', 'JobTestArea')
        )
    )

    id_list = serializers.ListField()

    def validate(self, value):
        module = value.get('module', None)
        id_list = value.get('id_list', [])
        serializer = CheckModelSerializer(data={module: id_list})
        serializer.is_valid(raise_exception=True)
        value['id_list'] = serializer.validated_data.get(module, [])
        return value


class TestProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestProject
        fields = '__all__'


class OperateTestGatherSerializer(serializers.Serializer):
    operate = serializers.ChoiceField(
        choices=[
            ('add', 'add'),
            ('copy', 'copy'),
            ('remove', 'remove'),
            ('quit', 'quit')
        ]
    )

    test_gather_list = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=TestGather.objects.all()
        )
    )

    target_test_project = serializers.PrimaryKeyRelatedField(
        queryset=TestProject.objects.all(),
        required=False
    )

    source_test_project = serializers.PrimaryKeyRelatedField(
        queryset=TestProject.objects.all(),
        required=False
    )

    def validate(self, attrs):
        # add， copy， rm target_test_project is required
        operate = attrs.get('operate')
        if operate == 'add' or operate == 'copy' or operate == 'rm':
            if attrs.get('target_test_project') is None:
                return reef_400_response(message='target_test_project parameter is required')
        if operate == 'remove' or operate == 'quit':
            if attrs.get('source_test_project') is None:
                return reef_400_response(message='source_test_project parameter is required')
        return attrs


class GetTestGatherSerializer(serializers.Serializer):
    test_project = serializers.PrimaryKeyRelatedField(
        queryset=TestProject.objects.all(),
        required=False
    )

    exclude_test_project = serializers.PrimaryKeyRelatedField(
        queryset=TestProject.objects.all()
    )

    limit = serializers.IntegerField(min_value=0, required=False)
    offset = serializers.IntegerField(min_value=0, required=False)
    contains = serializers.CharField(required=False)


class CustomTestGatherDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestGather
        fields = ('name', 'job_count', 'cabinet_version', 'duration_time', 'update_time', 'id')
