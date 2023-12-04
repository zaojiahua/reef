import os
from pathlib import Path

from django.db.models import Count
from rest_framework import status
from rest_framework.response import Response

from apiv1.module.job.models import CustomTag, Job, JobTestArea, JobResourceFile, JobFlow, TestGather, TestProject, \
    Unit, Unit_EN
from apiv1.core.response import reef_400_response
from apiv1.core.utils import ReefLogger
from apiv1.module.job.serializer import CustomTagSerializer, JobSerializer, JobTestAreaSerializer, \
    JobResourceFileSerializer, JobFlowSerializer, TestGatherSerializer, TestProjectSerializer, UnitLibSerializer, \
    UnitENLibSerializer
from apiv1.core.view.generic import GenericViewSet
from apiv1.module.job import signal
from reef.settings import MEDIA_ROOT


# customtag 通用接口,无特殊逻辑
class DynamicCustomTagViewSet(GenericViewSet):
    serializer_class = CustomTagSerializer
    queryset = CustomTag.objects.all()
    return_key = 'customtags'
    queryset_filter = {}
    instance_filter = {}


# job 通用接口,无特殊逻辑
class DynamicJobViewSet(GenericViewSet):
    serializer_class = JobSerializer
    queryset = Job.objects.all()
    return_key = 'jobs'
    queryset_filter = {}
    instance_filter = {}

    # 不支持delete，如果有删除的需求，应该使用PATH方法更新job_deleted字段为True
    def destroy(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    # job 更新数据
    def perform_update(self, serializer):
        old_job = self.get_object()
        serializer.save()
        job = self.get_object()
        # job cabinet_type 字段变动，更新测试集表，cabinet_version 字段
        if old_job.cabinet_type != job.cabinet_type:
            test_gather_queryset = job.testgather.all()
            for test_gather in test_gather_queryset:
                cabinets = test_gather.job.exclude(cabinet_type=None).values('cabinet_type').annotate(
                    Count('cabinet_type'))
                cabinet_version_list = [cabinet['cabinet_type'] for cabinet in cabinets]
                test_gather.cabinet_version = {'cabinet_version_list': cabinet_version_list}
                test_gather.save()


# jobtestarea 通用接口,无特殊逻辑
class DynamicJobTestAreaViewSet(GenericViewSet):
    serializer_class = JobTestAreaSerializer
    queryset = JobTestArea.objects.all()
    return_key = 'jobtestareas'
    queryset_filter = {}
    instance_filter = {}


# unit 通用接口,无特殊逻辑
class DynamicUnitLibViewSet(GenericViewSet):
    serializer_class = UnitLibSerializer
    queryset = Unit.objects.all()
    return_key = 'unit'
    queryset_filter = {}
    instance_filter = {}


# unit_en 通用接口，无特殊逻辑
class DynamicUnitENLibViewSet(GenericViewSet):
    serializer_class = UnitENLibSerializer
    queryset = Unit_EN.objects.all()
    return_key = 'unit'
    queryset_filter = {}
    instance_filter = {}


# re_file通用接口,无特殊逻辑
class DynamicJobResourceFileViewSet(GenericViewSet):
    serializer_class = JobResourceFileSerializer
    queryset = JobResourceFile.objects.all()
    return_key = 'job_res_files'
    queryset_filter = {}
    instance_filter = {}


# job_flow通用接口,无特殊逻辑
class DynamicJobFlowViewSet(GenericViewSet):
    serializer_class = JobFlowSerializer
    queryset = JobFlow.objects.all()
    return_key = 'job_flows'
    queryset_filter = {}
    instance_filter = {}

    # 重写create\update方法，触发job_res_file_export信号，异步完成job_res_file导出更新
    def perform_create(self, serializer):
        super(DynamicJobFlowViewSet, self).perform_create(serializer)
        signal.job_res_file_export.send(sender=self.__class__, job=[serializer.data['job']])

    def perform_update(self, serializer):
        try:
            ui_json_file = JobFlow.objects.get(id=serializer.initial_data['id']).ui_json_file.path
        except Exception as e:
            ui_json_file = None
            logger = ReefLogger('backend')
            logger.error(f'{serializer.initial_data.get("id")} not exist: \n'
                         f'{e}')
        super(DynamicJobFlowViewSet, self).perform_update(serializer)
        # rm old ui_json file
        if ui_json_file is not None and os.path.exists(ui_json_file):
            os.remove(ui_json_file)
        if self.action == 'partial_update':
            if self.request.data.get('ui_json_file', None):
                signal.job_res_file_export.send(sender=self.__class__, job=[serializer.data['job']])
        if self.action == 'put':
            signal.job_res_file_export.send(sender=self.__class__, job=[serializer.data['job']])

    def perform_destroy(self, instance):
        ui_json_file_path = instance.ui_json_file.path
        job_res_queryset = instance.job_res_file.all()
        for job_res in job_res_queryset:
            job_res_path = job_res.file.path
            self.unlink_file(job_res_path)
            job_res.delete()
        self.unlink_file(ui_json_file_path)
        super(DynamicJobFlowViewSet, self).perform_destroy(instance)

    def unlink_file(self, path):
        path = Path(path)
        if path.exists() and path.is_file():
            path.unlink()


class TestGatherViewSet(GenericViewSet):
    serializer_class = TestGatherSerializer
    queryset = TestGather.objects.all()
    return_key = 'test_gather'
    queryset_filter = {}
    instance_filter = {}


class TestProjectViewSet(GenericViewSet):
    serializer_class = TestProjectSerializer
    queryset = TestProject.objects.all()
    return_key = 'test_project'
    queryset_filter = {}
    instance_filter = {}

    def destroy(self, request, *args, **kwargs):
        if hasattr(request.user, 'username') and request.user.username == 'admin':
            # 删除项目，移除项目下的测试集
            instance = self.get_object()
            instance.test_gather.clear()
            return super(TestProjectViewSet, self).destroy(request, *args, **kwargs)
        else:
            reef_400_response(description='admin用户才可以删除项目', message=f'user obj: {request.user}')
