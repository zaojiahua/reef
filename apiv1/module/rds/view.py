import copy
import re
import datetime
from operator import itemgetter

from django.db.models import F, Q, Count
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status, views
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request
from rest_framework.response import Response

from apiv1.core.cache import cache_dcr
from apiv1.core.constants import REDIS_CACHE_GET_RDS_RAPID, REDIS_COOLPAD_POWER_LAST_TIME
from apiv1.core.response import ReefResponse, reef_400_response
from apiv1.core.utils import SimilarityMatrixMonitor
from apiv1.core.view.generic import AutoExecuteSerializerGenericAPIView
from apiv1.module.device.models import Device, PhoneModel
from apiv1.module.job.models import Job
from apiv1.module.rds.models import Rds, RdsLog, RdsScreenShot
from apiv1.module.rds.serializer import RdsCreateOrUpdateSerializer, UploadRdsLogSerializer, UploadScreenShotSerializer, \
    RdsSerializer, GetRdsStatisticsDataSerializer, SortRdsScreenShotSerializer, RdsScreenShotSerializer, \
    FilterInvalidRdsSerializer, RdsScreenShotFileMultiUploadSerializer, UploadCoolPadPowerLastSerializer
from reef.settings import redis_pool_connect


def _swagger_extra_param():
    """
    add swagger parameter and parameter field type
    """
    tboard__id = openapi.Parameter('tboard__id', openapi.IN_QUERY, description="tboard id", type=openapi.TYPE_INTEGER)
    device__id__in = openapi.Parameter('device__id__in', openapi.IN_QUERY, description="device id",
                                       type=openapi.TYPE_INTEGER)
    job__id__in = openapi.Parameter('job__id__in', openapi.IN_QUERY, description="job id", type=openapi.TYPE_INTEGER)
    start_time__gt = openapi.Parameter('start_time__gt', openapi.IN_QUERY, description="start time greater than",
                                       type=openapi.TYPE_STRING)
    end_time__lt = openapi.Parameter('end_time__lt', openapi.IN_QUERY, description="end time less then",
                                     type=openapi.TYPE_STRING)
    job_assessment_value__in = openapi.Parameter('job_assessment_value__in', openapi.IN_QUERY,
                                                 description="job assessment value",
                                                 type=openapi.TYPE_STRING)
    device__phone_model__phone_model_name__in = openapi.Parameter('device__phone_model__phone_model_name__in',
                                                                  openapi.IN_QUERY,
                                                                  description="device phone model phone model name",
                                                                  type=openapi.TYPE_STRING)
    device__android_version__version__in = openapi.Parameter('device__android_version__version__in', openapi.IN_QUERY,
                                                             description="device android version version",
                                                             type=openapi.TYPE_STRING)
    device__phone_model__cpu_name__in = openapi.Parameter('device__phone_model__cpu_name__in', openapi.IN_QUERY,
                                                          description="device phone model cpu name",
                                                          type=openapi.TYPE_STRING)
    job__custom_tag__custom_tag_name__in = openapi.Parameter('job__custom_tag__custom_tag_name__in', openapi.IN_QUERY,
                                                             description="job custom tag custom tag name",
                                                             type=openapi.TYPE_STRING)
    ordering = openapi.Parameter('ordering', openapi.IN_QUERY, description="ordering", type=openapi.TYPE_STRING)

    param_list = [tboard__id, device__id__in, job__id__in, start_time__gt, end_time__lt, job_assessment_value__in,
                  device__phone_model__phone_model_name__in, device__android_version__version__in,
                  device__phone_model__cpu_name__in, job__custom_tag__custom_tag_name__in, ordering]

    return param_list


