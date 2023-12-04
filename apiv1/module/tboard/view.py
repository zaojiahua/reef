import collections, copy, re, time, os
import math
import random
from datetime import datetime
from typing import List, Dict
from pathlib import Path
from functools import reduce

import requests
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import QuerySet, Count, Q
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from apiv1.core.cache import cache_dcr
from apiv1.core.constants import JOB_TYPE_UNIQ, POWER_CONSUMPTION_ERROR_CODE, TEMP_CONSUMPTION_ERROR_CODE, \
    TBOARD_DELETE_FAIL_GROUP, REDIS_TBOARD_DELETE, REDIS_TBOARD_DELETE_FAIL, REDIS_CACHE_GET_TBOARD_STATISTIC, \
    DEVICE_STATUS_IDLE, DEVICE_STATUS_BUSY, COOLPAD_GET_CRUMB, COOLPAD_UPLOAD_TBOARD_DATA
from apiv1.core.factory import init_open_module_factory, check_func_execute
from apiv1.core.request import ReefRequest
from apiv1.core.response import reef_400_response, ReefResponse, reef_500_response
from apiv1.core.status import StatusCode
from apiv1.core.utils import update_device_matching_rule, OpenAPIAnonRateThrottle, date_format_transverter, ReefLogger, \
    join_path
from apiv1.core.tool import Checkout, ReefFTP
from apiv1.core.view.generic import AutoExecuteSerializerGenericAPIView
from apiv1.module.device.models import Device, DevicePower, DeviceTemperature
from apiv1.module.device.signal import update_device_status
from apiv1.module.job.models import Job, JobParameter
from apiv1.module.rds.models import Rds
from apiv1.module.system.models import Cabinet
from apiv1.module.tboard.models import TBoard
from apiv1.module.tboard.serializer import CreateTBoardSerializer, EndTBoardSerializer, TBoardRunningDetailSerializer, \
    GetTboardStatisticsSerializer, GetJobPriorTboardSerializer, RepeatExecuteTBoardSerializer, \
    GetTBoardFieldsSerializer, TBoardSerializer, CreateRepeatTBoardSerializer, RepeatExecuteTBoardCheckSerializer, \
    ReleaseBusyDeviceSerializer, CoolPadCreateTBoardSerializer, OpenCreateTBoardSerializer
from apiv1.module.tboard.tasks.tasks import get_hash_data_in_redis, sorted_data, tboard_delete, \
    prepare_tboard_report_cache
from reef import settings
from reef.settings import redis_connect, JOB_RES_FILE_EXPORT_PATH, MEDIA_ROOT


class CreateTBoardView(generics.GenericAPIView):
    """
    Coral创建任务时，会呼叫此接口
    """
    serializer_class = CreateTBoardSerializer
    queryset = TBoard.objects.all()

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tboard = serializer.save()
        return Response(
            {'id': tboard.id},
            status=status.HTTP_201_CREATED
        )


class EndTBoardView(generics.GenericAPIView):
    """
    Coral结束任务运行时，会呼叫此接口
    """
    serializer_class = EndTBoardSerializer
    queryset = TBoard.objects.all()

    def put(self, request, pk):
        tboard = self.get_object()
        serializer = self.get_serializer(tboard, data=request.data)
        serializer.is_valid(raise_exception=True)
        tboard = serializer.update(tboard, serializer.validated_data)

        """
        如果该TBoard中包含Uniq类的Job, 将此Tboard视为Uniq类的TBoard
        对于Uniq类的Tboard来说，完成任务时自动计算该用例的耗电量/温度，并
        对应记录至Rds.power_consumption/Rds.temp_consumption中。


        Rds的开始/结束电量/温度查询逻辑: 
        开始: 开始前1min内，最接近rds.start_time的电量/温度数据
        结束: 结束后1min内，最接近rds.end_time的电量/温度数据

        _ Rds开始前1 min
        |                       DevicePower/DeviceTemp 1
        | 
        |                       DevicePower/DeviceTemp 2   <====取用该数据
        ___ Rds开始
        |
        |
        |
        |
        |
        |
        ___ Rds结束
        |                       DevicePower/DeviceTemp 3   <=====取用该数据
        |
        |                       DevicePower/DeviceTemp 4
        _ Rds结束后 1 min

        若范围内查无电量/温度信息，则视为数据异常处理。
        """
        if tboard.finished_flag:
            search_timedelta = timezone.timedelta(minutes=1)
            # Not uniq job in tboard, Not compute power data and temp data
            if not Job.objects.filter(tboardjob__tboard_id=tboard.id).filter(job_type=JOB_TYPE_UNIQ).exists():
                if tboard.belong == 'coolpad':
                    obj = init_open_module_factory(tboard.belong)
                    check_func_execute(obj, 'handle_tboard_data', tboard)
                    check_func_execute(obj, 'end_tboard_upload_data', tboard)
                    check_func_execute(obj, 'crete_statistics_xlsx', tboard)
                return Response(self.get_serializer(tboard).data)

            devices: List[int] = Device.objects. \
                filter(tboard=tboard.id). \
                order_by("id"). \
                values_list("id", flat=True)

            rdss: List[Dict] = Rds.objects. \
                filter(tboard=tboard.id). \
                filter(device__in=devices). \
                filter(job__job_type=JOB_TYPE_UNIQ). \
                order_by("device_id", "start_time"). \
                values("id", "device_id", "start_time", "end_time")

            if len(rdss) == 0:
                return Response(self.get_serializer(tboard).data)

            start_time: datetime = min(rdss, key=lambda item: item["start_time"])["start_time"]
            end_time: datetime = max(rdss, key=lambda item: item["end_time"])["end_time"]

            devicepowers: List[Dict] = DevicePower.objects. \
                filter(record_datetime__gte=start_time - search_timedelta). \
                filter(record_datetime__lte=end_time + search_timedelta). \
                filter(device_id__in=devices). \
                order_by("device_id", "record_datetime"). \
                values("device_id", "battery_level", "record_datetime")

            time.sleep(1)  # device temperature 每隔1s往数据库推送一次数据
            devicetemps: List[Dict] = DeviceTemperature.objects. \
                filter(record_datetime__gte=start_time - search_timedelta). \
                filter(record_datetime__lte=end_time + search_timedelta). \
                filter(device_id__in=devices). \
                order_by("device_id", "record_datetime"). \
                values("device_id", "temperature", "record_datetime")

            update_list = []
            for rds in rdss:
                start_battery_level = None
                end_battery_level = None
                start_temperature = None
                end_temperature = None

                # device_power
                for i in range(len(devicepowers) - 1, -1, -1):
                    devicepower = devicepowers[i]
                    if rds["device_id"] == devicepower["device_id"]:
                        if _time_in_range(
                                devicepower["record_datetime"],
                                rds["start_time"],
                                rds["start_time"] - search_timedelta):
                            start_battery_level = devicepower["battery_level"]
                            break

                for i in range(0, len(devicepowers)):
                    devicepower = devicepowers[i]
                    if rds["device_id"] == devicepower["device_id"]:
                        if _time_in_range(
                                devicepower["record_datetime"],
                                rds["end_time"],
                                rds["end_time"] + search_timedelta):
                            end_battery_level = devicepower["battery_level"]
                            break

                # device_temp
                for i in range(len(devicetemps) - 1, -1, -1):
                    devicetemp = devicetemps[i]
                    if rds["device_id"] == devicetemp["device_id"]:
                        if _time_in_range(
                                devicetemp["record_datetime"],
                                rds["start_time"],
                                rds["start_time"] - search_timedelta):
                            start_temperature = devicetemp["temperature"]
                            break

                for i in range(0, len(devicetemps)):
                    devicetemp = devicetemps[i]
                    if rds["device_id"] == devicetemp["device_id"]:
                        if _time_in_range(
                                devicetemp["record_datetime"],
                                rds["end_time"],
                                rds["end_time"] + search_timedelta):
                            end_temperature = devicetemp["temperature"]
                            break

                update_list.append(
                    Rds(
                        id=rds["id"],
                        power_consumption=POWER_CONSUMPTION_ERROR_CODE
                        if start_battery_level is None or end_battery_level is None
                        else start_battery_level - end_battery_level,
                        temp_consumption=TEMP_CONSUMPTION_ERROR_CODE
                        if start_temperature is None or end_temperature is None
                        else start_temperature - end_temperature
                    )
                )

            Rds.objects.bulk_update(update_list, ("power_consumption", "temp_consumption"), batch_size=100)

            # 预热统计缓存
            prepare_tboard_report_cache.delay(tboard.id)
        return Response(self.get_serializer(tboard).data)


