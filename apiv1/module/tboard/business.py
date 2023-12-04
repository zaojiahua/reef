from rest_framework.exceptions import APIException

from apiv1.module.job.models import Job
from apiv1.module.tboard.models import TBoardJob, TBoard


def insert_get_battery_job(tboard: TBoard) -> None:
    """
    在创建TBoard时，若其中包含Job的类别为 'Uniq'（Uniq类的Job,
    其tboard.repeat_time = 1，tboard.job的数量=1）
    则自动在其前后插入测试电量的用例(job-getBattery)，用以量测该任务的电量变化
    """
    if (tboard.job.count() != 1) or (tboard.job.first().job_type != "Uniq"):
        return

    try:
        job_get_battery = Job.objects.get(job_label="job-getBattery")
    except Job.DoesNotExist:
        raise APIException("找不到电量自动检测的用例'job-getBattery',它被意外删除了吗?", 404)

    TBoardJob.objects.filter(tboard=tboard, job=tboard.job.first()).update(order=1)
    TBoardJob.objects.bulk_create([
        TBoardJob(tboard=tboard, job=job_get_battery, order=0),
        TBoardJob(tboard=tboard, job=job_get_battery, order=2),
    ])