class GetRdsView(generics.GenericAPIView):
    """
    高效查询rds数据
    """

    def get(self, request):
        parameter = request.query_params
        if parameter is None:
            return Response({'error': 'missing parameter'}, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(parameter.dict(), dict):
            parameter_dict = parameter.dict()
        else:
            return Response({'error': 'Parameters Format Error'}, status=status.HTTP_400_BAD_REQUEST)

        # 将limit,offset参数剔除，后边filter查询直接使用 parameter_dict dict。
        if 'limit' in parameter_dict:
            parameter_dict.pop('limit')
        if 'offset' in parameter_dict:
            parameter_dict.pop('offset')

        # 筛选不等于的条件
        not_equal_parmeter = {}
        parameter_dict_copy = copy.deepcopy(parameter_dict)
        for parameter in parameter_dict_copy:
            if '!' in parameter:
                value = parameter_dict.pop(parameter)
                not_equal_parmeter[parameter.replace('!', '')] = value

        try:
            rds_queryset = Rds.objects.select_related('device', 'job').filter(**parameter_dict).exclude(**not_equal_parmeter)
        except Exception as e:
            return Response({'error': f'Parameter is not a table field: {e}'}, status=status.HTTP_400_BAD_REQUEST)

        # 对数据进行分页
        pagination = LimitOffsetPagination()
        rds_queryset = pagination.paginate_queryset(rds_queryset, request, view=None)

        data_list = []
        for rds in rds_queryset:
            result = {
                "device": {
                    "device_label": rds.device.device_label
                },
                "id": rds.id,
                "job": {
                    "job_label": rds.job.job_label,
                },
                "job_assessment_value": rds.job_assessment_value,
                "start_time": rds.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            data_list.append(result)
        results = {'rdss': data_list}
        return Response(results, status=status.HTTP_200_OK)


class FilterRdsValidityView(generics.GenericAPIView):
    """
    根据有效性查询rds数据
    """

    serializer_class = RdsSerializer

    def get(self, request):
        parameter_dict = request.query_params.dict()

        parameter_dict.pop('limit', None)
        parameter_dict.pop('offset', None)
        parameter_dict.pop('ordering', None)

        # 拼接参数
        job_assessment_value = parameter_dict.get('job_assessment_value!', None)
        q_parmeter = ''
        if job_assessment_value is not None:
            parameter_dict.pop('job_assessment_value!')
            q_parmeter = [f'~Q(job_assessment_value={v})' for v in job_assessment_value.split(',')]

        # in关系
        reeflist_re_pattern = re.compile(r'^ReefList\[.*\]$')
        parameter_dict_copy = copy.deepcopy(parameter_dict)
        for k, v in parameter_dict_copy.items():
            if re.match(reeflist_re_pattern, v) is not None:
                parameter_dict[k] = v[9:-1].split('{%,%}')

        # = 查询
        try:
            rds_queryset = Rds.objects.select_related('device', 'job').filter(**parameter_dict)
        except Exception as e:
            return Response({'error': f'Parameter is not a table field: {e}'}, status=status.HTTP_400_BAD_REQUEST)

        # != 查询
        if q_parmeter:
            try:
                rds_queryset = eval(f"rds_queryset.filter({'&'.join(q_parmeter)})")
            except Exception as e:
                return Response({'error': f'Parameter is not a table field: {e}'}, status=status.HTTP_400_BAD_REQUEST)
        # 排序
        if 'ordering' in request.query_params.dict():
            filter_ordering = OrderingFilter()
            rds_queryset = filter_ordering.filter_queryset(request, rds_queryset, self)
        # 分页
        if 'limit' in request.query_params.dict() or 'offset' in request.query_params.dict():
            pagination = LimitOffsetPagination()
            rds_queryset = pagination.paginate_queryset(rds_queryset, request, view=None)

        data_list = []
        for rds in rds_queryset:
            result = {
                "device": {
                    "id": rds.device.id,
                    "device_name": rds.device.device_name
                },
                "id": rds.id,
                "job": {
                    "id": rds.job.id,
                    "job_name": rds.job.job_name
                },
                "job_assessment_value": rds.job_assessment_value,
                "filter": rds.filter
            }
            data_list.append(result)
        results = {'rdss': data_list}
        return Response(results, status=status.HTTP_200_OK)


class GetRdsGroupByDeviceLabelView(generics.GenericAPIView):
    """
    根据Device.device_label分组，返回Rds信息
    """

    @swagger_auto_schema(manual_parameters=_swagger_extra_param(),
                         responses={200: "{'id':0,'job_assessment_value':'string','device_id':0}"})
    @action(detail=True, methods=['get'])
    def get(self, request: Request):

        """
        Example url params:
        tboard__id=12
        device__id__in=ReefList[1{%,%}2]
        job__id__in=ReefList[1]
        start_time__gt=2018-11-10 00:00:00
        end_time__lt=2018-12-11 23:59:59
        job_assessment_value__in=ReefList[0{%,%}1{%,%}-1]
        device__phone_model__phone_model_name__in=ReefList[]
        device__android_version__version__in=ReefList[]
        device__phone_model__cpu_name__in=ReefList[]
        job__custom_tag__custom_tag_name__in=ReefList[]
        ordering=-start_time
        """
        query_params = request.query_params
        tboard_id = query_params.get('tboard__id', None)
        device_ids = query_params.get('device__id__in', None)
        job_ids = query_params.get('job__id__in', None)
        start_time = query_params.get('start_time__gt', None)
        end_time = query_params.get('end_time__lt', None)
        job_assessment_values = query_params.get('job_assessment_value__in', None)
        phone_model_names = query_params.get('device__phone_model__phone_model_name__in', None)
        android_versions = query_params.get('device__android_version__version__in', None)
        cpu_names = query_params.get('device__phone_model__cpu_name__in', None)
        custom_tag_names = query_params.get('job__custom_tag__custom_tag_name__in', None)
        ordering = query_params.get('ordering', "-start_time")

        validate_pattern = re.compile('^ReefList\[.*\]$')

        # 解析参数结构
        device_ids = convert_str_param_to_list(
            validate_pattern,
            device_ids,
            'devices'
        )

        job_ids = convert_str_param_to_list(
            validate_pattern,
            job_ids,
            'jobs'
        )

        job_assessment_values = convert_str_param_to_list(
            validate_pattern,
            job_assessment_values,
            'job_assessment_values'
        )
        phone_model_names = convert_str_param_to_list(
            validate_pattern,
            phone_model_names,
            'phone_model_names'
        )
        android_versions = convert_str_param_to_list(
            validate_pattern,
            android_versions,
            'android_versions'
        )
        cpu_names = convert_str_param_to_list(
            validate_pattern,
            cpu_names,
            'cpu_names'
        )
        custom_tag_names = convert_str_param_to_list(
            validate_pattern,
            custom_tag_names,
            'custom_tag_names'
        )

        # filter 过滤结果集
        qs = Rds.objects.all()
        if tboard_id is not None:
            qs = qs.filter(tboard_id=tboard_id)
        if device_ids is not None:
            qs = qs.filter(device__id__in=device_ids)
        if job_ids is not None:
            qs = qs.filter(job__id__in=job_ids)
        if start_time is not None:
            qs = qs.filter(start_time__gt=start_time)
        if end_time is not None:
            qs = qs.filter(end_time__lt=end_time)
        if job_assessment_values is not None:
            qs = qs.filter(job_assessment_value__in=job_assessment_values)
        if phone_model_names is not None:
            qs = qs.filter(device__phone_model__phone_model_name__in=phone_model_names)
        if android_versions is not None:
            qs = qs.filter(device__android_version__version__in=android_versions)
        if cpu_names is not None:
            qs = qs.filter(device__phone_model__cpu_name__in=cpu_names)
        if custom_tag_names is not None:
            qs = qs.filter(job__custom_tag__custom_tag_name__in=custom_tag_names)

        # 根据device_label进行分组
        rdss = list(qs.annotate(
            device_label=F('device__device_label')
        ).values(
            'id', 'job_assessment_value', 'device_label', 'device_id'
        ).order_by(ordering))

        return_data = {}
        for rds in rdss:
            device_label = rds['device_label']
            if device_label not in return_data:
                return_data[device_label] = []
            return_data[device_label].append(
                {
                    'id': rds['id'],
                    'job_assessment_value': rds['job_assessment_value'],
                    'device_id': rds['device_id']
                }
            )

        return Response(return_data, status=status.HTTP_200_OK)


class GetRdsGroupByPhoneModelNameView(generics.GenericAPIView):
    """
    根据Device.phone_model分组，返回Rds信息
    """

    @swagger_auto_schema(manual_parameters=_swagger_extra_param(),
                         responses={200: "{'id':0,'job_assessment_value':string,'device_id':string}"})
    @action(detail=True, methods=['get'])
    def get(self, request: Request):
        """
        Example url params:
        &tboard__id=12
        &device__id__in=ReefList[1{%,%}2]
        &job__id__in=ReefList[1]
        &start_time__gt=2018-11-10 00:00:00
        &end_time__lt=2018-12-11 23:59:59
        &job_assessment_value__in=ReefList[0{%,%}1{%,%}-1]
        &device__phone_model__phone_model_name__in=ReefList[]
        &device__android_version__version__in=ReefList[]
        &device__phone_model__cpu_name__in=ReefList[]
        &job__custom_tag__custom_tag_name__in=ReefList[]
        &ordering=-start_time
        """
        query_params = request.query_params
        tboard_id = query_params.get('tboard__id', None)
        device_ids = query_params.get('device__id__in', None)
        job_ids = query_params.get('job__id__in', None)
        start_time = query_params.get('start_time__gt', None)
        end_time = query_params.get('end_time__lt', None)
        job_assessment_values = query_params.get('job_assessment_value__in', None)
        phone_model_names = query_params.get('device__phone_model__phone_model_name__in', None)
        android_versions = query_params.get('device__android_version__version__in', None)
        cpu_names = query_params.get('device__phone_model__cpu_name__in', None)
        custom_tag_names = query_params.get('job__custom_tag__custom_tag_name__in', None)
        ordering = query_params.get('ordering', '-start_time')
        validate_pattern = re.compile('^ReefList\[.*\]$')

        device_ids = convert_str_param_to_list(
            validate_pattern,
            device_ids,
            'devices'
        )

        job_ids = convert_str_param_to_list(
            validate_pattern,
            job_ids,
            'jobs'
        )

        job_assessment_values = convert_str_param_to_list(
            validate_pattern,
            job_assessment_values,
            'job_assessment_values'
        )
        phone_model_names = convert_str_param_to_list(
            validate_pattern,
            phone_model_names,
            'phone_model_names'
        )
        android_versions = convert_str_param_to_list(
            validate_pattern,
            android_versions,
            'android_versions'
        )
        cpu_names = convert_str_param_to_list(
            validate_pattern,
            cpu_names,
            'cpu_names'
        )
        custom_tag_names = convert_str_param_to_list(
            validate_pattern,
            custom_tag_names,
            'custom_tag_names'
        )

        # filter结果集
        qs = Rds.objects.all()
        if tboard_id is not None:
            qs = qs.filter(tboard_id=tboard_id)
        if device_ids is not None:
            qs = qs.filter(device__id__in=device_ids)
        if job_ids is not None:
            qs = qs.filter(job__id__in=job_ids)
        if start_time is not None:
            qs = qs.filter(start_time__gt=start_time)
        if end_time is not None:
            qs = qs.filter(end_time__lt=end_time)
        if job_assessment_values is not None:
            qs = qs.filter(job_assessment_value__in=job_assessment_values)
        if phone_model_names is not None:
            qs = qs.filter(device__phone_model__phone_model_name__in=phone_model_names)
        if android_versions is not None:
            qs = qs.filter(device__android_version__version__in=android_versions)
        if cpu_names is not None:
            qs = qs.filter(device__phone_model__cpu_name__in=cpu_names)
        if custom_tag_names is not None:
            qs = qs.filter(job__custom_tag__custom_tag_name__in=custom_tag_names)

        # 根据phone_model_name进行分组
        rdss = list(qs.annotate(
            phone_model_name=F('device__phone_model__phone_model_name')
        ).values(
            'id', 'job_assessment_value', 'phone_model_name', 'device_id'
        ).order_by(ordering))

        return_data = {}
        for rds in rdss:
            phone_model_name = rds['phone_model_name']
            # 对phone_model_name去重
            if phone_model_name not in return_data:
                return_data[phone_model_name] = []
            return_data[phone_model_name].append(
                {
                    'id': rds['id'],
                    'job_assessment_value': rds['job_assessment_value'],
                    'device_id': rds['device_id']
                }
            )

        return Response(return_data, status=status.HTTP_200_OK)


class GetRdsRapidView(generics.GenericAPIView):
    """
    取得Rds信息
    """

    @swagger_auto_schema(manual_parameters=_swagger_extra_param(), )
    @action(detail=True, methods=['get'])
    @cache_dcr(key_leading=REDIS_CACHE_GET_RDS_RAPID, ttl_in_second=3)
    def get(self, request):
        """
        To resolve performance issue, customize rds list api to improve that
        """
        """
        Example url params:

        fields=id,
            device,
            device.device_name,
            device.device_label,
            job_assessment_value,
            device.phone_model,
            device.phone_model.phone_model_name
        &device__phone_model__phone_model_name=ReefList[]
        &device__android_version__version=ReefList[]
        &device__phone_model__cpu_name=ReefList[]
        &job__custom_tag__custom_tag_name=ReefList[]
        &tboard__id=12
        &device__id__in=ReefList[1{%,%}2]
        &job__id__in=ReefList[1]
        &start_time__gt=2018-11-10 00:00:00
        &end_time__lt=2018-12-11 23:59:59
        &job_assessment_value__in=ReefList[0{%,%}1{%,%}-1]
        """
        query_params = request.query_params
        tboard_id = query_params.get('tboard__id', None)
        device_ids = query_params.get('device__id__in', None)
        job_ids = query_params.get('job__id__in', None)
        start_time = query_params.get('start_time__gt', None)
        end_time = query_params.get('end_time__lt', None)
        job_assessment_values = query_params.get('job_assessment_value__in', None)
        phone_model_names = query_params.get('device__phone_model__phone_model_name__in', None)
        android_versions = query_params.get('device__android_version__version__in', None)
        cpu_names = query_params.get('device__phone_model__cpu_name__in', None)
        custom_tag_names = query_params.get('job__custom_tag__custom_tag_name__in', None)
        validate_pattern = re.compile('^ReefList\[.*\]$')

        device_ids = convert_str_param_to_list(
            validate_pattern,
            device_ids,
            'devices'
        )

        job_ids = convert_str_param_to_list(
            validate_pattern,
            job_ids,
            'jobs'
        )

        job_assessment_values = convert_str_param_to_list(
            validate_pattern,
            job_assessment_values,
            'job_assessment_values'
        )
        phone_model_names = convert_str_param_to_list(
            validate_pattern,
            phone_model_names,
            'phone_model_names'
        )
        android_versions = convert_str_param_to_list(
            validate_pattern,
            android_versions,
            'android_versions'
        )
        cpu_names = convert_str_param_to_list(
            validate_pattern,
            cpu_names,
            'cpu_names'
        )
        custom_tag_names = convert_str_param_to_list(
            validate_pattern,
            custom_tag_names,
            'custom_tag_names'
        )

        qs = Rds.objects.all()
        if tboard_id is not None:
            qs = qs.filter(tboard_id=tboard_id)
        if device_ids is not None:
            qs = qs.filter(device__id__in=device_ids)
        if job_ids is not None:
            qs = qs.filter(job__id__in=job_ids)
        if start_time is not None:
            qs = qs.filter(start_time__gt=start_time)
        if end_time is not None:
            qs = qs.filter(end_time__lt=end_time)
        if job_assessment_values is not None:
            qs = qs.filter(job_assessment_value__in=job_assessment_values)
        if phone_model_names is not None:
            qs = qs.filter(device__phone_model__phone_model_name__in=phone_model_names)
        if android_versions is not None:
            qs = qs.filter(device__android_version__version__in=android_versions)
        if cpu_names is not None:
            qs = qs.filter(device__phone_model__cpu_name__in=cpu_names)
        if custom_tag_names is not None:
            qs = qs.filter(job__custom_tag__custom_tag_name__in=custom_tag_names)
        qs = qs.values('id', 'device', 'job_assessment_value', 'job_id')
        # 过滤掉没有运行完成的rds
        qs = qs.exclude(job_assessment_value='')

        devices = Device.objects.all()
        if device_ids is not None:
            devices = Device.objects.filter(id__in=device_ids)
        devices = devices.values('id', 'device_label', 'device_name', 'phone_model')

        phone_model_ids = {device['phone_model'] for device in devices}
        phone_models = PhoneModel.objects.filter(id__in=phone_model_ids).values('id', 'phone_model_name')
        # parse phone_models to id:phone_model_name dict
        phone_models = {phone_model['id']: phone_model['phone_model_name'] for phone_model in phone_models}
        # parse devices to id:(device_label, device_name) dict
        devices = {device['id']: (device['device_label'], device['device_name'], device['phone_model'])
                   for device in devices}

        return_data = {
            'rdss': [
                {
                    'id': rds['id'],
                    'job_assessment_value': rds['job_assessment_value'],
                    'device': {
                        'id': rds['device'],
                        'device_label': devices[rds['device']][0],
                        'device_name': devices[rds['device']][1],
                        'phone_model': {
                            'phone_model_name': phone_models[devices[rds['device']][2]]
                        } if devices[rds['device']][2] is not None else None
                    },
                    'job': {
                        'id': rds['job_id']
                    }
                } for rds in qs
            ]
        }
        return Response(return_data, status=status.HTTP_200_OK)


class RdsCreateOrUpdateView(generics.GenericAPIView):
    """
    Coral创建, Rds时所使用的接口, 更新rds操作的需求被移除
    """
    serializer_class = RdsCreateOrUpdateSerializer

    def post(self, request):
        serializer = RdsCreateOrUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rds = serializer.save()
        # rds = Rds.objects.create(**serializer.validated_data)
        return Response({'id': rds.id}, status=status.HTTP_200_OK)


class UploadRdsLogView(generics.GenericAPIView):
    """
    RdsLog 上传接口
    """
    serializer_class = UploadRdsLogSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            rds = Rds.objects.get(
                job=serializer.validated_data['job'],
                device=serializer.validated_data['device'],
                start_time=serializer.validated_data['start_time']
            )
        except Rds.DoesNotExist:
            return Response({"message": "Rds with doesn't exist"}, status=status.HTTP_404_NOT_FOUND)

        RdsLog.objects.create(
            rds=rds,
            log_file=serializer.validated_data['log_file'],
            file_name=serializer.validated_data['file_name']
        )

        return ReefResponse()


class UploadRdsScreenShotView(generics.GenericAPIView):
    """
    RdsScreen-shot上传接口
    """
    serializer_class = UploadScreenShotSerializer

    def post(self, request):
        serializer = UploadScreenShotSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            rds = Rds.objects.get(device=serializer.validated_data['device'],
                                  job=serializer.validated_data['job'],
                                  start_time=serializer.validated_data['start_time'])
        except Rds.DoesNotExist:
            return Response({"message": "Rds doesn't exist"}, status=status.HTTP_404_NOT_FOUND)

        RdsScreenShot.objects.create(
            rds=rds,
            img_file=serializer.validated_data['rds_screen_shot'],
            file_name=serializer.validated_data['file_name']
        )
        return Response(status=status.HTTP_201_CREATED)


class GetRdsStatisticsData(generics.GenericAPIView):
    """
    根据tboard, device, job，统计 rds
    通过，失败，无效率
    """
    serializer_class = GetRdsStatisticsDataSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request_data = serializer.validated_data
        rds_queryset = Rds.objects.filter(**request_data)
        if not rds_queryset.exists():
            return Response(get_response_data(), status=status.HTTP_200_OK)
        rds_count = rds_queryset.count()
        pass_rds_count = rds_queryset.filter(job_assessment_value='0').count()
        fail_rds_count = rds_queryset.filter(job_assessment_value='1').count()
        response_data = get_response_data(rds_count=rds_count, rds_percentage=100, pass_rds_count=pass_rds_count,
                                          pass_rds_percentage=round(pass_rds_count / rds_count, 2),
                                          fail_rds_count=fail_rds_count, fail_rds_percentage=round(fail_rds_count / rds_count, 2),
                                          invalid_rds_count=rds_count - pass_rds_count - fail_rds_count,
                                          invalid_rds_percentage=round((rds_count - pass_rds_count - fail_rds_count) / rds_count, 2))
        return Response(response_data, status=status.HTTP_200_OK)


class GetSimilarityMatrix(views.APIView):

    def get(self, request):
        similarity_matrix = SimilarityMatrixMonitor()
        similarity_matrix.device_queryset = Device.objects.all()
        similarity_matrix.job_queryset = Job.objects.filter(job_deleted=False, job_type='Joblib').order_by('id')
        similarity_matrix.rds_queryset = Rds.objects.filter(start_time__gt=timezone.now() - datetime.timedelta(days=5),
                                                            end_time__lt=timezone.now(),
                                                            created_by_ai_tester=False).exclude(job__job_deleted=True)
        similarity_matrix_data, device_label_list, job_label_list = similarity_matrix.calculate_matrix(similarity_matrix.rds_queryset)
        results = {
            'matrix_data': similarity_matrix_data,
            'device_label_list': device_label_list,
            'job_label_list': job_label_list
        }
        return Response(results, status=status.HTTP_200_OK)


class GetJobFeatureMatrix(views.APIView):

    def get(self, request):
        similarity_matrix = SimilarityMatrixMonitor()
        similarity_matrix.job_queryset = Job.objects.filter(job_deleted=False, job_type='Joblib').order_by('id')
        job_feature_pd, job_label_list = similarity_matrix.form_job_feature_matrix()
        similarity_matrix.deal_with_multi_item(job_feature_pd.loc[:, similarity_matrix._muti_item_name].values,
                                               job_label_list)
        similarity_matrix.deal_with_str_item(similarity_matrix.job_feature_df.loc[:, "author"], "author")
        similarity_matrix._deal_with_abnormal_item(similarity_matrix.job_feature_df)
        return Response(similarity_matrix.job_feature_df.to_dict(orient="split"), status=status.HTTP_200_OK)


class SortRdsScreenShotView(generics.GenericAPIView):

    queryset = Rds.objects.all()
    serializer_class = SortRdsScreenShotSerializer

    def get(self, request):
        """
        当前存在两种文件名称格式
        (flow_6750)_(6_4)ocr-0.93222.png
        (flow_6750)_(inner_13)_(1_5)ocr-0.62768.png
        """
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        rds = serializer.validated_data.get('rds', None)
        rds_screen_shot_queryset = RdsScreenShot.objects.filter(rds=rds, is_resource_file=False)
        pattern = re.compile(r'[(](.*?)[)]', re.S)
        sort_data_list = []
        file_name_except_list = []
        for rds_screen_shot in rds_screen_shot_queryset:
            re_res = pattern.findall(rds_screen_shot.file_name)
            if len(re_res) < 2:
                file_name_except_list.append(rds_screen_shot)    # file name except
                continue
            order_data = [rds_screen_shot]
            try:
                # 提取文件名中的数字要转为int类型，str状态下，10会在2前边
                for index, item in enumerate(re_res):
                    if index == 0:
                        flow_id = item.split('_')[1]
                        order_data.append(int(flow_id))
                    if index == 1:
                        if 'inner_' in item:
                            two_data = item.split('_')[1]
                            order_data.extend([int(two_data), 1])
                        else:
                            order_data.extend([int(i) for i in item.split('_')])
                    if index == 2:
                        order_data.extend([int(i) for i in item.split('_')])
                    # 补全非inner job数据，统一补全为1_1
                    if index == 1 and len(re_res) <= 2:
                        order_data.extend([1, 1])
                sort_data_list.append(order_data)
            except:
                file_name_except_list.append(rds_screen_shot)    # file name except
        res_list = sorted(sort_data_list, key=itemgetter(1, 2, 3, 4, 5), reverse=serializer.validated_data['reverse'])
        results = [
            RdsScreenShotSerializer(res[0]).data
            for res in res_list
        ]
        if file_name_except_list:
            except_list = [
                RdsScreenShotSerializer(res).data
                for res in file_name_except_list
            ]
            results.extend(except_list)
        return ReefResponse(data=results)


class FilterInvalidRdsView(generics.GenericAPIView):

    serializer_class = FilterInvalidRdsSerializer
    queryset = Rds.objects.all()

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = serializer.validated_data.get('job_id', None)
        device = serializer.validated_data.get('device_id', None)
        tboard = serializer.validated_data.get('tboard_id', None)
        reverse = serializer.validated_data.get('reverse', False)

        rds_queryset = Rds.objects.filter(tboard=tboard).exclude(job_assessment_value__in=['0', '1'])
        if job:
            rds_queryset = rds_queryset.filter(job=job)
        if device:
            rds_queryset = rds_queryset.filter(device=device)
        rds_data = rds_queryset.values('job_assessment_value').annotate(count=Count('job_assessment_value'))
        res_data = sorted(rds_data, key=lambda x: x['count'], reverse=reverse)
        return ReefResponse(data=res_data)


class RdsScreenShotFileMultiUploadView(AutoExecuteSerializerGenericAPIView):
    """
    批量上传 rds screen shot file
    """
    serializer_class = RdsScreenShotFileMultiUploadSerializer

    def post(self, request):
        serializer = self.execute(request)
        re_file = serializer.save()
        return Response(re_file, status=status.HTTP_201_CREATED)


class UploadCoolPadPowerLastView(AutoExecuteSerializerGenericAPIView):
    """
    upload coolpad power last
    """

    serializer_class = UploadCoolPadPowerLastSerializer

    def post(self, request):
        serializer = self.execute(request)
        tboard = serializer.validated_data.get('tboard')
        device = serializer.validated_data.get('device')
        standby_time = serializer.validated_data.get('standby_time', 0)
        redis_key = f"{REDIS_COOLPAD_POWER_LAST_TIME}:{tboard.id}:{device.device_label}"
        now_time = timezone.localtime()
        day = now_time.day
        year = now_time.year
        month = now_time.month
        # 2:30 作为续航计算开始时间，酷派指定。
        time_zone = timezone.get_current_timezone()
        start_time = timezone.datetime(year, month, day, 2, 30, tzinfo=time_zone)

        if (now_time - start_time).days < 0:
            # 当前时间小于开始时间，数据无效。val = -1
            seconds = -1
        else:
            seconds = (now_time - start_time).seconds

        if seconds > 0:
            # 任务前台运行时长： 续航 - 待机时长
            # 待机时间： 待机时间 + 4 小时（2:00 - 6:00 待机）
            standby_time = standby_time + 14400
            task_run_time = seconds - standby_time
            task_run_time = task_run_time if task_run_time > 0 else -1
        else:
            task_run_time = -1
            standby_time = -1
        redis_val = {
            'power_last_time': seconds,
            'task_run_time': task_run_time,
            'standby_time': standby_time,
            'start_time': timezone.datetime.strftime(start_time, "%Y-%m-%d %H:%M:%S"),
            'now_time': timezone.datetime.strftime(now_time, "%Y-%m-%d %H:%M:%S")
        }
        redis_pool_connect.hmset(
            redis_key,
            redis_val,
        )
        redis_pool_connect.expire(redis_key, 3600 * 24)

        return ReefResponse()


#####################################################
# helper function                                   #
#####################################################

def validate_list_param(param):
    # 解析正则匹配ReefList规则
    m = re.match('ReefList\[.*\]', param)
    return m is not None


def convert_str_param_to_list(validate_pattern, items_str, item_name):
    # 解析参数规则，str 转 list
    if items_str is not None:
        if re.match(validate_pattern, items_str) is None:
            return Response(f'format of {item_name} list is invalid!',
                            content_type='text/plain', status=status.HTTP_400_BAD_REQUEST)
        return items_str[9:-1].split('{%,%}')
    return None


def get_response_data(rds_count=0, rds_percentage=0, pass_rds_count=0, pass_rds_percentage=0, fail_rds_count=0, fail_rds_percentage=0,
                      invalid_rds_count=0, invalid_rds_percentage=0):
    # 拼接rds 数据
    response_data = {
        "rds_count": rds_count,
        "rds_percentage": rds_percentage,
        "pass_rds_count": pass_rds_count,
        "pass_rds_percentage": pass_rds_percentage,
        "fail_rds_count": fail_rds_count,
        "fail_rds_percentage": fail_rds_percentage,
        "invalid_rds_count": invalid_rds_count,
        "invalid_rds_percentage": invalid_rds_percentage
    }
    return response_data


