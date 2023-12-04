import math, uuid
import re
from datetime import date
from typing import List

from django.apps import apps
from django.db import connection
from django.db.models import Count
from django.shortcuts import reverse
from rest_framework import generics
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from apiv1.core.cache import cache_dcr
from apiv1.core.constants import REDIS_CACHE_GET_DATA_VIEW
from apiv1.core.response import ReefResponse, reef_400_response
from apiv1.core.view.generic import AutoExecuteSerializerGenericAPIView
from apiv1.module.device.models import Device
from apiv1.module.job.models import Job, TestGather
from apiv1.module.job.serializer import DataViewJobFilterSerializer, CheckTBoardSerializer
from apiv1.module.rds.models import Rds
from apiv1.module.tboard.models import TBoard

COUNT_PER_PAGE = 20


class GetDataViewSerializer(serializers.Serializer):
    tboard_id = serializers.PrimaryKeyRelatedField(
        queryset=TBoard.objects.all(),
        required=False,
        source='tboard',
        default=None
    )
    group_by = serializers.ChoiceField(
        required=True,
        choices=["device", "job"],
    )
    start_date = serializers.DateField(required=False, default=None)
    end_date = serializers.DateField(required=False, default=None)
    device_id = serializers.PrimaryKeyRelatedField(
        queryset=Device.objects.all(),
        required=False,
        default=None,
        source='device'
    )
    job_id = serializers.PrimaryKeyRelatedField(
        queryset=Job.objects.filter(),
        required=False,
        default=None,
        source='job'
    )
    devices = serializers.CharField(
        required=False,
        default=None,
    )
    jobs = serializers.CharField(
        required=False,
        default=None
    )
    page = serializers.IntegerField(min_value=0, required=False, default=0)
    ordering = serializers.ChoiceField(
        required=False,
        choices=['success_ratio', 'fail_ratio', 'na_ratio', '-success_ratio', '-fail_ratio', '-na_ratio'],
        default='-na_ratio'
    )
    na_ratio = serializers.CharField(
        required=False,
        default=None,
        help_text="筛选任务的无效率，正数代表大于，负数代表小于。例如na_ratio=-0.5，代表筛选无效率<=0.5的结果"
    )
    success_ratio = serializers.CharField(
        required=False,
        default=None,
        help_text="筛选任务的成功率，正数代表大于，负数代表小于。例如success_ratio=-0.5，代表筛选成功率<=0.5的结果"
    )
    fail_ratio = serializers.CharField(
        required=False,
        default=None,
        help_text="筛选任务的失败率，正数代表大于，负数代表小于。例如fail_ratio=-0.5，代表筛选失败率率<=0.5的结果"
    )

    @staticmethod
    def validate_devices(val: str):
        if val is None:
            return None

        pattern = "^([0-9]+,)*[0-9]+$"
        if re.match(pattern, val):
            return [int(device_id) for device_id in val.split(",")]
        raise ValidationError("devices invalid!")

    @staticmethod
    def validate_jobs(val: str):
        if val is None:
            return None
        pattern = "^([0-9]+,)*[0-9]+$"
        if re.match(pattern, val):
            return [int(job_id) for job_id in val.split(",")]
        raise ValidationError("jobs invalid!")

    @staticmethod
    def validate_success_ratio(val: str):
        if val is None:
            return None
        pattern = r"^-?[0-9]+\.?[0-9]*$"
        if re.match(pattern, val):
            return float(val)
        raise ValidationError("invalid value")

    @staticmethod
    def validate_fail_ratio(val: str):
        return GetDataViewSerializer.validate_success_ratio(val)

    @staticmethod
    def validate_na_ratio(val: str):
        return GetDataViewSerializer.validate_success_ratio(val)


class GetDataViewView(generics.GenericAPIView):
    serializer_class = GetDataViewSerializer

    # @cache_dcr(key_leading=REDIS_CACHE_GET_DATA_VIEW, ttl_in_second=86400 * 14)
    def get(self, request: Request) -> Response:
        param = request.query_params.dict()
        serializer = GetDataViewSerializer(data=param)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        ret = get_data_view_result(data["tboard"], data["group_by"], data["start_date"], data["end_date"],
                                   data["device"], data["job"], data["page"], data["devices"], data["jobs"],
                                   data["ordering"], data["success_ratio"], data["fail_ratio"], data["na_ratio"])

        return Response(ret)


