import logging

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils import timezone

from apiv1.core.constants import JOB_TYPE_JOB_LIB, JOB_TYPE_PERF_JOB, JOB_SECOND_TYPE_TIME_JOB, JOB_TYPE_PRIOR_JOB
from apiv1.core.model import AbsBase
from apiv1.module.job.models import Job
from apiv1.module.user.models import ReefUser

logger = logging.getLogger(__name__)


def get_tboard_default_name():
    return 'TBoard{:.0f}'.format(timezone.datetime.timestamp(timezone.now()))


class TBoard(models.Model):
    author = models.ForeignKey(ReefUser, on_delete=models.PROTECT, related_name='tboard', verbose_name='用户')
    repeat_time = models.PositiveSmallIntegerField(default=1, verbose_name='任务重复次数')
    board_name = models.CharField(max_length=32, default=get_tboard_default_name, verbose_name='任务名称')
    # 该任务是否已经结束
    finished_flag = models.BooleanField(default=False, verbose_name='任务是否结束')
    board_stamp = models.DateTimeField(verbose_name='创建任务时间')
    device = models.ManyToManyField("Device", related_name='tboard', verbose_name='装置')
    job = models.ManyToManyField(Job, related_name='tboard', verbose_name='用例', through='TBoardJob')
    # tboard执行结束时间, 由于tboard在创建的时候不可能知道它的具体结束时间，给予nullable属性
    end_time = models.DateTimeField(null=True)
    success_ratio = models.FloatField(null=True, default=None)
    is_to_delete = models.BooleanField(default=False, verbose_name='是否要被删除')
    # 记录每个cabinet运行状态 key: cabinet_id  value: 0  1  -1
    # (0表示该cabinet的任务运行完成，1表示任务正在运行, -1表示任务下发失败)
    cabinet_dict = JSONField(null=True)
    tboard_type = models.CharField(
        max_length=20,
        choices=(
            (JOB_TYPE_JOB_LIB, JOB_TYPE_JOB_LIB),
            (JOB_TYPE_PERF_JOB, JOB_TYPE_PERF_JOB),
            (JOB_TYPE_PRIOR_JOB, JOB_TYPE_PRIOR_JOB)
        ),
        default=JOB_TYPE_JOB_LIB,
        verbose_name='tboard分类'
    )
    tboard_second_type = models.CharField(
        max_length=15,
        choices=(
            (JOB_SECOND_TYPE_TIME_JOB, JOB_SECOND_TYPE_TIME_JOB),
        ),
        null=True, blank=True,
        verbose_name='tboard二级分类'
    )
    job_random_order = models.BooleanField(default=False, verbose_name="tboard中用例顺序是否随机")
    test_gather_name = models.CharField(max_length=350, default="", verbose_name='测试集名称合集')
    belong = models.CharField(max_length=150, blank=True, null=True, verbose_name='第三方创建者')

    class Meta:
        verbose_name_plural = "任务"

    @property
    def progress(self):
        rdss = self.rds.all()
        finished_rds_count = 0
        for rds in rdss:
            if rds.end_time is not None:
                finished_rds_count += 1
        total = (len(self.device.all()) * len(self.job.all()) * self.repeat_time)
        progress = finished_rds_count / total if total != 0 else 0
        if progress > 1:
            logger.warning('tboard has invalid progress value\n'
                           f'tboard_id: {self.id}'
                           f'progress: {progress}')
        return round(progress, 2)


class TBoardJob(models.Model):
    """
    TBoard和Job的关联关系，也记录了Job在TBoard中的顺序
    TBoardJob并不是Django自动生成的关联关系Model，创建的时候需要手动维护其顺序信息
    """
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="tboardjob", verbose_name="用例关联")
    tboard = models.ForeignKey(TBoard, on_delete=models.CASCADE, related_name="tboardjob", verbose_name="任务关联")
    order = models.SmallIntegerField(verbose_name="用例在任务中的顺序")


class TBoardStatisticsResult(AbsBase):

    tboard = models.ForeignKey(TBoard, on_delete=models.CASCADE, related_name="tboardstatisticsresult", verbose_name="任务关联")
    file_path = models.CharField(max_length=350, verbose_name='文件路径')