class GetTboardRunningDetailView(generics.GenericAPIView):
    """
    取得tboard的细节运行结果
    """
    serializer_class = TBoardRunningDetailSerializer
    tboard_id = openapi.Parameter('tboard_id', openapi.IN_QUERY, description="tboard id", type=openapi.TYPE_INTEGER)

    @swagger_auto_schema(manual_parameters=[tboard_id])
    @action(detail=True, methods=['get'])
    def get(self, request: Request):

        tboard_id = request.query_params.get('tboard_id', None)
        if tboard_id is None:
            return Response({'error': 'Need url param "tboard_id"!'}, status=status.HTTP_400_BAD_REQUEST)

        assert str.isdigit(tboard_id)

        tboard = get_object_or_404(TBoard.objects.all(), pk=tboard_id)
        return_data = TBoardRunningDetailSerializer(instance=tboard).data

        # 对job数据进行去重处理
        jobs = []
        _ = [jobs.append(job) for job in return_data['jobs'] if job not in jobs]
        return_data['jobs'] = jobs

        job_totals = _to_dict(Rds.objects.filter(
            tboard=tboard_id,
            end_time__isnull=False
        ).values(
            'job_id'
        ).annotate(
            total=Count('job_id'),
        ), 'job_id', 'total')

        job_passses = _to_dict(Rds.objects.filter(
            tboard=tboard_id,
            end_time__isnull=False,
        ).values(
            'job_id'
        ).annotate(
            passs=Count('job_id', filter=Q(job_assessment_value='0')),
        ), 'job_id', 'passs')

        job_fails = _to_dict(Rds.objects.filter(
            tboard=tboard_id,
            end_time__isnull=False,
        ).values(
            'job_id'
        ).annotate(
            fail=Count('job_id', filter=Q(job_assessment_value='1')),
        ), 'job_id', 'fail')

        devices = _to_dict(Device.objects.filter(
            tboard=tboard_id
        ).values('id', 'device_name'), 'id', 'device_name')

        device_passses = _to_dict(Rds.objects.filter(
            tboard=tboard_id,
            end_time__isnull=False
        ).values(
            'device_id', 'job_id'
        ).annotate(
            passs=Count('device_id', filter=Q(job_assessment_value='0'))
        ), ('device_id', 'job_id'), 'passs')

        device_fails = _to_dict(Rds.objects.filter(
            tboard=tboard_id,
            end_time__isnull=False
        ).values(
            'device_id', 'job_id'
        ).annotate(
            fail=Count('device_id', filter=Q(job_assessment_value='1'))
        ), ('device_id', 'job_id'), 'fail')

        device_nas = _to_dict(Rds.objects.filter(
            tboard=tboard_id,
            end_time__isnull=False
        ).values(
            'device_id', 'job_id'
        ).annotate(
            na=Count('device_id', filter=~(Q(job_assessment_value='0') | Q(job_assessment_value='1')))
        ), ('device_id', 'job_id'), 'na')

        for job in return_data['jobs']:
            job_id = job.get('id')
            job['total'] = job_totals.get(job_id, 0)
            job['pass'] = job_passses.get(job_id, 0)
            job['fail'] = job_fails.get(job_id, 0)
            job['na'] = job['total'] - job['pass'] - job['fail']
            job['failure'] = float(
                '{:.2f}'.format(
                    job['fail'] / (job['pass'] + job['fail'])
                )
            ) if job['pass'] + job['fail'] > 0 else 0
            job['devices'] = []

            for device in return_data['devices']:
                device_id = device['id']
                key = (device_id, job_id)
                passs = device_passses.get(key, None)
                fail = device_fails.get(key, None)
                na = device_nas.get(key, None)
                if (passs is None) and (fail is None) and (na is None):
                    continue
                device['has_rds'] = True
                dic = {
                    'id': device_id,
                    'device_name': devices.get(device_id),
                    'pass': passs,
                    'fail': fail,
                    'na': na
                }
                job['devices'].append(dic)

            return_data['devices'] = [device for device in return_data['devices'] if device['has_rds']]

        return Response(return_data, status=status.HTTP_200_OK)


class GetTboardStatisticsView(generics.GenericAPIView):
    """
    取得tboard的整体统计结果
    """
    serializer_class = GetTboardStatisticsSerializer
    tboard_id = openapi.Parameter('tboard_id', openapi.IN_QUERY, description="tboard id", type=openapi.TYPE_INTEGER)

    @swagger_auto_schema(manual_parameters=[tboard_id])
    @action(detail=True, methods=['get'])
    @cache_dcr(key_leading=REDIS_CACHE_GET_TBOARD_STATISTIC, ttl_in_second=300)
    def get(self, request: Request):
        tboard_id = request.query_params.get('tboard_id', None)
        if tboard_id is None:
            return Response({'error': 'Need url param "tboard_id"!'}, status=status.HTTP_400_BAD_REQUEST)

        tboard = get_object_or_404(TBoard.objects.all(), id=tboard_id)
        tboard_statistics = TBoard.objects.filter(
            id=tboard_id,
            rds__end_time__isnull=False
        ).aggregate(
            total=Count('rds'),
            success=Count('rds', Q(rds__job_assessment_value='0')),
            fail=Count('rds', Q(rds__job_assessment_value='1')),
        )
        for k, v in tboard_statistics.items():
            setattr(tboard, k, v)
        tboard.na = tboard_statistics['total'] - tboard_statistics['success'] - tboard_statistics['fail']
        tboard.failure = tboard_statistics['fail'] / (tboard_statistics['success'] + tboard_statistics['fail']) \
            if (tboard_statistics['success'] + tboard_statistics['fail']) != 0 else 0
        tboard.failure = f'{tboard.failure:.2f}'

        return Response(GetTboardStatisticsSerializer(instance=tboard).data)


