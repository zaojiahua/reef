import re

from rest_framework import generics
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from apiv1.core.cache import cache_dcr
from apiv1.core.constants import REDIS_CACHE_GET_DATA_VIEW_SUMMERY
from apiv1.module.rds.models import Rds


class GetDataViewSummerySerializer(serializers.Serializer):
    devices = serializers.CharField(
        required=False,
        default=None
    )
    start_date = serializers.DateField(
        required=False,
        default=None
    )
    end_date = serializers.DateField(
        required=False,
        default=None
    )

    @staticmethod
    def validate_devices(val: str):
        if val is None:
            return None

        pattern = "^([0-9]+,)*[0-9]+$"
        if re.match(pattern, val):
            return [int(device_id) for device_id in val.split(",")]
        raise ValidationError("devices invalid!")


class GetDataViewSummeryView(generics.GenericAPIView):
    serializer_class = GetDataViewSummerySerializer

    # @cache_dcr(key_leading=REDIS_CACHE_GET_DATA_VIEW_SUMMERY)
    def get(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        rds_queryset = Rds.objects.all()
        if data["devices"] is not None:
            rds_queryset = rds_queryset.filter(device__in=data['devices'])
        if data["start_date"] is not None:
            rds_queryset = rds_queryset.filter(start_time__gte=data["start_date"])
        if data["end_date"] is not None:
            rds_queryset = rds_queryset.filter(start_time__lte=data["end_date"].strftime('%Y-%m-%d 23:59:59'))

        ret = rds_queryset.values_list("job_assessment_value", flat=True)
        success = fail = na = 0

        for val in ret:
            try:
                val = int(val)
            except (ValueError, TypeError):
                na += 1
                continue

            if val == 0:  # pass
                success += 1
            elif val == 1:
                fail += 1
            else:
                na += 1

        return Response({
            "success": success,
            "fail": fail,
            "na": na,
            "total": success + fail + na,
            "success_ratio": 0 if success == fail == na == 0 else round(1.0 * success / (success + fail + na), 2),
            "fail_ratio": 0 if success == fail == na == 0 else round(1.0 * fail / (success + fail + na), 2),
            "na_ratio": 0 if success == fail == na == 0 else round(1.0 * na / (success + fail + na), 2)
        })