class DataViewLabelFilterView(AutoExecuteSerializerGenericAPIView):

    serializer_class = CheckTBoardSerializer
    queryset = Job.objects.all()

    def get(self, request):
        serializer = self.execute(request, action='get')
        tboard = serializer.validated_data.get('tboard')
        test_gather = serializer.validated_data.get('test_gather')
        if tboard:
            queryset = tboard.job.all()
        elif test_gather:
            queryset = test_gather.job.all()
        else:
            return reef_400_response(message='lack parameter')
        label_dict = {
            'JobTestArea': ["id", "description"],
            'AndroidVersion': ["id", "version"],
            'PhoneModel': ['id', 'phone_model_name'],
            'RomVersion': ['id', 'version'],
            'CustomTag': ['id', 'custom_tag_name'],
        }
        result = {}
        for model in label_dict.keys():
            model_class = apps.get_model('apiv1', model)
            model_data = model_class.objects.filter(**{'job__in': queryset}).distinct('id').values(*label_dict[model])
            result[model] = list(model_data)
        if tboard:
            result['Author'] = [{'id': job.author_id, 'username': job.author.username} for job in Job.objects.filter(tboard=tboard).distinct('author')]
            result['CabinetType'] = [{'type': job.cabinet_type, "id": index} for index, job in enumerate(Job.objects.filter(tboard=tboard).distinct('cabinet_type'))]
        else:
            result['Author'] = [{'id': job.author_id, 'username': job.author.username} for job in
                                Job.objects.filter(testgather=test_gather).distinct('author')]
            result['CabinetType'] = [{'type': job.cabinet_type, "id": index} for index, job in
                                     enumerate(Job.objects.filter(testgather=test_gather).distinct('cabinet_type'))]
        return ReefResponse(data=result)


class DataViewFilterView(AutoExecuteSerializerGenericAPIView):

    serializer_class = DataViewJobFilterSerializer
    queryset = Job.objects.all()

    """
    job 数据统计
    1. 按条件筛选
    2. 搜索
    3. 排序
    4. 分页
    """

    def post(self, request):
        serializer = self.execute(request)
        tboard = serializer.validated_data.get('tboard')
        order = serializer.validated_data.get('order')
        reverse = serializer.validated_data.get('reverse')
        offset = serializer.validated_data.get('offset')
        limit = serializer.validated_data.get('limit')
        filter_condition = serializer.validated_data.get('filter_condition')
        contains = serializer.validated_data.pop('contains', None)
        job = serializer.validated_data.pop('job', None)
        device = serializer.validated_data.pop('device', None)
        validated_data = serializer.validated_data
        # 获取第一级数据
        if filter_condition == 'job' and job is None:
            queryset = Job.objects.filter(tboard=tboard)
            delete_dict_data(['tboard', 'order', 'reverse', 'offset', 'limit', 'filter_condition'], validated_data)
        elif filter_condition == 'device' and device is None:
            queryset = Device.objects.filter(tboard=tboard)
            delete_dict_data(['tboard', 'order', 'reverse', 'offset', 'limit', 'filter_condition'], validated_data)
        # 获取第二级数据， ex：一级数据为job info，二级数据获取device info，需要查询device表。
        elif filter_condition == 'job' and job:
            queryset = Device.objects.filter(tboard=tboard)
            delete_dict_data(['tboard', 'order', 'reverse', 'offset', 'limit', 'filter_condition'], validated_data)
        elif filter_condition == 'device' and device:
            queryset = Job.objects.filter(tboard=tboard)
            delete_dict_data(['tboard', 'order', 'reverse', 'offset', 'limit', 'filter_condition'], validated_data)
        else:
            return reef_400_response(message=f'filter_condition is must fields')
        # 去重，创建tboard job选择运行多轮次，这里会出现多个相同job obj，所以去重。
        queryset = queryset.distinct('id')
        # 条件筛选
        queryset = queryset.filter(**validated_data)
        data_count = queryset.count()
        # 模糊查询
        if contains:
            if filter_condition == 'job':
                queryset = queryset.filter(job_name__contains=contains)
            elif filter_condition == 'device':
                queryset = queryset.filter(device_name__contains=contains)
            data_count = queryset.count()
        # 统计rds
        result = filter_rds_data(tboard, queryset, device, job)
        # 排序
        if order:
            result: List = sorted(result, key=lambda x: x[order], reverse=reverse)
        # 分页
        if limit and offset >= 0:
            result = data_page(result, limit, offset)

        return ReefResponse(data=result, headers={"Total-Count": data_count})


def data_page(data: list, limit, offset):
    if len(data) <= limit:
        return data
    else:
        if offset == 0:
            return data[:limit]
        else:
            return data[offset*limit: offset*limit + limit]


def delete_dict_data(list_data: list, dict_data):
    for data in list_data:
        dict_data.pop(data, None)
    return dict_data


