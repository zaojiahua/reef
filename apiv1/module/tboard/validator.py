from typing import List

from rest_framework.exceptions import ValidationError

from apiv1.module.device.models import DevicePower, Device
from apiv1.module.job.models import Job


def validate_device_battery_level(devices: List[Device], jobs: List[Job]) -> None:
    upper_limit = float("inf")
    lower_limit = float("-inf")
    for job_cond in jobs:
        if job_cond.power_upper_limit is not None:
            upper_limit = min(upper_limit, job_cond.power_upper_limit)
        if job_cond.power_lower_limit is not None:
            lower_limit = max(lower_limit, job_cond.power_lower_limit)

    for device in devices:
        device_id = device.id
        battery_level = _get_device_battery_level(device_id)
        if (upper_limit != float("inf")) and (battery_level > upper_limit):
            raise ValidationError(
                detail={"error": f"Device ID={device_id}, 电量={battery_level}, 电量不符合Job电量上限({upper_limit})限制"})
        if (lower_limit != float("-inf")) and (battery_level < lower_limit):
            raise ValidationError(
                detail={"error": f"Device ID={device_id}, 电量={battery_level}, 电量不符合Job电量下限({lower_limit})限制"})


def validate_uniq_job(repeat_time: int, jobs: List[Job]) -> None:
    """
    If a tboard include a job which job_type is 'Uniq',
    There are some limitations of the tboard:
    1. TBoard.repeat_time = 1 (not greater and not less than 1)
    2. TBoard.job.count() = 1 (only one job)
    """
    for job in jobs:
        if job.job_type == 'Uniq':
            break
    else:
        return

    if repeat_time != 1:
        raise ValidationError(detail={"error": f"包含Uniq类Job的TBoard, 只能执行1个轮次"})
    if len(jobs) != 1:
        raise ValidationError(detail={"error": f"包含Uniq类Job的TBoard, 只能包含一个用例"})


#############################################
# helper function                           #
#############################################
def _get_device_battery_level(device_id: int) -> int:
    """
    Helper function for get device's battery level info.
    """
    dp = DevicePower.objects \
        .values("record_datetime", "battery_level") \
        .filter(device_id=device_id) \
        .order_by("-record_datetime") \
        .first()
    if dp is None:
        return -1
    return dp["battery_level"]