class GetTboardProgressView(generics.GenericAPIView):
    """
    取得tboard运行的进度，
    Tboard的进度定义如下:
    已产生的RDS的数量（不包含正在产生的RDS）/job数量*device数量*任务中配置的轮数
    其中，Rds，Job，Device皆是指关联至该TBoard的相应资源
    """
    tboards = openapi.Parameter('tboards', openapi.IN_QUERY, description="tboards", type=openapi.TYPE_INTEGER)

    @swagger_auto_schema(manual_parameters=[tboards])
    @action(detail=True, methods=['get'])
    def get(self, request):
        tboards = request.query_params.get('tboards', None)
        if tboards is None:
            return Response({'error': 'Need url param "tboards"!'}, status=status.HTTP_400_BAD_REQUEST)

        tboards = re.sub('[^0-9]', ' ', tboards)
        tboard_ids_list = tboards.split()
        tboard_ids = list(map(int, set(tboard_ids_list)))
        tboard_queryset = TBoard.objects.all()
        job_queryset = Job.objects.all()
        device_queryset = Device.objects.all()
        if not tboard_ids:
            return Response({'error': 'Lack of effective tboard id'}, status=status.HTTP_400_BAD_REQUEST)

        # 根据tboard分组获取完成的rds数量
        rds_queryset = list(
            Rds.objects.filter(tboard_id__in=tboard_ids).exclude(end_time=None).values('tboard_id').annotate(
                rds_finished_count=Count('tboard_id')))
        # 将还没有rds数据的tboard 添加到查询列表中
        if len(rds_queryset) != len(tboard_ids):
            # 比较差值
            start_execute_tboard_list = [tboard['tboard_id'] for tboard in rds_queryset]
            for tboard_id in tboard_ids:
                if tboard_id not in start_execute_tboard_list:
                    rds_queryset.append({'tboard_id': tboard_id, 'rds_finished_count': 0})

        results = []
        for tboard_data in rds_queryset:
            result = {}
            finished_flag = tboard_queryset.filter(id=tboard_data['tboard_id']).values_list('finished_flag',
                                                                                            flat=True).first()
            # tboard 完成不需要计算进度
            if finished_flag:
                progress = 1
            else:
                job_count = job_queryset.filter(tboard=tboard_data['tboard_id']).count()
                device_count = device_queryset.filter(tboard=tboard_data['tboard_id']).count()
                repeat_time = tboard_queryset.filter(id=tboard_data['tboard_id']).first().repeat_time
                progress = tboard_data['rds_finished_count'] / (job_count * device_count * repeat_time)
                finished_flag = False
                if str('{:.3f}'.format(progress)) == '1.000':
                    str_progress = str(progress)
                    progress = float(str_progress[:str_progress.index('.') + 4])

            result['id'] = tboard_data['tboard_id']
            result['progress'] = '{:.3f}'.format(progress)
            result['finished_flag'] = finished_flag
            results.append(result)

        return Response({'tboards': results}, status=status.HTTP_200_OK)


class GetTboardSuccessRatioView(generics.GenericAPIView):
    """
    取得tboard成功率
    成功率的计算公式：
    结果为通过的RDS数量/已产生的RDS数量
    """

    def get(self, request):
        tboards = request.query_params.get('tboards', None)
        tboards = re.sub('[^0-9]', ' ', tboards)
        tboard_ids_list = tboards.split()
        tboard_ids = list(set(tboard_ids_list))
        tboard_queryset = TBoard.objects.filter(id__in=tboard_ids)
        tboard_list = []
        for tboard in tboard_queryset:
            tboard_dict = {
                'id': tboard.id,
                'success_ratio': 0 if tboard.success_ratio is None else tboard.success_ratio,
                'finished_flag': tboard.finished_flag,
                'end_time': date_format_transverter(tboard.end_time)
            }
            tboard_list.append(tboard_dict)
        return_data = {
            'tboards': tboard_list
        }
        return Response(return_data, status=status.HTTP_200_OK)


