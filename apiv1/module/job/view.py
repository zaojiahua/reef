import codecs
import copy
import datetime
import json
import os
import random
import re
import shutil
import string
import zipfile

from pathlib import Path

from django.apps import apps
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import IntegrityError, transaction, DataError
from django.db.models import F, Count, Max
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from rest_framework import generics, status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework import mixins
from django.db import transaction, connection
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated

from apiv1.core.constants import REEF_USER_DEFAULT_PASSWORD, REEF_ADMIN_GROUP_NAME, JOB_TYPE_INNER_JOB
from apiv1.core.response import reef_400_response, ReefResponse, reef_500_response
from apiv1.core.status import StatusCode
from apiv1.core.utils import JobBindResource, date_format_transverter
from apiv1.core.view.generic import AutoExecuteSerializerGenericAPIView
from apiv1.module.device.models import AndroidVersion, Manufacturer, PhoneModel, RomVersion
from apiv1.module.job import signal
from apiv1.module.job.models import Job, JobTestArea, CustomTag, JobResourceFile, JobFlow, TestGather, Unit, Unit_EN
from apiv1.module.job.serializer import UnionJobSerializer, JobMultiResourceFileSerializer, JobExportSerializer, \
    JobInfoSerializer, JobImportSerializer, JobFlowOrderUpdateSerializer, JobFlowCopySerializer, JobCopySerializer, \
    JobBindResourceSerializer, UpdateTestGatherSerializer, MergeTestGatherSerializer, JobLabelOrderSerializer, \
    SearchJobSerializer, CheckTBoardSerializer, DataViewJobFilterSerializer, DeleteTagSerializer, \
    JobExecuteImportSerializer, OperateTestGatherSerializer, GetTestGatherSerializer, CustomTestGatherDataSerializer, \
    UnitLibSerializer, UnitENLibSerializer
from apiv1.module.job.tasks.tasks import update_job_res_file
from apiv1.module.rds.models import Rds
from apiv1.module.user.models import ReefUser
from reef.settings import BASE_DIR, JOB_EXPORT_ZIP_ROOT, JOB_EXPORT, MEDIA_ROOT, JOB_IMPORT_TMP_ROOT


# class UnitLanguage(generics.GenericAPIView):
#
#     def get(self, request, *args, **kwargs):
#         params = request.query_params
#         language = params.get('language', 'zh')
#
#         if language == 'zh':
#             queryset = Unit.objects.all()
#             serializer_class = UnitLibSerializer(queryset, many=True)
#         else:
#             queryset = Unit_EN.objects.all()
#             serializer_class = UnitENLibSerializer(queryset, many=True)
#         return Response({'unit': serializer_class.data})
#
#     def post(self, request, *args, **kwargs):
#         # 提供中英文unit表的新增，更新和删除
#         # 删除：{"operate":"delete", "id":1, "language":"" }
#         # 新增：{"content":{}, "language":"", }
#         # 更新：{"id":1, "language":"", "content":""}
#         params = request.query_params
#         operate = params.get('operate', None)
#         unit_id = params.get('id', None)
#         language = params.get('language', 'ch')
#         content = params.get('content', None)
#
#         if operate == 'delete':
#             # 删除
#             pass
#         else:
#             if unit_id is None:
#                 # 新增
#                 pass
#             else:
#                 # 更新
#                 pass


class UnionJobView(generics.GenericAPIView):
    # 根据筛选条件（phone_model_name/android_version__version）筛选出job并集集合（通用接口返回交集）
    # ------------------------------------------------------------------
    #   job/属性          phone_model_name     android_version__version
    #     job1               dior1                     8.1.0
    #     job2               dior2                     10.5.6
    # ------------------------------------------------------------------
    #  if filter phone_model_name=dior1&android_version__version=10.5.6
    #        return   jobs:[job1，job2]

    queryset = Job.objects.filter(job_deleted=False)
    serializer_class = UnionJobSerializer

    def get(self, request, *args, **kwargs):
        params = request.query_params
        phone_model_names = params.get('phone_model_name__in', None)
        android_versions = params.get('android_version__version__in', None)
        list_pattern = re.compile('^ReefList\[.*\]$')

        # phone_model
        if phone_model_names is not None:  # ReefList[model1{%,%}model2{%,%}model3]
            if re.match(list_pattern, phone_model_names) is None:
                return Response('Bad phone_model_name argument, '
                                'use phone_model_name__in=ReefList[model1{%,%}model2{%,%}model3]',
                                status=status.HTTP_400_BAD_REQUEST)
            phone_model_names = phone_model_names[9:-1].split('{%,%}')
        else:
            phone_model_names = []

        # android_version
        if android_versions is not None:  # ReefList[version1{%,%}version2{%,%}version3]
            if re.match(list_pattern, android_versions) is None:
                return Response('Bad android_version__version__in argument, '
                                'use android_version__version__in=ReefList[version1{%,%}version2{%,%}version3]',
                                status=status.HTTP_400_BAD_REQUEST)
            android_versions = android_versions[9:-1].split('{%,%}')
        else:
            android_versions = []

        queryset = self.get_queryset()
        job_filter_by_phone_model_names = queryset.filter(
            phone_models__phone_model_name__in=phone_model_names).distinct()
        job_filter_by_android_versions = queryset.filter(android_version__version__in=android_versions).distinct()

        # 对筛选queryset做并集
        if phone_model_names or android_versions:
            queryset = job_filter_by_phone_model_names.union(job_filter_by_android_versions)

        serializer = self.get_serializer(instance=queryset.order_by('id'), many=True)
        return Response({'jobs': serializer.data})


