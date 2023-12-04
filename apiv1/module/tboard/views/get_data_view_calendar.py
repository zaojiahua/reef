import re
from datetime import date
from typing import List, Tuple

from django.db import connection
from rest_framework import serializers, generics
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from apiv1.core.cache import cache_dcr
from apiv1.core.constants import REDIS_CACHE_GET_DATA_VIEW_CALENDAR


class GetDataViewCalendarSerializer(serializers.Serializer):
    devices = serializers.CharField(
        required=False,
        default=None
    )
    jobs = serializers.CharField(
        required=False,
        default=None
    )
    start_date = serializers.DateField(
        required=True
    )
    end_date = serializers.DateField(
        required=True
    )
    target = serializers.ChoiceField(
        choices=[
            'success',
            'fail',
            'na'
        ]
    )

    @staticmethod
    def validate_devices(val: str):
        if val is None:
            return None

        pattern = "^([0-9]+,)*[0-9]+$"
        if re.match(pattern, val):
            return [device_id for device_id in val.split(",")]
        raise ValidationError("devices invalid!")

    @staticmethod
    def validate_jobs(val: str):
        if val is None:
            return None
        pattern = "^([0-9]+,)*[0-9]+$"
        if re.match(pattern, val):
            return [job_id for job_id in val.split(",")]
        raise ValidationError("jobs invalid!")


class GetDataViewCalendarView(generics.GenericAPIView):
    serializer_class = GetDataViewCalendarSerializer

    # @cache_dcr(key_leading=REDIS_CACHE_GET_DATA_VIEW_CALENDAR, ttl_in_second=300)
    def get(self, request: Request) -> Response:
        param = request.query_params
        serializer = self.get_serializer(data=param)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        target = data["target"]
        cond_jav = "false"  # condition of job assessment value

        if target == "success":
            cond_jav = "job_assessment_value='0'"
        elif target == "fail":
            cond_jav = "job_assessment_value='1'"
        elif target == "na":
            cond_jav = "job_assessment_value!~'^[0-1]$'"

        start_date: date = data['start_date']
        end_date: date = data["end_date"]
        jobs: List[str] = data["jobs"]
        devices: List[str] = data["devices"]

        cond_jobs = "" if jobs is None else f"and job_id in ({','.join(jobs)}) "
        cond_devices = "" if devices is None else f"and device_id in ({','.join(devices)}) "

        sql = f"""
        select cast(start_time + interval '8 H' as date) as days, count(*)
        from apiv1_rds
        where 
        {cond_jav}
        {cond_jobs}
        {cond_devices}
        and
        start_time >= '{start_date.strftime("%Y-%m-%d")}'
        and
        start_time <= '{end_date.strftime("%Y-%m-%d 23:59:59.999999")}'
        group by days
        """
        with connection.cursor() as c:
            c.execute(sql)
            ret = c.fetchall()

        return Response({
            "intervals": _get_intervals(ret),
            "data": ret
        })


def _get_intervals(vals: List[Tuple[date, int]]):
    if len(vals) == 0:
        return [(0, 0), (0, 0), (0, 0), (0, 0)]
    _, max_ = max(vals, key=lambda x: x[1])
    _, min_ = min(vals, key=lambda x: x[1])

    return [
        (
            round(min_),
            round((0.75 * min_) + (0.25 * max_))
        ),
        (
            round((0.75 * min_) + (0.25 * max_)),
            round((0.5 * min_) + (0.5 * max_))
        ),
        (
            round((0.5 * min_) + (0.5 * max_)),
            round((0.25 * min_) + (0.75 * max_))
        ),
        (
            round((0.25 * min_) + (0.75 * max_)),
            round(max_)
        )
    ]