def filter_rds_data(tboard, queryset, device=None, job=None):
    result = []
    for obj in queryset:
        if isinstance(obj, Job):
            name = 'job_name'
            label_name = 'job_label'
            rds_queryset = Rds.objects.filter(
                job=obj, tboard=tboard
            )
        elif isinstance(obj, Device):
            name = 'device_name'
            label_name = 'device_label'
            rds_queryset = Rds.objects.filter(
                device=obj, tboard=tboard
            )
        res_data = {
            'id': obj.id,
            'name': f'{ f"{getattr(obj, label_name)}" if getattr(obj, name) is None else getattr(obj, name)}' ,
            'success_num': 0,
            'success_rate': 0,
            'fail_num': 0,
            'fail_rate': 0,
            'invalid_rate': 0,
            'invalid_num': 0,
            'count_num': 0,
            'uuid': uuid.uuid1()    # 前端需要一个唯一字段
        }
        if device:
            rds_queryset = rds_queryset.filter(device=device)
            res_data['label_id'] = device.id    # 前端需要此字段用来判断二级数据属于哪个一级数据
            res_data['label_name'] = device.device_label if device.device_name is None else device.device_name
        if job:
            rds_queryset = rds_queryset.filter(job=job)
            res_data['label_id'] = job.id   # # 前端需要此字段用来判断二级数据属于哪个一级数据
            res_data['label_name'] = job.job_label if job.job_name is None else job.job_name
        count_num = rds_queryset.count()
        if not count_num:
            result.append(res_data)
            continue
        res_data['count_num'] = count_num
        datas = rds_queryset.filter(job_assessment_value__in=['0', '1']).values('job_assessment_value').annotate(
            Count('id'))
        for data in datas:
            if data.get('job_assessment_value') == '0':
                success_num = data.get('id__count', 0)
                success_rate = round(success_num/count_num*100, 2)
                res_data['success_num'] = success_num
                res_data['success_rate'] = success_rate
            if data.get('job_assessment_value') == '1':
                fail_num = data.get('id__count', 0)
                fail_rate = round(fail_num/count_num*100, 2)
                res_data['fail_num'] = fail_num
                res_data['fail_rate'] = fail_rate
        invalid_num = rds_queryset.exclude(job_assessment_value__in=['0', '1']).count()
        invalid_rate = round(invalid_num/count_num*100, 2)
        res_data['invalid_num'] = invalid_num
        res_data['invalid_rate'] = invalid_rate
        result.append(res_data)
    return result


