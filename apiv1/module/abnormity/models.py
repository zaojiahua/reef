from django.db import models
from django.contrib.postgres.fields import JSONField

from apiv1.core.model import AbsDescribe, AbsBase
from apiv1.module.device.models import Device
from apiv1.module.tboard.models import TBoard


class AbnormityType(models.Model):
    title = models.CharField(max_length=30, verbose_name='异常类型标题')
    sub_title = models.CharField(max_length=30, blank=True, null=True, verbose_name='异常类型子标题')
    describe = models.CharField(max_length=100, blank=True, null=True, verbose_name='异常类型描述')
    is_active = models.BooleanField(default=True, verbose_name='是否可用')
    """
    由于coral不知道关于异常类型的信息
    reef用此字段自己识别异常类型
    当前只有电量异常，暂定规则如下：
        1 = 电量异常
        2 = ANR
        3 = Crash
        4 = Exception
    """
    code = models.IntegerField(unique=True, verbose_name='异常类型编码')

    class Meta:
        verbose_name_plural = "异常类型"


class AbnormityPolicy(models.Model):
    name = models.CharField(max_length=30, verbose_name='规则名称', unique=True)
    """
    {
        type: ..... (通用字段，指示类型)
        value: .....
    }
    power: 
        type = power_leave
        value = (battery_level)
    """
    policy_rule = JSONField(verbose_name='规则')
    abnormity_type = models.ForeignKey(AbnormityType,
                                       on_delete=models.SET_NULL,
                                       null=True,
                                       related_name='abnormity_policy',
                                       verbose_name='异常类型')
    """
    reef用此字段自己识别异常规则:
        1 = 电量跳电规则
    """
    code = models.IntegerField(unique=True, verbose_name='异常政策编码')

    class Meta:
        verbose_name_plural = "定义异常规则"


class Abnormity(AbsBase):
    start_time = models.DateTimeField(verbose_name='异常开始时间')
    end_time = models.DateTimeField(blank=True, null=True, verbose_name='异常结束时间')
    device = models.ForeignKey(Device,
                               db_index=True,
                               on_delete=models.CASCADE,
                               related_name='abnormity',
                               verbose_name='设备')
    abnormity_type = models.ForeignKey(AbnormityType,
                                       db_index=True,
                                       on_delete=models.CASCADE,
                                       related_name='abnormity',
                                       verbose_name='异常类型')
    tboard = models.ForeignKey(TBoard,
                               on_delete=models.SET_NULL,
                               related_name='abnormity',
                               blank=True,
                               null=True,
                               verbose_name='出现异常所在的Tboard')
    abnormity_policy = models.ForeignKey(AbnormityPolicy,
                                         db_index=True,
                                         on_delete=models.CASCADE,
                                         blank=True,
                                         null=True,
                                         related_name='abnormity',
                                         verbose_name='异常规则')
    is_end = models.BooleanField(default=False, db_index=True)
    # 该字段用于日期分组
    date = models.DateField(auto_now_add=True, verbose_name='异常创建日期')

    class Meta:
        verbose_name_plural = "异常概要"


class AbnormityDetail(AbsDescribe):
    time = models.DateTimeField(verbose_name='异常发生时间')
    """
    Data format
    {
        data: str|list|dict
    }
    
    1. power: 
            {power: battery_level}
    """
    result_data = JSONField(verbose_name='异常结果记录')
    abnormity = models.ForeignKey(Abnormity,
                                  db_index=True,
                                  on_delete=models.CASCADE,
                                  related_name='abnm_detail',
                                  verbose_name='异常概要')

    class Meta:
        verbose_name_plural = "异常详情"


class AbnormityLog(AbsDescribe):

    abnormity_detail = models.ForeignKey(
        AbnormityDetail,
        on_delete=models.CASCADE,
        related_name='abnormitylog',
        verbose_name='异常详情'
    )
    file = models.FileField(upload_to="abnormity_logs/%Y_%m_%d", verbose_name='测试结果日志文件')
    name = models.CharField(max_length=100, verbose_name='测试结果日志文件名称')
    type = models.CharField(max_length=50, verbose_name='用例资源文件类型')