class InsertTBoard(generics.GenericAPIView):
    throttle_classes = (OpenAPIAnonRateThrottle,)
    serializer_class = CreateTBoardSerializer
    CREATE_LEVEL = ['AI_TEST', 'USER']

    def create_tboard(self, request):
        """
        发起任务：
            1. 校验zip包是否正常
            2. 通知coral
            3. 判断下发是否成功
        """
        # tboard_name字段有default值，并且不为空，适应前端传空字串的情况(不传也可以拿default值)
        if request.data.get('board_name', None) == '':
            request.data['board_name'] = 'TBoard{:.0f}'.format(timezone.datetime.timestamp(timezone.now()))

        create_level = request.data.pop('create_level') if 'create_level' in request.data else 'USER'
        if create_level not in self.CREATE_LEVEL:
            return reef_400_response(
                message=f"input invalid create_level parameter, can't is {create_level}",
                description='AI_TEST 不能用此方式下发任务'
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        job_list = serializer.validated_data['job']
        if not job_list:
            return reef_400_response(
                message=f'Error: job list is empty. api job_list parameter: {job_list}',
                description='至少选取1个用例，用例列表不能为空'
            )
        # checkout job zip file
        checkout = Checkout()
        correct_list, error_list = checkout.checkout_zip_file(job_list)
        # correct_list, error_list = checkout_job_zip_file(job_list)
        if error_list:
            error_job_name_list = [
                {
                    'job_name': job.job_name,
                    'job_label': job.job_label,
                    'job_type': job.job_type,
                    'id': job.id
                } for job in error_list
            ]
            correct_list = [job.job_label for job in correct_list]
            return reef_400_response(
                data={'correct_job_label_list': correct_list, 'error_job_name_list': error_job_name_list}
            )
        device_list = serializer.validated_data['device']
        job_prior_data = serializer.validated_data.get('job_prior_data', None)

        device_cabinet_ips = collections.defaultdict(list)
        for device in device_list:
            device_cabinet_ips[device.cabinet.ip_address].append(device)

        tboard = serializer.save()
        tboard.cabinet_dict = {Cabinet.objects.get(ip_address=ip).id: 1 for ip in device_cabinet_ips}
        tboard.save()
        if not job_prior_data:
            res_status_code = insert_tboard_request(tboard, job_list, device_cabinet_ips, create_level)
        else:
            res_status_code = job_prior_insert_tboard(tboard, job_prior_data, device_cabinet_ips, create_level)
        for k, v in copy.deepcopy(res_status_code).items():
            if v == 200:
                res_status_code.pop(k)

        # 下发的任务全失败则直接删除对应的tboard
        if len(res_status_code) == len(device_cabinet_ips):
            for ip in res_status_code:
                tboard.device.remove(*device_cabinet_ips[ip])
            tboard.delete()
            fail_cabinet_name_list = [
                f'{Cabinet.objects.get(ip_address=ip).cabinet_name}: {res_status_code[ip]}' for ip in res_status_code
            ]
            return reef_400_response(
                message={'status': 'fail', 'fail_cabinet': fail_cabinet_name_list},
                description=f'{",".join(fail_cabinet_name_list)}下发任务失败'
            )

        # 下发的任务存在失败则返回失败cabinet,解除cabinet对应device与tboard的关联,更新cabinet_dict的信息,成功下发的机柜修改设备状态。
        elif res_status_code:
            cabinet_dict = tboard.cabinet_dict

            for ip in res_status_code:
                tboard.device.remove(*device_cabinet_ips[ip])
                device_cabinet_ips.pop(ip, None)
                cabinet_dict[Cabinet.objects.get(ip_address=ip).id] = -1

            # 将下发成功的机柜设备状态修改为busy
            update_device_status.insert_tboard_update_device_status(device_cabinet_ips)
            tboard.cabinet_dict = cabinet_dict
            tboard.save()
            return Response({
                'status': 'warning',
                'fail_cabinet': [Cabinet.objects.get(ip_address=ip).cabinet_name for ip in res_status_code]},
                status=status.HTTP_200_OK)

        update_device_status.insert_tboard_update_device_status(device_cabinet_ips)
        return tboard.id

    def post(self, request):
        self.create_tboard(request)
        return Response({'status': 'success'}, status=status.HTTP_200_OK)


class OpenInsertTBoard(InsertTBoard):

    throttle_classes = (OpenAPIAnonRateThrottle,)
    serializer_class = OpenCreateTBoardSerializer

    def post(self, request):
        tboard_id = self.create_tboard(request)
        return ReefResponse({'tboard_id': tboard_id})


class OpenCoolPadInsertTBoard(AutoExecuteSerializerGenericAPIView):

    throttle_classes = (OpenAPIAnonRateThrottle,)
    serializer_class = CoolPadCreateTBoardSerializer

    def post(self, request):
        """
        CoolPad 打包刷机包后触发接口，下发任务
        场景流程: 先执行刷机job --> 执行后续规定的测试用例
        接口流程: 校验job包完整性
        """
        serializer = self.execute(request=request)
        # 拉取ftp 刷机包到reef
        special_job = serializer.validated_data.get("special_job")
        ftp_ip = serializer.validated_data.get('ftp_ip')
        ftp_port = serializer.validated_data.get('ftp_port')
        ftp_user = serializer.validated_data.get('ftp_user')
        ftp_passwd = serializer.validated_data.get('ftp_passwd')
        file_path = serializer.validated_data.get("file_path")
        try:
            reef_ftp = ReefFTP(ftp_ip, ftp_user, ftp_passwd, ftp_port)()
        except Exception as e:
            return reef_400_response(message=f'ftp server login fail, error info: {e}')
        # 将ftp路径保存在media/coolpad 路径下
        media_cool_pad = os.path.join(MEDIA_ROOT, 'coolpad')
        local_path = join_path(media_cool_pad, file_path)
        p = Path(local_path)
        if not p.exists():
            p.mkdir(parents=True)
        try:
            reef_ftp.download_dir_files(file_path, local_path)
        except Exception as e:
            return reef_400_response(description=f"ftp file download fail: {e}, ftp path: {file_path}")
        # 校验job包完整性
        fastboot_job = serializer.validated_data.get('fastboot_job')
        finis_job = serializer.validated_data.get('finis_job')
        checkout_job_list = []
        checkout_job_list.append(fastboot_job)
        checkout_job_list.append(finis_job)
        jobs = serializer.validated_data['jobs']
        for job in jobs:
            checkout_job_list.append(job.get('job_label'))
        checkout = Checkout()
        correct_list, error_list = checkout.checkout_zip_file(checkout_job_list)
        if error_list:
            reef_400_response(description='用例缺少zip文件', message=f"error job list:{error_list}")

        # 记录刷机job参数
        # 这里要先创建刷机job参数数据。在上传数据到coolpad处，按时间排序tboard为条件筛选JobParameter表第一条数据，拿到file_path进行数据上传
        description = serializer.validated_data.get("description")
        fastboot_job_parameter = JobParameter.objects.create(
            **{"describe": description, "parameter": {'file_path': file_path}, "job": fastboot_job}
        )
        # random job, job_result_list:[(job obj, parameter)]
        job_result_list, job_parameter_data = handle_random_job(jobs)

        # 刷机job放在下发队列最前边
        job_result_list[0:0] = [(fastboot_job, fastboot_job.job_parameter.order_by('-create_time').first().parameter)]

        # finis job 放在队列尾端
        job_result_list.append((finis_job, {}))

        # serializer save 方法会创建tboard时使用
        serializer.validated_data['jobs'] = [job for job, _ in job_result_list]

        # create tboard
        phone_model = serializer.validated_data['phone_model']
        # 当前为筛选Tcab_2中的空闲设备。
        device_list = Device.objects.filter(
            status='idle', cabinet__type='Tcab_2', phone_model=phone_model
        )[:3]
        if not device_list:
            reef_400_response(description='没有可用的设备', message=f"phone model info: {phone_model}")
        serializer.validated_data['devices'] = device_list
        device_cabinet_ips = collections.defaultdict(list)
        for device in device_list:
            device_cabinet_ips[device.cabinet.ip_address].append(device)

        tboard = serializer.save()
        tboard.cabinet_dict = {Cabinet.objects.get(ip_address=ip).id: 1 for ip in device_cabinet_ips}
        tboard.save()
        # 修改设备状态为busy， scp需要时间，设备状态修改延迟会导致下发新任务选错设备。下发失败的机柜，设备重新修改状态为idle。
        update_device_status.insert_tboard_update_device_status(device_cabinet_ips)
        # job parameter 记录 tboard， tboard create fail， job 参数记录会删除。
        fastboot_job_parameter.tboard = tboard
        fastboot_job_parameter.save()
        job_parameter_obj_list = [
            JobParameter(job=job_obj, parameter=job_parameter_data[job_obj], tboard=tboard)
            for job_obj in job_parameter_data
        ]
        JobParameter.objects.bulk_create(job_parameter_obj_list)

        # 下发任务并运行
        res_status_code = job_parameter_insert_tboard_request(
            file_path, local_path, tboard, job_result_list, device_cabinet_ips, special_job, 'USER'
        )

        handle_insert_tboard_res(res_status_code, device_cabinet_ips, tboard)

        return ReefResponse()


class RemoveTBoard(generics.GenericAPIView):
    """
    强制停止tboard，将请求转发给coral停止任务，coral服务调用 end_tboard/<int:pk>/ api停止任务
    """
    def post(self, request):
        tboard_id = request.data.get('tboard_id')
        tboard = get_object_or_404(TBoard.objects.all(), id=tboard_id)

        if not tboard.cabinet_dict:
            return Response('tboard has no related coral instance, please check', status=status.HTTP_400_BAD_REQUEST)

        running_cabinet = [cabinet_id for cabinet_id, running_status in tboard.cabinet_dict.items() if
                           running_status == 1]

        res_status_code = {}
        job_parameter = None
        for ip, cabinet_id in [(Cabinet.objects.get(id=cabinet_id).ip_address, cabinet_id) for cabinet_id in running_cabinet]:
            try:
                res = requests.delete(
                    f"http://{ip}:{settings.CORAL_PORT}/tboard/remove_tboard/{tboard_id}/",
                    timeout=30
                )
                res_status_code.update({ip: (res.status_code, cabinet_id)})
                if res.status_code != 500:
                    job_parameter = res.json().get('data', {"message": "job parameter not message"})
                # 模拟返回数据用作测试
                # res_status_code.update({ip: (random.choice([200, 500]), cabinet_id)})
            except OSError:
                res_status_code.update({ip: (500, cabinet_id)})
        # 临时将job tboard 运行参数数据写入到文件中
        import json
        file_path = MEDIA_ROOT + '/job_parameter.log'
        if isinstance(job_parameter, dict):
            with open(file_path, 'w') as f:
                f.write(json.dumps(job_parameter))

        for ip, v in copy.deepcopy(res_status_code).items():
            v, cabinet_id = v
            if v == 200:
                # 更新cabinet_dict 字段, 0表示任务完成
                cabinet_dict = tboard.cabinet_dict
                cabinet_dict[cabinet_id] = 0
                dict_values = list(filter(lambda n: n != -1, list(cabinet_dict.values())))
                # 所有机柜变为0将任务置位结束
                if dict_values:
                    if any(dict_values):
                        tboard.cabinet_dict = cabinet_dict
                        tboard.save()
                    else:
                        tboard.cabinet_dict = cabinet_dict
                        tboard.finished_flag = True
                        tboard.end_time = timezone.now()
                        tboard.save()
                # 修改当前tboard中，所有状态为busy，并且没有执行新任务的设备，状态变为idle。
                update_device_list = []
                busy_device_list = list(tboard.device.filter(cabinet__ip_address=ip, status=DEVICE_STATUS_BUSY))
                for device in busy_device_list:
                    # 判断当前设备关联的最近一个tboard是否是当前要停止的tboard
                    newly_tboard = device.tboard.order_by('-id').first()
                    if newly_tboard == tboard:
                        update_device_list.append(device)
                update_device_status.remove_tboard_update_device_status(update_device_list)
                res_status_code.pop(ip)

        if len(res_status_code) == 0:
            return Response({'status': 'success', 'job_parameter':job_parameter}, status=status.HTTP_200_OK)

        elif len(res_status_code) == len(running_cabinet):
            return Response({
                'status': 'fail',
                'fail_cabinet': [Cabinet.objects.get(ip_address=ip).cabinet_name for ip in res_status_code]},
                status=status.HTTP_200_OK)

        elif res_status_code:
            return Response({
                'status': 'warning',
                'fail_cabinet': [Cabinet.objects.get(ip_address=ip).cabinet_name for ip in res_status_code]},
                status=status.HTTP_200_OK)

        return Response({'status': 'success'}, status=status.HTTP_200_OK)


class DeleteTBoard(generics.GenericAPIView):

    def post(self, request):
        """
        :param request: tboard_id ( list)
        :return: 200OK

        celery异步删除tboard，删除tboard的信息推送到redis，websocket推送消息

        redis存储数据结构：hash
             删除中心列表 ：tboard删除状态有3种： to_be_delete、deleting、deleted
                            存储结构如下：
                                          key：tboard_delete_{tboard_id}
                                          value：{
                                                'id': id,
                                                'board_name': .board_name,
                                                'board_stamp': board_stamp
                                                'success_ratio': '0%',
                                                'author': tboard.author,
                                                'state': 'to_be_delete' （初始状态）
                                                'record_time': timezone.now
                                            }

             删除失败列表 ：删除失败内部提供retry机制，retry失败则会进入删除失败列表
                            存储结构如下：
                                          key：tboard_deleted_fail_{tboard_id}
                                          value：{
                                                'id': id,
                                                'board_name': .board_name,
                                                'board_stamp': board_stamp
                                                'success_ratio': '0%',
                                                'author': tboard.author,
                                                'record_time': timezone.now
                                          }
        websocket：数据通过socket连接，实时推送消息
                   有2个consumer ：TBoardDeleteConsumer（删除中心列表）
                                   BoardDeleteFailConsumer（删除失败列表）

        """

        ids = request.data.get('tboard_id')
        tboards = TBoard.objects.filter(id__in=ids)

        if len(ids) != len(tboards):
            return Response('you had input error tboard id', status=status.HTTP_400_BAD_REQUEST)

        # 如果tboard is_to_delete字段为true，则说明该tboard为删除失败重试，失败重试的数据从reids移除
        retry_ids = tboards.filter(is_to_delete=True).values_list('id', flat=True)
        if retry_ids:
            redis_connect.delete(*[f'{REDIS_TBOARD_DELETE_FAIL}:{retry_id}' for retry_id in retry_ids])

            # 向删除列表发送一次消息，更新删除列表
            tboard_deleted_fail_message = get_hash_data_in_redis(f'{REDIS_TBOARD_DELETE_FAIL}:*')
            message = sorted_data(
                tboard_deleted_fail_message,
                lambda e: (e.__getitem__('record_time'))
            )
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(TBOARD_DELETE_FAIL_GROUP, {
                "type": "send_message",
                "message": message
            })

        # 将tboard is_to_delete状态置为True
        tboards.update(is_to_delete=True)

        # 将要删除的Tboard的数据往redis里面存一份
        for tboard in tboards:
            redis_connect.hmset(f'{REDIS_TBOARD_DELETE}:{tboard.id}', {
                'id': tboard.id,
                'board_name': tboard.board_name,
                'board_stamp': tboard.board_stamp.strftime('%Y-%m-%d %H:%M:%S'),
                'success_ratio': '%.1f%%' % (tboard.success_ratio * 100) if tboard.success_ratio else '0%',
                'author': str(tboard.author),
                'state': 'to_be_delete',
                'record_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            })

        # 将任务添加到队列进行删除
        for id in ids:
            tboard_delete.delay(id)
        return Response(status=status.HTTP_200_OK)


class JobPriorTboardView(generics.GenericAPIView):

    serializer_class = GetJobPriorTboardSerializer
    queryset = TBoard.objects.all()

    def get(self, request):
        # 更新device关联资源信息
        queryset = Device.objects.filter(status='idle')
        update_device_matching_rule(queryset)

        jobs_id = request.query_params.get('jobs_id')
        serializer = GetJobPriorTboardSerializer(data={"jobs_id": jobs_id})
        serializer.is_valid(raise_exception=True)
        job_queryset = Job.objects.filter(id__in=jobs_id.split(','), job_deleted=False)
        result_data = {}
        matching_success = []
        matching_fail = []
        for job in job_queryset:
            # data = {'matching_rule__device__simcard_1__operator__in': ['中国电信']}  test data
            if job.matching_rule:
                job_rule_data = job.matching_rule
                job_rule_data.pop('resource_data')
                filter_dict = spear_dict(job_rule_data, '__')
                filter_dict = {'matching_rule__' + k: v for k, v in filter_dict.items()}
            else:
                filter_dict = {}
            if filter_dict:
                # job 都有cabinet_type 参数时，使用cabinet_type 进行筛选, cabinet_type 后加字段，有的job没有设置该属性。
                device = Device.objects.filter(
                    status='idle', cabinet__type=job.cabinet_type).filter(
                    **filter_dict
                ).first()
            else:
                device = Device.objects.filter(status='idle', cabinet__type=job.cabinet_type).first()
            if device:
                data = {
                    "device": {
                        "device_id": device.id,
                        "device_name": device.device_name,
                        "device_label": device.device_label
                    },
                    "job": {
                        "job_id": job.id,
                        "job_name": job.job_name,
                        "job_label": job.job_label
                    }
                }
                matching_success.append(data)
            else:
                data = {
                        "job_id": job.id,
                        "job_name": job.job_name,
                }
                matching_fail.append(data)
        result_data.update({'matching_fail': matching_fail, 'matching_success': matching_success})
        return Response(result_data, status=status.HTTP_200_OK)


class RepeatExecuteTBoardView(generics.GenericAPIView):

    serializer_class = RepeatExecuteTBoardSerializer
    queryset = TBoard.objects.all()

    def post(self, request):
        """
        在来一次：
            执行条件：
            1. tboard关联的用例是否有被删除
            2. tboard关联的设备是否可用（状态），并且没有变动机柜
        """
        tboard_id = request.data.get('id', None)
        try:
            old_tboard = TBoard.objects.get(id=tboard_id)
        except Exception as e:
            reef_400_response(StatusCode.QUERY_DATABASE_DATA_FAILED.value,
                              StatusCode.QUERY_DATABASE_DATA_FAILED.name,
                              e
                              )
        # checkout device status
        device = old_tboard.device.all().first()
        if device.status != 'idle':
            reef_400_response(StatusCode.DEVICE_NOT_IDLE.value, StatusCode.DEVICE_NOT_IDLE.name)
        # checkout job exist
        job = old_tboard.job.filter(job_deleted=False).first()
        if not job:
            reef_400_response(StatusCode.JOB_NOT_EXIST.value, StatusCode.JOB_NOT_EXIST.name)
        # create new tboard
        tboard_data = GetTBoardFieldsSerializer(old_tboard)
        tboard_data = tboard_data.data
        tboard_data.update({"cabinet_dict": {f"{device.cabinet.id}": 1}, "board_stamp": timezone.now()})
        serializer = CreateRepeatTBoardSerializer(data=tboard_data)
        serializer.is_valid(raise_exception=True)
        tboard = serializer.save()

        post_data = {
            'tboard_id': tboard.id,
            'create_level': "USER",
            'owner_label': str(tboard.author.id),
            'jobs': [
                {'job_label': job.job_label,
                 'updated_time': job.updated_time.strftime('%Y-%m-%d %H:%M:%S'),
                 'url': f'/media/job_res_file_export/{job.job_label}.zip',
                 'flow_execute_mode': job.flow_execute_mode,
                 'inner_job': [
                     {'job_label': inner_flow.job.job_label,
                      'updated_time': inner_flow.job.updated_time.strftime('%Y-%m-%d %H:%M:%S'),
                      'url': f'/media/job_res_file_export/{inner_flow.job.job_label}.zip',
                      } for job_flow in job.job_flow.all() for inner_flow in job_flow.inner_flow.all()
                 ],
                 'job_flows': [
                     {
                         'id': job_flow.id,
                         'order': job_flow.order,
                         'name': job_flow.name
                     } for job_flow in job.job_flow.all()
                 ]
                 }
            ],
            'board_name': tboard.board_name,
            'repeat_time': tboard.repeat_time
        }

        try:
            res = requests.post(
                f"http://{device.cabinet.ip_address}:{settings.CORAL_PORT}/tboard/insert_tboard/",
                json={**post_data, 'device_label_list': [device.device_label]}
            )
            if res.status_code != 200:
                raise Exception(f'coral res code is not 200, but:{res.status_code}')
        except Exception as e:
            tboard.cabinet_dict = {f'{device.cabinet.id}': -1}
            tboard.save()
            tboard.device.clear()
            tboard.delete()
            reef_400_response(StatusCode.REQUEST_CORAL_FAILED.value, StatusCode.REQUEST_CORAL_FAILED.name,
                              e)
        return Response({'status': 'success'}, status=status.HTTP_200_OK)


class TBoardRepeatExecuteCheckView(AutoExecuteSerializerGenericAPIView):

    serializer_class = RepeatExecuteTBoardCheckSerializer
    queryset = TBoard.objects.all()

    def post(self, request):
        """
        1. 获取tboard用例，有用例被删除， 不能执行
        2. 获取tboard使用设备，设备没有一个可用（idle），不能执行
        """
        serializer = self.execute(request)
        tboard = serializer.validated_data.get('tboard')
        deleted_job_queryset = tboard.job.filter(job_deleted=True)
        if deleted_job_queryset:
            return reef_400_response(description='当前用例列表存在缺失，无法运行在来一次')
        idle_device_queryset = tboard.device.filter(status=DEVICE_STATUS_IDLE)
        if not idle_device_queryset.exists():
            return reef_400_response(description='当前设备非idle状态，无法运行在来一次')
        else:
            job_label_list = [job.job_label for job in tboard.job.all()]
            device_label_list = [device.device_label for device in idle_device_queryset]
            device_name_list = [device.device_name if device.device_name is not None else '' for device in idle_device_queryset]
            if tboard.device.all().count() == idle_device_queryset.count():
                return ReefResponse(
                    data={
                        'job_label_list': job_label_list,
                        'device_label_list': device_label_list
                    }
                )
            else:
                return ReefResponse(
                    data={
                        'job_label_list': job_label_list,
                        'device_label_list': device_label_list,
                        'description': f'该任务中的部分设备已被占用，是否使用设备{device_name_list}运行当前任务'
                    }
                )


class ReleaseBusyDeviceView(generics.GenericAPIView):

    serializer_class = ReleaseBusyDeviceSerializer
    queryset = TBoard.objects.filter(finished_flag=False)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tboard = serializer.validated_data.get('tboard_id')
        if tboard:
            tboard.device.filter(status='busy').update(status=DEVICE_STATUS_IDLE)
        return ReefResponse()


######################################################
# helper function                                    #
######################################################

def _to_dict(data: QuerySet, key_names, value_key):
    if isinstance(key_names, str):
        return {dic[key_names]: dic[value_key] for dic in list(data)}
    elif isinstance(key_names, tuple):
        return {tuple([dic[key] for key in key_names]): dic[value_key] for dic in list(data)}

    assert False, 'Params is invalid for function _to_dict'


def _time_in_range(target: datetime, datetime1: datetime, datetime2: datetime) -> bool:
    return min(datetime1, datetime2) <= target <= max(datetime1, datetime2)


def prefix_dict(di_, prefix_s=''):
    """
    把字典的每个key都带上前缀prefix_s
    :param di_:
    :param prefix_s:
    :return:
    """
    return {prefix_s + k: v for k, v in di_.items()}


def spear_dict(di_, con_s='.'):
    """
    展开dict(如果下层还是dict)，需要递归，展开到下层的数据类型不是字典为止
    :param di_: 输入字典
    :param con_s: 层级间的连接符号
    :return: 深度不大于1的字典，嵌套的其他数据类型照旧
    """
    ret_di = {}
    for k, v in di_.items():
        if isinstance(v, dict) and v:
            v = spear_dict(v, con_s)
            ret_di.update(prefix_dict(v, prefix_s=k + con_s))
        else:
            ret_di.update({k: v})
    return ret_di


def handle_random_job(job_info_list):
    # job_info_list : [{"job_label": job obj, "execute_num": 3, "execute_time": 60}] execute_time 单位分钟
    """
    方法流程:
        1. 随机用例执行时间，在循环中为每个job的每次执行随机出执行时间
            * 用例执行总时长 - 执行次数 * 用例前置时间
            * 每轮循环出执行时间后，下次的随机时间在1 到 总时间 - 以随机出的时间范围呢
        2. 待机执行时间
            * 以16小时为基础 减去用例执行时间 得出待机总时长
            * 随机出一个job总轮次列表，根据待机总时长获取一个ratio，处理列表数据使列表数据总和为待机总时长。
    """
    # 用例前置准备时间，总时间要先减去该时间乘执行次数
    job_set_out_time_list = {
        "场景测试_百度": 20 + 25,
        "场景测试_抖音": 57 + 25,
        "场景测试_抖音火山版": 45 + 25,
        "场景测试_抖音极速版": 58 + 25,
        "场景测试_番茄免费小说": 80 + 25,
        "场景测试_和平精英": 200 + 25,
        "场景测试_今日头条": 25 + 25,
        "场景测试_今日头条极速版": 25 + 25,
        "场景测试_快手": 60 + 25,
        "场景测试_快手极速版": 45 + 25,
        "场景测试_浏览器": 22 + 25,
        "场景测试_拼多多": 25 + 25,
        "场景测试_七猫免费小说": 39 + 25,
        "场景测试_腾讯视频": 30 + 25,
        "场景测试_王者荣耀": 70 + 25,
        "场景测试_微信": 25 + 25,
        "场景测试_西瓜视频": 35 + 25,
        "场景测试_拨号": 15 + 15,
        "场景测试_QQ": 30 + 30
    }
    # 随机job数据产出 [(job obj, {time: 随机出的时间})]
    job_result_list = []
    # 用例运行总时长
    all_job_execute_num_count = 0
    # 用例运行总次数
    all_job_execute_time_count = 0
    # job 参数集合，向表中写入数据。
    job_parameter_data = {}
    for job in job_info_list:
        job_execute_count_time = job.get('execute_time')
        all_job_execute_time_count += job_execute_count_time
        execute_num = job.get('execute_num')
        all_job_execute_num_count += execute_num
        job_obj = job.get('job_label')
        # 处理用例的前置准备时间, 判断手机是否亮屏，页面是否有该app等操作。
        job_set_out_time = job_set_out_time_list.get(job_obj.job_name, None)
        if job_set_out_time is None:
            continue
        job_execute_count_time = round((job_execute_count_time * 60 - (job_set_out_time * execute_num)) / 60)
        # 当前每个用例最小执行时间是1分钟，除去前置时间最小时间不能小于轮数 * 1
        if job_execute_count_time <= execute_num:
            reef_400_response(description=f'job: {job_obj.job_name}执行总时间不满足用例每轮次最少执行一分钟条件')
        # job 参数记录, 写入表中
        job_parameter_list = []
        for num in range(execute_num, 0, -1):
            # 最后一轮job使用剩余时间
            if num == 1:
                job_parameter_list.append(job_execute_count_time)
                job_result_list.append((job_obj, {"time": job_execute_count_time}))
            else:
                if job_execute_count_time - num <= 1:
                    random_time = 1
                else:
                    random_time = random.randint(1, job_execute_count_time - num)
                job_parameter_list.append(random_time)
                job_result_list.append((job_obj, {"time": random_time}))
                job_execute_count_time -= random_time
        job_parameter_data[job_obj] = {"job_random_execute_time": job_parameter_list, "job_standby_time": []}
    random.shuffle(job_result_list)

    # 待机时间单位为秒，coral使用sleep实现。任务前台运行传递时间单位为分钟，用例运行一轮是1分钟，使用reef传递过去的time判断执行多到轮
    # 生成待机时间, 整个测试流程为16小时, 待机总时长 = 16 * 60 - 用例执行总时长
    standby_time_count = (16 * 60 - all_job_execute_time_count) * 60
    # 测试使用短的待机时间
    # standby_time_count = 10
    # 生成的最大随机数为 每个用例最小执行1分钟，待机时间要给每个用例留1分钟运行时间。
    sample_max_data = (standby_time_count - all_job_execute_num_count) * 60
    random_data_list = sample_random_list(sample_max_data, standby_time_count, all_job_execute_num_count)
    if len(random_data_list) == len(job_result_list):
        for index, random_data in enumerate(random_data_list):
            job_result_list[index][1].update({"standby_time": random_data})
            job_obj = job_result_list[index][0]
            job_parameter_data[job_obj]['job_standby_time'].append(random_data)
    # job_parameter_data: {job_obj:{job_standby_time: [], job_random_execute_time:[]}}
    return job_result_list, job_parameter_data


def sample_random_list(sample_max, summation, sample_num):

    if sample_num <= 1:
        return [sample_max]
    random_list = random.sample(range(1, sample_max), k=sample_num - 1)
    ratio = summation / sum(random_list)
    ret = [1 if math.floor(data * ratio) <= 0 else math.floor(data * ratio) for data in random_list]
    ret.append(summation - sum(ret))
    return ret


def handle_insert_tboard_res(res_status_code, device_cabinet_ips, tboard):
    # 下发成功的机柜从res_status_code中删除。
    copy_device_cabinet_ips = copy.deepcopy(device_cabinet_ips)
    for k, v in copy.deepcopy(res_status_code).items():
        if v == 200:
            res_status_code.pop(k)
            # 成功设备出列
            copy_device_cabinet_ips.pop(k)

    # 下发的任务全失败则直接删除对应的tboard
    if len(res_status_code) == len(device_cabinet_ips):
        for ip in res_status_code:
            tboard.device.remove(*device_cabinet_ips[ip])
        tboard.delete()
        # 将下发失败的设备状态恢复idle
        update_device_status.insert_tboard_fail_update_device_status(copy_device_cabinet_ips)
        fail_cabinet_name_list = [
            f'{Cabinet.objects.get(ip_address=ip).cabinet_name}: {res_status_code[ip]}' for ip in res_status_code
        ]
        return reef_400_response(
            message={'status': 'fail', 'fail_cabinet': fail_cabinet_name_list},
            description=f'{",".join(fail_cabinet_name_list)} 下发任务失败'
        )

    # 下发的任务存在失败则返回失败cabinet,解除cabinet对应device与tboard的关联,更新cabinet_dict的信息
    elif res_status_code:
        cabinet_dict = tboard.cabinet_dict

        for ip in res_status_code:
            tboard.device.remove(*device_cabinet_ips[ip])
            device_cabinet_ips.pop(ip, None)
            cabinet_dict[Cabinet.objects.get(ip_address=ip).id] = -1

        tboard.cabinet_dict = cabinet_dict
        tboard.save()
        # 将下发失败的设备状态恢复idle
        update_device_status.insert_tboard_fail_update_device_status(copy_device_cabinet_ips)
        fail_cabinet_name_list = [Cabinet.objects.get(ip_address=ip).cabinet_name for ip in res_status_code]
        return reef_400_response(
            message={'status': 'warning', 'fail_cabinet': fail_cabinet_name_list},
            description=f'{",".join(fail_cabinet_name_list)} 下发任务失败'
        )


def insert_tboard_request(tboard, job_list, device_cabinet_ips, create_level):
    post_data = {
        'tboard_id': tboard.id,
        'create_level': create_level,
        'owner_label': str(tboard.author.id),
        'job_random_order': tboard.job_random_order,
        'jobs': [
            {
                'job_label': job.job_label,
                'flow_execute_mode': job.flow_execute_mode,
                'updated_time': job.updated_time.strftime('%Y-%m-%d %H:%M:%S'),
                'url': f'/media/job_res_file_export/{job.job_label}.zip',
                'job_flows': [
                    {
                        'id': job_flow.id,
                        'order': job_flow.order,
                        'name': job_flow.name
                    } for job_flow in job.job_flow.all()
                ],
                'inner_job': [
                    {
                        'job_label': inner_flow.job.job_label,
                        'updated_time': inner_flow.job.updated_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'url': f'/media/job_res_file_export/{inner_flow.job.job_label}.zip',
                    } for job_flow in job.job_flow.all() for inner_flow in job_flow.inner_flow.all()
                ]
            } for job in job_list
        ],
        'board_name': tboard.board_name,
        'repeat_time': tboard.repeat_time
    }

    res_status_code = {}
    for ip in device_cabinet_ips:
        try:
            res = requests.post(
                f"http://{ip}:{settings.CORAL_PORT}/tboard/insert_tboard/",
                json={**post_data, 'device_label_list': [device.device_label for device in device_cabinet_ips[ip]]},
                timeout=2
            )
            res_status_code.update({ip: res.status_code})
        except OSError:
            res_status_code.update({ip: 500})
    return res_status_code


def job_parameter_insert_tboard_request(ftp_path, local_path, tboard, job_data_list, device_cabinet_ips, special_job, create_level):
    # job_data_list: [(job obj, parameter)]
    post_data = {
        'tboard_id': tboard.id,
        'create_level': create_level,
        'owner_label': str(tboard.author.id),
        'job_random_order': tboard.job_random_order,
        'jobs': [
            {
                'job_label': job.job_label,
                'flow_execute_mode': job.flow_execute_mode,
                'updated_time': job.updated_time.strftime('%Y-%m-%d %H:%M:%S'),
                'url': f'/media/job_res_file_export/{job.job_label}.zip',
                'job_flows': [
                    {
                        'id': job_flow.id,
                        'order': job_flow.order,
                        'name': job_flow.name
                    } for job_flow in job.job_flow.all()
                ],
                'inner_job': [
                    {
                        'job_label': inner_flow.job.job_label,
                        'updated_time': inner_flow.job.updated_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'url': f'/media/job_res_file_export/{inner_flow.job.job_label}.zip',
                    } for job_flow in job.job_flow.all() for inner_flow in job_flow.inner_flow.all()
                ],
                'job_parameter': parameter,
                'is_support_parameter': job.is_support_parameter
            } for job, parameter in job_data_list
        ],
        'board_name': tboard.board_name,
        'repeat_time': tboard.repeat_time
    }

    special_job_info = {
        'job_label': special_job.job_label,
        'flow_execute_mode': special_job.flow_execute_mode,
        'updated_time': special_job.updated_time.strftime('%Y-%m-%d %H:%M:%S'),
        'url': f'/media/job_res_file_export/{special_job.job_label}.zip',
        'job_flows': [
            {
                'id': job_flow.id,
                'order': job_flow.order,
                'name': job_flow.name
            } for job_flow in special_job.job_flow.all()
        ],
        'inner_job': [
            {
                'job_label': inner_flow.job.job_label,
                'updated_time': inner_flow.job.updated_time.strftime('%Y-%m-%d %H:%M:%S'),
                'url': f'/media/job_res_file_export/{inner_flow.job.job_label}.zip',
            } for job_flow in special_job.job_flow.all() for inner_flow in job_flow.inner_flow.all()
        ],
    }

    res_status_code = {}
    for ip in device_cabinet_ips:
        # coral 创建对应目录
        url = f"http://{ip}:{settings.CORAL_PORT}/pane/mk_dir/"
        # 容器内创建，根目录是app。scp 到宿主机 根目录是TMach_source
        coral_file_path = join_path('/app/source/rom', ftp_path)
        body = {'dir_path': coral_file_path}
        req = ReefRequest(url, **{"json": body, "timeout": 3})
        rep = req.post({"coral_ip": ip, "body": body})
        status_code = getattr(rep, 'status_code', None)
        # coral 创建对应目录失败不执行scp，不下发任务
        if rep is None or rep.status_code != 200:
            log_content = f"coral create dir error: \n" \
                          f"coarl ip: {ip}\n" \
                          f"rep status_code: {status_code}\n" \
                          f"coral file path: {coral_file_path}"
            logger = ReefLogger('debug')
            logger.error(log_content)
            res_status_code.update({ip: 500})
            continue
        # scp 刷机包到 coral
        try:
            coral_file_path = coral_file_path.replace('app', 'TMach_source', 1)
            ret_val = os.system(f'scp -r {local_path} root@{ip}:{coral_file_path}')
            if ret_val != 0:
                log_content = f"scp file to coral error, ret val is not zero\n" \
                              f"local_path: {local_path}\n" \
                              f"coarl ip: {ip}\n" \
                              f"ret val: {ret_val}\n" \
                              f"coral path: {coral_file_path}"
                logger = ReefLogger('debug')
                logger.error(log_content)
                res_status_code.update({ip: 500})
                continue
        except Exception as e:
            log_content = f"scp file to coral error:\n" \
                          f"local_path: {local_path}\n" \
                          f"coarl ip: {ip}\n" \
                          f"coral path: {coral_file_path}" \
                          f"exception info: {e}"
            logger = ReefLogger('debug')
            logger.error(log_content)
            res_status_code.update({ip: 500})
            continue
        # 下发任务
        url = f"http://{ip}:{settings.CORAL_PORT}/tboard/insert_tboard/"
        body = {**post_data,
                'device_label_list': [device.device_label for device in device_cabinet_ips[ip]],
                'special_job_info': special_job_info
                }
        req = ReefRequest(url, **{"json": body, "timeout": 3})
        rep = req.post({"coral_ip": ip, "body": body})
        if rep is None:
            res_status_code.update({ip: 500})
            continue
        res_status_code.update({ip: rep.status_code})

    return res_status_code


def temp_job_parameter_insert_tboard_request(tboard, tboard_parameter, device_cabinet_ips, create_level):
    tboard_parameter['board_name'] = tboard.board_name
    tboard_parameter['tboard_id'] = tboard.id
    post_data = tboard_parameter

    res_status_code = {}
    for ip in device_cabinet_ips:
        url = f"http://{ip}:{settings.CORAL_PORT}/tboard/insert_tboard/"
        body = {**post_data, 'device_label_list': [device.device_label for device in device_cabinet_ips[ip]]}
        req = ReefRequest(url, **{"json": body, "timeout": 3})
        rep = req.post({"coral_ip": ip, "body": body})
        if rep is None:
            res_status_code.update({ip: 500})
            continue
        res_status_code.update({ip: rep.status_code})

    return res_status_code


def job_prior_insert_tboard(tboard, job_prjob_data, device_cabinet_ips, create_level):
    post_data = {
        'tboard_id': tboard.id,
        'create_level': create_level,
        'owner_label': str(tboard.author.id),
        'board_name': tboard.board_name,
        'device_mapping': [],
        'job_random_order': tboard.job_random_order,
    }
    res_status_code = {}
    for ip in device_cabinet_ips:
        post_data['device_mapping'] = [
            {
                'device_label': device.device_label,
                'job': get_job_info(job_prjob_data.get(device.device_label, []))
            }
            for device in device_cabinet_ips[ip]
        ]
        try:
            res = requests.post(
                f"http://{ip}:{settings.CORAL_PORT}/tboard/insert_tboard/",
                json={**post_data}
            )
            res_status_code.update({ip: res.status_code})
        except OSError:
            res_status_code.update({ip: 500})
    return res_status_code


def get_job_info(job_obj_list):
    jobs = []
    for job in job_obj_list:
        jobs.append({
            'job_label': job.job_label,
            'flow_execute_mode': job.flow_execute_mode,
            'updated_time': job.updated_time.strftime('%Y-%m-%d %H:%M:%S'),
            'url': f'/media/job_res_file_export/{job.job_label}.zip',
            'job_flows': [
                {
                    'id': job_flow.id,
                    'order': job_flow.order,
                } for job_flow in job.job_flow.all()
            ],
            'inner_job': [
                {
                    'job_label': inner_flow.job.job_label,
                    'updated_time': inner_flow.job.updated_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'url': f'/media/job_res_file_export/{inner_flow.job.job_label}.zip',
                } for job_flow in job.job_flow.all() for inner_flow in job_flow.inner_flow.all()
            ]
        })
    return jobs


def checkout_job_zip_file(job_list):

    corrct_list = []
    error_list = []
    for job in job_list:
        # checkout job
        if job in error_list:
            continue
        if not os.path.exists(os.path.join(JOB_RES_FILE_EXPORT_PATH, f'{job.job_label}.zip')):
            error_list.append(job)
            # job zip file no exists, continue
            continue
        inner_error = False
        # checkout inner_job
        job_flows = job.job_flow.all()
        for job_flow in job_flows:
            # get everyone job_flow of inner_flow
            inner_flow_queryset = job_flow.inner_flow.all()
            for inner_flow in inner_flow_queryset:
                # get everyone inner_flow relate job
                inner_job = inner_flow.job
                if inner_job in error_list:
                    inner_error = True
                    continue
                if not os.path.exists(os.path.join(JOB_RES_FILE_EXPORT_PATH, f'{inner_job.job_label}.zip')):
                    error_list.append(inner_job)
                    inner_error = True
        # job zip, inner_job zip is exists
        if not inner_error:
            corrct_list.append(job)
    return corrct_list, error_list