class JobResourceFileMultiUploadView(generics.GenericAPIView):
    """
    该接口上传文件只限于job resource文件
    job flow 关联的ui.json 在通用接口path方法中进行更新
    """
    serializer_class = JobMultiResourceFileSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            re_file = serializer.save()
        except IntegrityError:
            return Response({'unique_together': "JobResourceFile's (job_flow,name) are not unique."},
                            status.HTTP_400_BAD_REQUEST)

        # 执行打包zip操作
        signal.job_res_file_export.send(sender=self.__class__, job=[serializer.validated_data['job_flow'].job.id])

        return Response(re_file, status=status.HTTP_201_CREATED)


class JobFlowOrderUpdateView(generics.GenericAPIView):
    serializer_class = JobFlowOrderUpdateSerializer

    def post(self, request):
        """
        :param request: {"job": id, "flows":[ids]}  -> 注：传入的flows是已经按order排序好的
        :return:
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = serializer.validated_data['job']
        flows = serializer.validated_data['flows']
        flow_qs = JobFlow.objects.filter(id__in=[flow.id for flow in flows])

        if list(filter(lambda n: n != job.id, flow_qs.values_list('job__id', flat=True))):
            return Response({'error': 'flows should from same job'}, status=status.HTTP_400_BAD_REQUEST)

        # 重新排序之前，先把所有flow的order值更新到一个不会冲突的值，再更新所有排序
        flow_qs.update(order=F('order') + 999)
        for order, id in enumerate(flow.id for flow in flows):
            JobFlow.objects.filter(id=id).update(order=order)

        return Response(status=status.HTTP_200_OK)


class JobExportView(generics.GenericAPIView):
    """
    用例导出：
    导出目录结构Ex:
    export_jobeZPdqoBX
    ├── inner_job
    │   └── c_huoshan_任意视频评论
    │       ├── job_attr.json
    │       └── 任意视频评论
    │           ├── -4_-5_configFile.json
    │           ├── -9_-5_configFile.json
    │           └── ui.json
    ├── job
    │   └── huoshan_home_003_0011（校验精选tab页）_NoCleanBG
    │       ├── job_attr.json
    │       └── 校验精选tab页
    │           ├── -22_-4_configFile.json
    │           ├── -2_-9_referImgFile.png
    │           └── ui.json
    └── mark_info.json

    1. 校验用例归属权,只允许导出自己用例（job关联inner job不做校验），admin用户不做校验
    2. 对inner job 进行去重操作
    """
    serializer_class = JobExportSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user_id']
        job_ids = [job.id for job in serializer.validated_data['job_ids']]
        job_queryset = Job.objects.filter(id__in=job_ids)

        # 管理员可以导出所有用例，普通用户只能导出自己的用例
        if REEF_ADMIN_GROUP_NAME not in list(user.groups.all().values_list('name', flat=True)):
            job_authors = job_queryset.values_list('author', flat=True)
            if list(filter(lambda n: n != user.id, job_authors)):
                return reef_400_response(description='用例导出失败，只能导出自己的用例')

        inner_jobs_info = []
        jobs_info = []
        username_list = []
        job_list = list(job_queryset)
        for job in job_queryset:
            if job.author.username not in username_list:
                username_list.append(job.author.username)
            # 获取job使用的inner job
            if job.job_type != JOB_TYPE_INNER_JOB:
                # 获取 job info
                write_job_info(job, jobs_info)
                for job_flow in job.job_flow.all():
                    for inner_flow in job_flow.inner_flow.all():
                        inner_job = inner_flow.job
                        # job 关联的inner job 不在导出列表里，将inner job添加到列表
                        if inner_job not in job_list:
                            job_list.append(inner_job)
                        write_job_info(inner_job, inner_jobs_info)
            # 获取 inner job info
            else:
                write_job_info(job, inner_jobs_info)
        # 序列化job
        job_attrs = JobInfoSerializer(job_list, many=True).data
        # 构建目录结构
        export_path = os.path.join(JOB_EXPORT_ZIP_ROOT,
                                   'export_job' + (''.join(random.sample(string.ascii_letters, 8))))

        inner_job_dir = os.path.join(export_path, 'inner_job')
        job_dir = os.path.join(export_path, 'job')

        Path(inner_job_dir).mkdir(parents=True, exist_ok=True)
        Path(job_dir).mkdir(parents=True, exist_ok=True)

        for job_attr in job_attrs:
            if job_attr['job_type'] == JOB_TYPE_INNER_JOB:
                job_path_dir = os.path.join(inner_job_dir, job_attr['job_name'])
                Path(job_path_dir).mkdir(parents=True, exist_ok=True)
            else:
                job_path_dir = os.path.join(job_dir, job_attr['job_name'])
                Path(job_path_dir).mkdir(parents=True, exist_ok=True)

            # job_flow
            for index, job_flow in enumerate(job_attr['job_flow']):
                job_flow_path_dir = os.path.join(job_path_dir, job_flow['name'])
                Path(job_flow_path_dir).mkdir(parents=True, exist_ok=True)
                try:
                    # copy ui_json_file, res file 资源到
                    # copy ui_json_file 为 ui.json
                    ui_json_file = os.path.join(MEDIA_ROOT, 'ui_json_file', job_flow['ui_json_file'].split('/')[-1])
                    shutil.copy(ui_json_file, os.path.join(job_flow_path_dir, 'ui.json'))

                    # copy res_file
                    job_res_files = job_flow.pop('job_res_file')
                    for job_res_file in job_res_files:
                        res_file = os.path.join(MEDIA_ROOT, 'job_resource_file', job_res_file['file'].split('/')[-1])
                        shutil.copy(res_file, os.path.join(job_flow_path_dir, job_res_file['name']))


                except FileNotFoundError as e:
                    shutil.rmtree(export_path)
                    return reef_400_response(
                        description='缺少依赖文件，请检查并重新保存用例',
                        message=f'job related resource file missing, please check job integrity: {e}'
                    )

            # 存储 job_attr 到 job_attr.json 文件中
            job_attr_str = json.dumps(job_attr)
            with open(os.path.join(job_path_dir, 'job_attr.json'), 'w') as json_file:
                json_file.write(job_attr_str)

        # 记录inner_job的job_label信息
        mark_info = json.dumps(
            {'username': username_list, 'inner_job': inner_jobs_info, 'job': jobs_info},
            ensure_ascii=False
        )
        with codecs.open(os.path.join(export_path, 'mark_info.json'), 'w', 'utf-8') as json_file:
            json_file.write(mark_info)

        # 生成压缩包
        file_name = f"job-export-{timezone.localtime().strftime('%Y-%m-%d-%H:%M:%S')}-{len(job_ids)}.zip"
        job_zip_path = os.path.join(JOB_EXPORT_ZIP_ROOT, file_name)
        zip_file(job_zip_path, export_path)

        shutil.rmtree(export_path)
        return Response({'success': f"/media/{JOB_EXPORT}/{file_name}"}, status=status.HTTP_200_OK)


class JobExecuteImportView(generics.GenericAPIView):
    serializer_class = JobExecuteImportSerializer

    def get_queryset(self):
        pass

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dir_name = serializer.validated_data.get('dir_name')
        job_name_list = serializer.validated_data.get('job_name_list', [])
        inner_job_name_list = serializer.validated_data.get('inner_job_name_list', [])

        import_dir = os.path.join(JOB_IMPORT_TMP_ROOT, dir_name)
        if not (Path(import_dir).exists() and Path(import_dir).is_dir()):
            return reef_400_response(
                description='上传文件包丢失，请重新上传ZIP包',
                message=f'dir: {dir_name} not exist'
            )

        # save inner job
        inner_job_dir = os.path.join(import_dir, 'inner_job')
        inner_job_label_list = []
        if inner_job_name_list:
            if Path(inner_job_dir).exists():
                inner_job_label_list = get_job_save(inner_job_dir, inner_job_name_list, import_dir)
            else:
                return reef_400_response(
                    description="缺少 inner job 目录，压缩包错误，请检查",
                    message=f"{dir_name} dir lack inner job directory, can't import inner job"
                )
        # save job
        job_dir = os.path.join(import_dir, 'job')
        job_label_list = []
        if job_name_list:
            if Path(job_dir).exists():
                job_label_list = get_job_save(job_dir, job_name_list, import_dir)
            else:
                return reef_400_response(
                    description="缺少 job 目录，压缩包错误，请检查",
                    message=f"{dir_name} dir lack job directory, can't import job"
                )

        # 导入完成删除导入目录
        shutil.rmtree(import_dir)

        # 打包用例
        job_label_list.extend(inner_job_label_list)
        ids = Job.objects.filter(job_label__in=job_label_list).values_list('id', flat=True)
        signal.job_res_file_export.send(sender=self.__class__, **dict(job=ids, is_job_import=True))

        return ReefResponse()


class JobImportView(generics.GenericAPIView):
    """
    校验导入权限，zip包是否可用
    返回job 差异项
    """
    serializer_class = JobImportSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user_id']
        zip_file = serializer.validated_data['file']

        if not zipfile.is_zipfile(zip_file):
            return reef_400_response(description='导入文件不是ZIP压缩文件', message='uploaded file format is incorrect')

        # 获取压缩包并解压
        zip_file_path = os.path.join(BASE_DIR, zip_file.name)
        with open(zip_file_path, 'wb+') as f:
            for chunk in zip_file.chunks():
                f.write(chunk)

        job_import_dir = 'job_import_' + (''.join(random.sample(string.ascii_letters, 8)))
        unzip_path = os.path.join(JOB_IMPORT_TMP_ROOT, job_import_dir)
        Path(unzip_path).mkdir()
        with zipfile.ZipFile(zip_file_path, 'r') as zf:
            zf.extractall(unzip_path)

        os.remove(zip_file_path)

        # 获取压缩包mark_info.json 信息, 三个参数不能缺省
        # {usernmae: [], inner_job:[{}], job:[] }
        with open(os.path.join(unzip_path, 'mark_info.json'), 'r', encoding='UTF-8') as f:
            mark_info = json.load(fp=f)
            user_names = mark_info.get('username')
            inner_jobs_info = mark_info.get('inner_job')
            jobs_info = mark_info.get('job')

        if user_names is None or inner_jobs_info is None or jobs_info is None:
            return reef_400_response(
                description='压缩包错误,不能用作用例导入',
                message=f'mark_info.json 内容错误: \n'
                        f'user_names: {user_names} \n'
                        f'inner_jobs_info: {inner_jobs_info} \n'
                        f'jobs_info: {jobs_info}'
            )

        # 普通用户只能导入自己的用例
        user_groups = list(user.groups.all().values_list('name', flat=True))
        if REEF_ADMIN_GROUP_NAME not in user_groups:
            if list(filter(lambda n: n != user.username, user_names)):
                return reef_400_response(description='用例导入失败，只能导入自己的用例')

        # 判断inner job所属用户是否存在，不存在则进行创建
        for inner_job_info in inner_jobs_info:
            user_name = inner_job_info['job_user_name']
            if user_name not in user_names:
                user_names.append(user_name)
        # admin可以导入任意用例，用例归属的用户不存在直接创建，密码默认并且不激活
        else:
            for username in user_names:
                if not ReefUser.objects.filter(username=username).exists():
                    ReefUser.objects.create_user(username, None, REEF_USER_DEFAULT_PASSWORD, is_active=False)

        # 获取差异job
        # inner job
        inner_job_diff_list, no_diff_inner_job_list = get_diff_job_list(inner_jobs_info)
        # job
        job_diff_list, no_diff_job_list = get_diff_job_list(jobs_info)
        inner_job_diff_list.extend(job_diff_list)
        return ReefResponse(
            data={
                'dir_name': job_import_dir, 'diff_data': inner_job_diff_list,
                'no_diff_inner_job_list': no_diff_inner_job_list, "no_diff_job_list": no_diff_job_list,
                'no_diff_job_num': len(no_diff_inner_job_list) + len(no_diff_job_list)
            }
        )


class JobChangeOwnerView(generics.GenericAPIView):
    def post(self, request):
        operate_user_id = request.data.get('operate_user_id')
        transfer_user_id = request.data.get('transfer_user_id')
        job_ids = request.data.get('job_ids')

        operate_user = get_object_or_404(ReefUser, id=operate_user_id)
        if REEF_ADMIN_GROUP_NAME not in list(operate_user.groups.all().values_list('name', flat=True)):
            return Response({'error': 'You do not have permission to operate '}, status=status.HTTP_400_BAD_REQUEST)

        change_user = get_object_or_404(ReefUser, id=transfer_user_id)
        if REEF_ADMIN_GROUP_NAME in list(change_user.groups.all().values_list('name', flat=True)):
            return Response({'error': 'Cannot transfer to admin role'}, status=status.HTTP_400_BAD_REQUEST)

        jobs = Job.objects.filter(id__in=job_ids)
        if jobs.count() != len(job_ids):
            return Response({'error': 'you had input error job id'}, status=status.HTTP_400_BAD_REQUEST)

        for job in jobs:
            job.author = change_user
            job.save()

        return Response({'success': 'OK'}, status=status.HTTP_200_OK)


class JobFlowCopyView(generics.GenericAPIView):
    serializer_class = JobFlowCopySerializer

    @transaction.atomic
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        #   不传name参数， 不进行unique together 判断。
        #   原因： UniqueTogetherValidator类始终施加一个隐式约束，即它应用的所有字段始终被视为必需的
        if request.data.get('name', None) is None:
            serializer.validators = []
        serializer.is_valid(raise_exception=True)
        flow = serializer.validated_data['flow']
        job_to_be_copy = serializer.validated_data['job']
        flow_name = serializer.validated_data.get('name', None)
        if flow_name is None:
            pattern = '副本'
            re_pattern = f'{flow.name}-{pattern}'
            flow_names_list = JobFlow.objects.filter(job=job_to_be_copy).values_list('name', flat=True)
            flow_names = [
                flow_name
                for flow_name in flow_names_list
                if flow_name.startswith(f'{flow.name}-{pattern}')
            ]
            if flow_names:
                # 获取副本后编号
                re_pattern = re.compile(r'(' + re_pattern + ')(\S+)')
                # TODO 调试使用
                # num_list = []
                # for flow_name in flow_names:
                #     if re_pattern.search(flow_name) is not None:
                #         res = re_pattern.search(flow_name).group(2)
                #         print(res)
                #         if res.isdigit():
                #             num_list.append(res)
                num_list = list(filter(lambda data: data.isdigit(), [
                    re_pattern.search(flow_name).group(2)
                    for flow_name in flow_names
                    if re_pattern.search(flow_name) is not None
                ]))
                if num_list:
                    max_num = max([int(num) for num in num_list])
                    flow_name = f'{flow.name}-{pattern}{max_num + 1}'
                else:
                    flow_name = f'{flow.name}-{pattern}1'
            # 当前job没有该flow name
            else:
                if flow.name in flow_names_list:
                    flow_name = f'{flow.name}-{pattern}'
                else:
                    flow_name = flow.name
            return ReefResponse({'flow_name': flow_name})
        else:
            # flow复制 包括flow本身的信息以及关联的res file信息
            _flow_copy(flow_name, flow, job_to_be_copy)

            # 更新job的更新时间
            job_to_be_copy.updated_time = timezone.now()
            job_to_be_copy.save()

            # 执行打包
            update_job_res_file(job_ids=[job_to_be_copy.id])
            return Response({'success': 'OK'}, status=status.HTTP_200_OK)


class JobDeletedView(generics.GenericAPIView):

    def post(self, request):
        job_ids = request.data.get('job_ids')
        jobs = list(Job.objects.filter(id__in=job_ids, job_deleted=False))

        if len(jobs) != len(job_ids):
            not_exist_job = list(set(job_ids) - set(jobs))
            return reef_400_response(StatusCode.JOB_NOT_EXIST.value, StatusCode.JOB_NOT_EXIST.name,
                                     f'Has input deleted job: {not_exist_job}')

        point_out = []
        job_obj_list = copy.deepcopy(jobs)
        for job in jobs:
            # inner job 判断是否有关联可用job
            if job.job_type == JOB_TYPE_INNER_JOB:
                if not request.user.is_superuser:
                    return reef_400_response(
                        custom_code=StatusCode.NOT_ADMIN_PERMISSION.value,
                        message=StatusCode.NOT_ADMIN_PERMISSION.name,
                        description='不是管理员，不能删除inner job！！！'
                    )
                flow_queryset = job.job_flow.first().job_flow.all()
                for flow in flow_queryset:
                    if not flow.job.job_deleted:
                        point_out.append(job.job_name)
                        job_obj_list.remove(job)
                        break
        if point_out:
            return reef_400_response(data={'point_out_job': point_out, 'enable': [job.id for job in job_obj_list]})
        for job in jobs:
            now_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            job.job_name = f'{job.job_name}_{now_time}'
            job.job_deleted = True
            # 删除flow 和inner flow关联
            for job_flow in job.job_flow.all():
                job_flow.inner_flow.clear()
            # 清理该用例和测试集关联
            test_gather_list = list(job.testgather.all())
            job.testgather.clear()
            for test_gather in test_gather_list:
                job_info = job_statistics(test_gather.job.all())
                TestGather.objects.filter(id=test_gather.id).update(**job_info)
            job.save()

        return ReefResponse()


class DeviceFilterJobListView(generics.GenericAPIView):

    def get(self):
        pass


class JobCopyView(generics.GenericAPIView):
    serializer_class = JobCopySerializer

    @transaction.atomic
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        copy_job = serializer.validated_data['job_id']

        job = Job.objects.create(
            job_label=serializer.validated_data['job_label'],
            job_name=serializer.validated_data['job_name'],
            job_type=copy_job.job_type,
            job_second_type=copy_job.job_second_type,
            description=copy_job.description,
            power_upper_limit=copy_job.power_upper_limit,
            power_lower_limit=copy_job.power_lower_limit,
            case_number=copy_job.case_number,
            priority=copy_job.priority,
            draft=copy_job.draft,
            job_deleted=copy_job.job_deleted,
            flow_execute_mode=copy_job.flow_execute_mode,
            cabinet_type=copy_job.cabinet_type,
            matching_rule=copy_job.matching_rule,
            author=serializer.validated_data['author_id']
        )

        job.test_area.add(*copy_job.test_area.all())
        job.android_version.add(*copy_job.android_version.all())
        job.phone_models.add(*copy_job.phone_models.all())
        job.rom_version.add(*copy_job.rom_version.all())
        job.custom_tag.add(*copy_job.custom_tag.all())

        for job_flow in copy_job.job_flow.all():
            _flow_copy(job_flow.name, job_flow, job, is_job_copy=True)

        signal.job_res_file_export.send(sender=self.__class__, job=[job.id])

        return Response({'success': 'OK'}, status=status.HTTP_200_OK)


class JobBindResourceView(generics.GenericAPIView):
    serializer_class = JobBindResourceSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        resource_data = serializer.validated_data['resource_data']
        job = serializer.validated_data['job_label']
        # handle [[]] --> {}
        handler = JobBindResource(resource_data)
        matching_rule = handler.handle()
        # 记录resource_data： [[],[]], 前端用于展示数据
        matching_rule.update({'resource_data': resource_data})
        job.matching_rule = matching_rule
        job.save()
        return ReefResponse(job.matching_rule)


class UpdateTestGatherViewSet(mixins.CreateModelMixin,
                              GenericViewSet):
    serializer_class = UpdateTestGatherSerializer
    queryset = TestGather.objects.all()

    def perform_create(self, serializer):
        jobs = Job.objects.filter(id__in=serializer.data.get('job_ids'))
        test_gather_queryset = TestGather.objects.filter(id=serializer.data['id'])
        test_gather = test_gather_queryset.first()
        if not test_gather:
            return reef_400_response(message=f"{serializer.data['id']} test_gather obj not exist")
        operate = serializer.data.get('operate')
        if operate == 'add':
            test_gather.job.add(*jobs)
            job_info = job_statistics(test_gather.job.all())
            test_gather_queryset.update(**job_info)
        elif operate == 'delete':
            test_gather.job.remove(*jobs)
            job_info = job_statistics(test_gather.job.all())
            test_gather_queryset.update(**job_info)


class MergeTestGatherView(generics.GenericAPIView):
    serializer_class = MergeTestGatherSerializer
    queryset = TestGather.objects.all()

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        test_gathers_queryset = serializer.validated_data['test_gathers']
        job_label_list = []
        for test_gather in test_gathers_queryset:
            job_label_list.extend(test_gather.job.all().values_list('job_label', flat=True))
        return ReefResponse({'job_label_list': job_label_list})


class JobLabelOrderView(generics.GenericAPIView):
    serializer_class = JobLabelOrderSerializer
    queryset = Job.objects.all()

    def get(self, request):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        model_name = serializer.validated_data['label_name']
        group_name = serializer.fields['label_name'].choices[model_name]
        model_cls = apps.get_model('apiv1', model_name)
        # model 是否有job fields
        if not hasattr(model_cls, 'job'):
            return reef_400_response(message=f"{model_cls} model not have job fields")
        group_data_queryset = model_cls.objects.filter(job__job_deleted=False).values(group_name, 'id').annotate(
            job_count=Count('job'))
        # sort
        results = sorted(group_data_queryset, key=lambda x: x['job_count'], reverse=True)
        res = []
        for data in results:
            data.update({'name': data.pop(group_name)})
            res.append(data)
        return ReefResponse(res)


class SearchJobView(generics.GenericAPIView):
    serializer_class = SearchJobSerializer
    queryset = Job.objects.all()

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = serializer.validated_data['job']
        job_list = serializer.validated_data.get('job_list', None)
        results = []
        count = 0
        if job.job_type == 'InnerJob':
            inner_job_flow = JobFlow.objects.filter(job=job).first()
            if inner_job_flow is None:
                return reef_400_response(description='当前用例异常，请检查用例', message=f'inner job not found job flow')
            job_flow_queryset = inner_job_flow.job_flow.filter(job__job_deleted=False).select_related('job').distinct(
                'job')
            count = len(job_flow_queryset)
            # 筛选在job list中的job。
            if job_list:
                job_flow_queryset = job_flow_queryset.filter(job__in=job_list, job__job_deleted=False)
                count = job_flow_queryset.count()
            job_flow_queryset = self.paginate_queryset(job_flow_queryset)
            for job_flow in job_flow_queryset:
                results.append({
                    'inner_job_name': job.job_name,
                    'job_name': job_flow.job.job_name,
                    'author': job_flow.job.author.username,
                    'cabinet_type': job_flow.job.cabinet_type
                })
        return ReefResponse(results, headers={"Total-Count": count})


class DeleteTagView(AutoExecuteSerializerGenericAPIView):
    serializer_class = DeleteTagSerializer

    def get_queryset(self):
        pass

    def delete(self, request):
        """
        批量删除自定义标签
        目前只支持删除：CustomTag， JobTestArea。且一次只能删除一种标签
        在使用的（关联job了）不可以删除。
        """
        serializer = self.execute(request)
        validated_data = serializer.validated_data
        model_list = validated_data.get('id_list')
        module = validated_data.get('module')
        if module == 'CustomTag':
            fields_name = 'custom_tag_name'
        elif module == 'JobTestArea':
            fields_name = 'description'
        else:
            fields_name = ''
        use_list = job_use_tag(model_list, fields_name)
        if not use_list:
            return ReefResponse()
        else:
            return reef_400_response(data=use_list)


class OperateTestGather(AutoExecuteSerializerGenericAPIView):
    serializer_class = OperateTestGatherSerializer
    queryset = TestGather.objects.all()

    def post(self, request):
        serializer = self.execute(request)
        operate = serializer.validated_data.get('operate')
        test_gather = serializer.validated_data.get('test_gather_list')
        target_test_project = serializer.validated_data.get('target_test_project')
        source_test_project = serializer.validated_data.get('source_test_project')
        change_num = None
        if operate == 'add':
            change_num = add_test_gather_to_project(target_test_project, test_gather)
        elif operate == 'copy':
            change_num = add_test_gather_to_project(target_test_project, test_gather)
        elif operate == 'remove':
            # 移动
            source_test_project.test_gather.remove(*test_gather)
            source_test_project.save(update_fields=['update_time'])
            change_num = add_test_gather_to_project(target_test_project, test_gather)
        elif operate == 'quit':
            # 从项目中移除
            source_test_project.test_gather.remove(*test_gather)
            source_test_project.save(update_fields=['update_time'])
        if change_num is None:
            ret = {}
        else:
            ret = {'change_num': change_num}
        return ReefResponse(ret)


class GetTestGatherViewSet(AutoExecuteSerializerGenericAPIView):
    serializer_class = GetTestGatherSerializer
    queryset = TestGather.objects.all()

    def get(self, request):
        serializer = self.execute(request, action='get')
        test_project = serializer.validated_data.get('test_project')
        exclude_test_project = serializer.validated_data.get('exclude_test_project')
        contains = serializer.validated_data.get('contains')
        test_gather_queryset = TestGather.objects.exclude(testproject=exclude_test_project).order_by('-update_time')
        if test_project:
            test_gather_queryset = test_gather_queryset.filter(testproject=test_project)
        if 'contains' in request.query_params.dict():
            test_gather_queryset = test_gather_queryset.filter(name__contains=contains)
        count = len(test_gather_queryset)
        if 'limit' in request.query_params.dict() or 'offset' in request.query_params.dict():
            pagination = LimitOffsetPagination()
            test_gather_queryset = pagination.paginate_queryset(test_gather_queryset, request, view=None)

        serializer = CustomTestGatherDataSerializer(test_gather_queryset, many=True)
        return ReefResponse(serializer.data, headers={"Total-Count": count})


#####################################################
# helper function                                   #
#####################################################
def zip_file(zip_file_path, file_path):
    f = zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(file_path):
        dir_path = root.replace(file_path, '') and root.replace(file_path, '') + os.sep or ''
        for file in files:
            f.write(os.path.join(root, file), dir_path + file)
    f.close()
    return


def file_copy(copy_obj: str = None, flow_obj=None, job_res_file_obj=None):
    if copy_obj == 'job_flow':
        new_file_name = FileSystemStorage().get_available_name('ui_json_file/ui.json')
        resource_file_path = flow_obj.ui_json_file.path
        tag_file_path = os.path.join(MEDIA_ROOT, new_file_name)
    elif copy_obj == 'job_res':
        new_file_name = FileSystemStorage().get_available_name(f'job_resource_file/{job_res_file_obj.name}')
        resource_file_path = job_res_file_obj.file.path
        tag_file_path = os.path.join(MEDIA_ROOT, new_file_name)
    else:
        return reef_500_response(message=f'copy_obj parameter illegal')
    if resource_file_path and tag_file_path:
        try:
            shutil.copy2(resource_file_path, tag_file_path)
        except Exception as e:
            # clean job flow ui_json_file, new create job res file
            if copy_obj == 'job_res':
                os.remove(flow_obj.ui_json_file.path)
                [os.remove(job_res.file.path) for job_res in JobResourceFile.objects.filter(job_flow=flow_obj)]
            reef_500_response(message=f'copy flow error: {e}')
        return new_file_name


def _flow_copy(name, flow, job, is_job_copy=False):
    file_name = file_copy('job_flow', flow)
    copy_flow = JobFlow.objects.create(
        name=name,
        job=job,
        flow_type=flow.flow_type,
        order=flow.order if is_job_copy else max([flow.order for flow in job.job_flow.all()], default=0) + 2,
        description=flow.description,
        ui_json_file=file_name
    )
    copy_flow.inner_flow.add(*list(flow.inner_flow.all()))

    for resfile in flow.job_res_file.all():
        file_name = file_copy('job_res', flow_obj=copy_flow, job_res_file_obj=resfile)
        JobResourceFile.objects.create(
            name=resfile.name,
            type=resfile.type,
            job_flow=copy_flow,
            file=file_name
        )
    return


def job_statistics(jobs):
    job_count = jobs.count()
    duration_time = sum([job.process_time for job in jobs if job.process_time is not None])
    cabinets = jobs.exclude(cabinet_type=None).values('cabinet_type').annotate(Count('cabinet_type'))
    # cabinets = [{cabinet_type: "cab-1", cabinet_type_count: 1}{cabinet_type: "cab-1", cabinet_type_count: 2}]
    cabinet_version_list = [cabinet['cabinet_type'] for cabinet in cabinets]
    return {'job_count': job_count, 'duration_time': duration_time, "update_time": timezone.localtime(),
            'cabinet_version': {'cabinet_version_list': cabinet_version_list}}


def job_use_tag(model_list, fields_name):
    use_list = []
    for model in model_list:
        job_count = model.job.filter(job_deleted=False).count()
        if job_count:
            use_list.append(getattr(model, fields_name))
        else:
            model.delete()
    return use_list


def get_diff_job_list(jobs_info):
    """
    jobs_info:
    [{
    'job_label': 'job-4cdc0ac1-2e95-6290-f419-25ded337b9cf',
    'update_time': '2022-02-14 10:50:33:853738',
    'job_name': 'xiaomi_获取日志（含bugReport）',
    'job_user_name': 'gejuan@anhereef.com'
    }]
    """
    diff_info_list = []
    no_diff_job_name_list = []
    for job_info in jobs_info:
        job_label = job_info['job_label']
        job_name = job_info['job_name']
        job_user_name = job_info['job_user_name']
        update_time = datetime.datetime.strptime(job_info['update_time'], "%Y-%m-%d %H:%M:%S:%f")
        try:
            # 存在冲突，返给前端页面进行选择
            job = Job.objects.get(job_label=job_label, job_deleted=False)
            # 导入用例和系统中原有用例做比较，true 表示导入用例时间更新，反之亦然。
            old_job_updated_time = timezone.localtime(job.updated_time)
            contrast = update_time.__gt__(old_job_updated_time.replace(tzinfo=None))
            ret = {
                'contrast': contrast,
                'import_job_name': job_name,
                'import_job_update_time': datetime.datetime.strftime(update_time, "%Y-%m-%d %H:%M:%S"),
                'import_job_username': job_user_name,
                'exist_job_name': job.job_name,
                'exist_job_update_time': datetime.datetime.strftime(old_job_updated_time, "%Y-%m-%d %H:%M:%S"),
                'exist_job_username': job.author.username,
                'job_type': job.job_type,
            }
            diff_info_list.append(ret)
        except Exception as e:
            no_diff_job_name_list.append(job_name)
    return diff_info_list, no_diff_job_name_list


def write_job_info(job, jobs_info):
    inner_job_info = {
        "job_label": job.job_label,
        "update_time": date_format_transverter(job.updated_time, format='%Y-%m-%d %H:%M:%S:%f'),
        "job_name": job.job_name,
        "job_user_name": job.author.username
    }
    if inner_job_info not in jobs_info:
        jobs_info.append(inner_job_info)
    return jobs_info


def save_job(job_attr, job_path, import_tmp_dir):
    """
    单个job保存数据
    """
    try:
        job_label = job_attr.get('job_label')
        attr_dict = dict(
            job_label=job_attr.get('job_label'),
            job_name=job_attr.get('job_name'),
            job_type=job_attr.get('job_type'),
            job_second_type=job_attr.get('job_second_type', None),
            description=job_attr.get('description'),
            power_upper_limit=job_attr.get('power_upper_limit'),
            power_lower_limit=job_attr.get('power_lower_limit'),
            case_number=job_attr.get('case_number'),
            priority=job_attr.get('priority'),
            draft=job_attr.get('draft'),
            cabinet_type=job_attr.get('cabinet_type'),
            matching_rule=job_attr.get('matching_rule'),
            # job_import导入的draft默认True，更新完成，打包用例完成将job置为可用
            job_deleted=True,
            flow_execute_mode=job_attr.get('flow_execute_mode'),
            updated_time=job_attr.get('updated_time'),
            author=get_object_or_404(ReefUser, username=job_attr['author']['username'])
        )

        # 这里不筛选job_deleted字段，假删除job做update，不能执行create
        job_queryset = Job.objects.filter(job_label=job_label)
        if job_queryset:
            job_queryset.update(**attr_dict)
            job = job_queryset.first()
        else:
            job = Job.objects.create(**attr_dict)

        # save job flow
        # 记录inner_flow 原来关联的job_flow
        relevance_job_flow_id_list = []
        if job.job_type == JOB_TYPE_INNER_JOB:
            [relevance_job_flow_id_list.extend(job_flow.job_flow.all()) for job_flow in job.job_flow.all()]

        # job: job_flow = 1: n
        for job_flow in job.job_flow.all():
            job_flow.delete()

        for job_flow in job_attr['job_flow']:
            job_flow_path = os.path.join(job_path, job_flow['name'])
            ui_json_file = os.path.join(job_flow_path, 'ui.json')
            with open(ui_json_file, 'r') as f:
                file = InMemoryUploadedFile(f, None, "ui.json", None, None, None)
                job_flow_obj = JobFlow.custom_objects.create(
                    name=job_flow['name'],
                    ui_json_file=file,
                    flow_type=job_flow['flow_type'],
                    job=job,
                    order=job_flow['order'],
                    description=job_flow['description']
                )
                # import inner job。 维护更新inner job时 inner_flow 与原来 job_flow的关联关系
                if job.job_type == JOB_TYPE_INNER_JOB:
                    job_flow_obj.job_flow.add(*relevance_job_flow_id_list)
                else:
                    inner_job_label_list = job_flow.get('inner_flow')
                    # check inner job exists
                    job_label_list = Job.objects.filter(job_label__in=inner_job_label_list).values_list('job_label',
                                                                                                        flat=True)
                    lack_inner_job = set(inner_job_label_list) ^ set(list(job_label_list))
                    if len(lack_inner_job):
                        raise Exception(f"缺少 inner job: {lack_inner_job}")
                    inner_flow_queryset = JobFlow.objects.filter(job__job_label__in=inner_job_label_list)
                    job_flow_obj.inner_flow.add(*inner_flow_queryset)

            # job: res_file = 1: n
            for re_file in os.listdir(job_flow_path):
                # ui.json文件是job flow 使用的文件，不是resource file，资源文件不能命名为ui.json.
                # coral 使用的zip包中，job flow 使用的json文件被命名为ui.json
                if re_file == 'ui.json':
                    continue
                with open(os.path.join(job_flow_path, re_file), 'rb') as f:
                    file = InMemoryUploadedFile(f, None, re_file, None, None, None)
                    JobResourceFile.objects.create(name=re_file,
                                                   type=re_file.split('.')[-1],
                                                   file=file,
                                                   job_flow=job_flow_obj)

        # job: test_area = n: n
        job.test_area.clear()
        for test_area in job_attr['test_area']:
            obj, _ = JobTestArea.objects.get_or_create(description=test_area['description'])
            job.test_area.add(obj)

        # job: custom_tag = n: n
        job.custom_tag.clear()
        for custom_tag in job_attr['custom_tag']:
            obj, _ = CustomTag.objects.get_or_create(custom_tag_name=custom_tag['custom_tag_name'])
            job.custom_tag.add(obj)

        # job: android_version = n: n
        job.android_version.clear()
        for android_version in job_attr['android_version']:
            obj, _ = AndroidVersion.objects.get_or_create(version=android_version['version'])
            job.android_version.add(obj)

        # job: phone_model = n: n
        job.phone_models.clear()
        for phone_model in job_attr['phone_models']:
            manufacturer = phone_model['manufacturer']
            obj, _ = Manufacturer.objects.get_or_create(manufacturer_name=manufacturer['manufacturer_name'])
            obj, _ = PhoneModel.objects.get_or_create(phone_model_name=phone_model['phone_model_name'],
                                                      defaults={
                                                          'cpu_name': phone_model['cpu_name'],
                                                          'manufacturer': obj,
                                                          'x_border': phone_model['x_border'],
                                                          'y_border': phone_model['y_border'],
                                                          'x_dpi': phone_model['x_dpi'],
                                                          'y_dpi': phone_model['y_dpi']})
            job.phone_models.add(obj)

        # job: rom_version = n: n
        job.rom_version.clear()
        for rom_version in job_attr['rom_version']:
            manufacturer = rom_version['manufacturer']
            obj, _ = Manufacturer.objects.get_or_create(manufacturer_name=manufacturer['manufacturer_name'])
            obj, _ = RomVersion.objects.get_or_create(version=rom_version['version'],
                                                      defaults={'manufacturer': obj})
            job.rom_version.add(obj)

    except Exception as e:
        # 导入错误清除解压文件夹
        shutil.rmtree(import_tmp_dir)
        job_type = job_attr.get('job_type')
        if job_type == JOB_TYPE_INNER_JOB:
            return reef_500_response(description=f'全部用例导入失败',
                                     message=f'job import fail: {e}')
        else:
            return reef_500_response(description=f'非内嵌用例导入失败，如有内嵌用例已导入',
                                     message=f'job import fail: {e}')


def get_job_save(job_dir, job_name_list, import_tmp_dir):
    """
    保存inner job 或 job 列表中的job到系统中
    """
    job_label_lsit = []
    # 批量导入某一类job为一个事务
    with transaction.atomic():
        for job_name in job_name_list:
            try:
                p = Path(os.path.join(job_dir, job_name, 'job_attr.json'))
                job_path = os.path.join(job_dir, job_name)
                with p.open() as f:
                    job_attr = json.load(fp=f)
            except Exception as e:
                return reef_400_response(
                    description=f'压缩包缺少必要文件',
                    message=f'job import file: {e}'
                )
            # 保存数据
            save_job(job_attr, job_path, import_tmp_dir)

            job_label_lsit.append(job_attr.get('job_label'))
        return job_label_lsit


def compute_test_project_gather_count(func):
    def wrapper(test_project, test_gather_obj_list):
        old_gather_count = len(test_project.test_gather.all())
        func(test_project, test_gather_obj_list)
        new_gather_count = len(test_project.test_gather.all())
        change_num = new_gather_count - old_gather_count
        return change_num

    return wrapper


@compute_test_project_gather_count
def add_test_gather_to_project(test_project, test_gather_obj_list):
    # 测试集添加到项目中
    test_project.test_gather.add(*test_gather_obj_list)
    test_project.save(update_fields=['update_time'])
