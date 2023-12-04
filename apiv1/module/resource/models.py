from django.db import models

from apiv1.module.device.models import Device, SubsidiaryDevice
from apiv1.core.constants import DEVICE_STATUS_BUSY, DEVICE_STATUS_IDLE
from apiv1.core.model import AbsBase


class SIMCard(AbsBase):

    operator = models.CharField(max_length=30, verbose_name='运营商')
    is_volte = models.BooleanField(default=True, verbose_name='是否有volte服务')
    status = models.CharField(
        max_length=30,
        choices=(
            (DEVICE_STATUS_BUSY, DEVICE_STATUS_BUSY),
            (DEVICE_STATUS_IDLE, DEVICE_STATUS_IDLE)
        ),
        default=DEVICE_STATUS_IDLE,
        verbose_name='SIM卡状态'
    )
    phone_number = models.CharField(max_length=30, unique=True, verbose_name='手机号码')
    order = models.SmallIntegerField(blank=True, null=True, verbose_name='SIM卡编号')
    history_relevance = models.CharField(max_length=30, blank=True, verbose_name='历史关联设备')
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='simcard',
        null=True,
        blank=True,
        verbose_name='绑定设备'
    )
    subsidiary_device = models.ForeignKey(
        SubsidiaryDevice,
        on_delete=models.CASCADE,
        related_name='simcard',
        null=True,
        blank=True,
        verbose_name='绑定僚机'
    )

    class Meta:
        verbose_name_plural = 'SIM 卡'


class APPGather(AbsBase):

    name = models.CharField(max_length=50, unique=True, verbose_name='app名称')
    max_login_num = models.SmallIntegerField(verbose_name='最大同时登陆数', default=1)


class Account(AbsBase):

    name = models.CharField(max_length=30, verbose_name='账号id')     # 登录使用的账号
    username = models.CharField(max_length=30, verbose_name='账号名称')  # 账号名称
    password = models.CharField(max_length=30, verbose_name='密码')
    status = models.CharField(
        max_length=15,
        choices=(
            (DEVICE_STATUS_BUSY, DEVICE_STATUS_BUSY),
            (DEVICE_STATUS_IDLE, DEVICE_STATUS_IDLE)
        ),
        default=DEVICE_STATUS_IDLE,
        verbose_name='账号状态'
    )
    phone_number = models.CharField(max_length=30, null=True, blank=True, verbose_name='绑定手机号码')
    head_portrait_name = models.CharField(max_length=30, blank=True, verbose_name='头像名称')
    crony = models.CharField(max_length=100, blank=True, verbose_name='好友')
    # 不是冗余字段，导入资源时用此字段校验新系统中是否有该app。
    app_name = models.CharField(max_length=30, blank=True, verbose_name='账号归属app名称')
    app = models.ForeignKey(
        APPGather,
        on_delete=models.CASCADE,
        related_name='account'
    )
    device = models.ManyToManyField(
        Device,
        related_name='account',
        verbose_name='关联设备',
        blank=True,
    )
    subsidiary_device = models.ManyToManyField(
        SubsidiaryDevice,
        related_name='account',
        verbose_name='关联僚机设备',
        blank=True
    )

    class Meta:
        unique_together = (
            ('name', 'app')
        )
        verbose_name_plural = "账号"

    def save(self, **kwargs):
        super(Account, self).save()
        # 将获取app名称，更新到app_name字段
        if getattr(self, 'app_name', None):
            return
        if getattr(self, 'app', None):
            self.app_name = self.app.name
            self.save()

    @property
    def max_login_num(self):
        if self.app:
            return self.app.max_login_num
        else:
            return None

    @property
    def usage_rate(self):
        max_num = self.app.max_login_num
        subsidiary_device_num = self.subsidiary_device.all().count()
        device_num = self.device.all().count()
        return f'{subsidiary_device_num + device_num}/{max_num}'


class TGuard(AbsBase):

    name = models.CharField(max_length=100, unique=True, verbose_name='词组名称')
    is_system = models.BooleanField(default=False, verbose_name='是否为系统固定词组')


