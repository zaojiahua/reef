from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils import timezone

from apiv1.core.constants import WOODENBOX_TYPE_POWER, WOODENBOX_TYPE_TEMP


class System(models.Model):
    """
    TMach系统，每个TMach系统中应该都会有一个唯一的system，这个唯一的system实例会在reef第一次初始化的时候创建，这个System会有一个随机产生的名称，
    格式为System%y%m%d%H%M%S%f，跟随在System后方的符号为常见的时间格式。
    为后续扩展做保留，目前来说，大多数时候你都不需要关心System的内容
    """
    system_name = models.CharField(max_length=50, verbose_name='系统名称')
    ip_address = models.GenericIPAddressField(verbose_name='系统IP地址')    # ip地址硬编码在migration文件中

    class Meta:
        verbose_name_plural = "系统"


class Cabinet(models.Model):
    """
    物理机柜，一个Cabinet对应的是一台真实的物理机柜，其中包含装载了Coral的物理主机
    """
    cabinet_name = models.CharField(max_length=50, unique=True, verbose_name='机柜名称')
    ip_address = models.GenericIPAddressField(verbose_name='机柜IP', unique=True)
    belong_to = models.ForeignKey(System, on_delete=models.PROTECT, related_name='cabinet', verbose_name='系统')
    is_delete = models.BooleanField(default=False, verbose_name='机柜是否移除')
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True, null=True)
    update_time = models.DateTimeField(verbose_name="更新时间", auto_now=True)
    type = models.CharField(max_length=50, verbose_name="机柜类型", null=True)
    m_location_x = models.FloatField(blank=True, null=True, verbose_name="m_location x 坐标")
    m_location_y = models.FloatField(blank=True, null=True, verbose_name="m_location y 坐标")
    m_location_z = models.FloatField(blank=True, null=True, verbose_name="m_location z 坐标")

    class Meta:
        verbose_name_plural = "机柜"


class WoodenBox(models.Model):
    """
    一个包含继电器，开关等硬件的木盒，可独立拆除，搬移
    """
    name = models.CharField(max_length=50, verbose_name='硬件模块名称')
    type = models.CharField(max_length=150,
                            choices=(
                                (WOODENBOX_TYPE_POWER, WOODENBOX_TYPE_POWER),
                                (WOODENBOX_TYPE_TEMP, WOODENBOX_TYPE_TEMP)
                            ),
                            verbose_name='硬件模块类型')
    ip = models.GenericIPAddressField(protocol='both', unpack_ipv4=True, verbose_name='木盒ip')
    config = JSONField(verbose_name='木盒配置文件')
    cabinet = models.ForeignKey(Cabinet,
                                on_delete=models.CASCADE,
                                null=True,
                                blank=True,
                                related_name='woodenbox',
                                verbose_name='机柜')
    create_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        unique_together = (
            ("name", "type"),
            ("ip", "cabinet")
        )


# class TMachType(models.Model):
#
#     # 优先使用ID作为唯一标示，直接获取顶级分类一下类型时使用type_name作为type的唯一标示。
#     type_name = models.CharField(max_length=20, verbose_name='类型名称', unique=True)
#     describe = models.CharField(max_length=100, verbose_name='描述')
#     tier = models.SmallIntegerField(verbose_name='类型属于的层级')
#     # 保留字段暂时没有使用
#     order = models.SmallIntegerField(default=0, verbose_name='类型排序')
#     parent_type = models.ForeignKey('self', related_name='tmach_type',
#                                     null=True, blank=True, on_delete=models.CASCADE, verbose_name='父级类型')