def get_data_view_result(tboard: TBoard = None, group_by: str = 'device', start_date: date = None,
                         end_date: date = None, device: Device = None, job: Job = None, page: int = 0,
                         devices: List[int] = None, jobs: List[int] = None, ordering: str = 'na_ratio',
                         success_ratio: float = None, fail_ratio: float = None, na_ratio: float = None):
    tboard_id: int = tboard.id if tboard else None
    device_id: int = device.id if device else None
    job_id: int = job.id if job else None
    tboard_cond = f"and tboard_id = {tboard_id} " if tboard_id else ""
    start_date_cond = f"and start_time >= '{start_date.strftime('%Y-%m-%d %H:%M:%S')}' " if start_date else ""
    end_date_cond = f"and start_time <= '{end_date.strftime('%Y-%m-%d 23:59:59')}' " if end_date else ""
    device_id_cond = f"and device_id = {device_id} " if device_id else ""
    job_id_cond = f"and job_id = {job_id} " if job_id else ""
    devices_cond = f"and device_id in ({','.join([str(device) for device in devices])}) " if devices is not None else ""
    jobs_cond = f"and job_id in ({','.join([str(job) for job in jobs])})" if jobs is not None else ""

    success_ratio_cond = f"and round(1.0 * r.success / (r.na + r.fail + r.success), 2) " \
                         f"{'>' if success_ratio >= 0 else '<'}= {success_ratio if success_ratio > 0 else -success_ratio} " \
        if success_ratio is not None else ""

    fail_ratio_cond = f"and round(1.0 * r.fail / (r.na + r.fail + r.success), 2) " \
                      f"{'>' if fail_ratio >= 0 else '<'}= {fail_ratio if fail_ratio > 0 else -fail_ratio} " \
        if fail_ratio is not None else ""

    na_ratio_cond = f"and round(1.0 * r.na / (r.na + r.fail + r.success), 2) " \
                    f"{'>' if na_ratio >= 0 else '<'}= {na_ratio if na_ratio > 0 else -na_ratio} " \
        if na_ratio is not None else ""

    sql = f"""
            select
                r.id,
                info.{group_by}_name,
                info.{group_by}_label,
                r.na,
                r.success,
                r.fail,
                r.na + r.fail + r.success as total,
                CASE
                when 1.0 * r.na / (r.na + r.fail + r.success) < 0.001 and 1.0 * r.na / (r.na + r.fail + r.success) != 0 then 0.001
                else round(1.0 * r.na / (r.na + r.fail + r.success), 3) END as na_ratio,
                CASE
                when 1.0 * r.fail / (r.na + r.fail + r.success) < 0.001 and 1.0 * r.fail / (r.na + r.fail + r.success) != 0 then 0.001
                else round(1.0 * r.fail / (r.na + r.fail + r.success), 3) END as fail_ratio,
                CASE
                when 1.0 * r.success / (r.na + r.fail + r.success) < 0.001 and 1.0 * r.success / (r.na + r.fail + r.success) != 0 then 0.001
                else round(1.0 * r.success / (r.na + r.fail + r.success), 3) END as success_ratio
            from
                (select
                coalesce(na.{group_by}_id, suc.{group_by}_id, fail.{group_by}_id) as id,
                coalesce(na.na, 0) as na,
                coalesce(suc.success, 0) as success,
                coalesce(fail.fail, 0) as fail
                from
                    (select {group_by}_id, count(*) as na
                    from apiv1_rds
                    where job_assessment_value!~'^[0-1]$' 
                    {tboard_cond} 
                    {start_date_cond}
                    {end_date_cond}
                    {device_id_cond}
                    {job_id_cond}
                    {devices_cond}
                    {jobs_cond}
                    group by {group_by}_id) as na
                full join
                    (select {group_by}_id, count(*) as success
                    from apiv1_rds
                    where job_assessment_value='0'
                    {tboard_cond}
                    {start_date_cond}
                    {end_date_cond}
                    {device_id_cond}
                    {job_id_cond}
                    {devices_cond}
                    {jobs_cond}
                    group by {group_by}_id) as suc
                on na.{group_by}_id=suc.{group_by}_id
                full join
                    (select {group_by}_id, count(*) as fail
                    from apiv1_rds
                    where job_assessment_value='1'
                    {tboard_cond}
                    {start_date_cond}
                    {end_date_cond}
                    {device_id_cond}
                    {job_id_cond}
                    {devices_cond}
                    {jobs_cond}
                    group by {group_by}_id) as fail
                on coalesce(na.{group_by}_id, suc.{group_by}_id)=fail.{group_by}_id
                ) as r
            left join apiv1_{group_by} as info
            on r.id=info.id
            where true
            {success_ratio_cond}
            {fail_ratio_cond}
            {na_ratio_cond}
            order by 
            {ordering[1:] if ordering.startswith('-') else ordering} {'DESC' if ordering.startswith('-') else 'ASC'},
            r.id ASC
            limit {COUNT_PER_PAGE}
            offset {COUNT_PER_PAGE} * {page}
            """
    with connection.cursor() as c:
        c.execute(sql)
        ret = c.fetchall()

    rds_queryset = Rds.objects.all()
    rds_queryset = rds_queryset if tboard_id is None else Rds.objects.filter(tboard_id=tboard_id)
    rds_queryset = rds_queryset if start_date is None else rds_queryset.filter(start_time__gte=start_date)
    rds_queryset = rds_queryset if end_date is None else rds_queryset.filter(start_time__lte=end_date)
    rds_queryset = rds_queryset if device_id is None else rds_queryset.filter(device_id=device_id)
    rds_queryset = rds_queryset if job_id is None else rds_queryset.filter(job_id=job_id)
    rds_queryset = rds_queryset if devices is None else rds_queryset.filter(device__in=devices)
    rds_queryset = rds_queryset if jobs is None else rds_queryset.filter(job__in=jobs)

    count = math.ceil(rds_queryset.distinct(f"{group_by}").count() / COUNT_PER_PAGE)
    param = {
        "group_by": group_by,
        "page": page,
        "ordering": ordering
    }
    if tboard_id:
        param["tboard_id"] = tboard_id
    if start_date:
        param["start_date"] = start_date
    if end_date:
        param["end_date"] = end_date
    if device:
        param["device_id"] = device.id
    if job:
        param["job_id"] = job.id
    if devices is not None:
        param["devices"] = ",".join([str(device) for device in devices])
    if jobs is not None:
        param["jobs"] = ",".join([str(job) for job in jobs])

    param["page"] = page + 1
    next_ = f"{reverse('get_data_view')}?{'&'.join([f'{k}={v}' for k, v in param.items() if v is not None])}" \
        if page + 1 < count else None
    param["page"] = page - 1
    prev_ = f"{reverse('get_data_view')}?{'&'.join([f'{k}={v}' for k, v in param.items() if v is not None])}" \
        if page - 1 >= 0 else None

    ret = {
        "fields": [f"{group_by}_id",
                   f"{group_by}_name",
                   f"{group_by}_label",
                   "na",
                   "success",
                   "fail",
                   "total",
                   "na_ratio",
                   "fail_ratio",
                   "success_ratio"],
        "count": count,
        "page_size": COUNT_PER_PAGE,
        "prev": prev_,
        "next": next_,
        "data": ret
    }

    return ret
