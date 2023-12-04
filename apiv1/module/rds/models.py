import logging
import os

from PIL import Image
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models.fields.files import ImageFieldFile
from django.utils import timezone
from django.contrib.postgres.indexes import BrinIndex

from apiv1.core.model import AbsBase
from apiv1.module.device.signal import ModelManager
from reef import settings
from apiv1.module.device.models import Device, PhoneModel, RomVersion
from apiv1.module.job.models import Job
from apiv1.module.tboard.models import TBoard
from apiv1.core.constants import POWER_CONSUMPTION_ERROR_CODE, TEMP_CONSUMPTION_ERROR_CODE, RDS_FILTER_SERIOUS


class Rds(AbsBase):
    # 任务开始时间
    start_time = models.DateTimeField(default=timezone.now, blank=False, verbose_name='用例开始时间')
    # 任务结束时间
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='用例结束时间')
    """
    0: 通过
    1: 失败
    负数为无效
    """
    job_assessment_value = models.CharField(max_length=50, blank=True, default='', verbose_name='测试评分')
    device = models.ForeignKey(Device, related_name='rds', on_delete=models.CASCADE, verbose_name='装置', db_index=True)
    job = models.ForeignKey(Job, related_name='rds', on_delete=models.CASCADE, verbose_name='用例', db_index=True)
    tboard = models.ForeignKey(
        TBoard,
        related_name='rds',
        on_delete=models.CASCADE,
        verbose_name='任务'
    )
    rds_dict = JSONField(null=True)
    created_by_ai_tester = models.CharField(max_length=50, blank=True, null=True, verbose_name='是否AItest用户创建')
    created_by_sys_job = models.CharField(max_length=50, blank=True, null=True, verbose_name='是否系统任务')
    phone_model = models.ForeignKey(PhoneModel, related_name='rds', blank=True, null=True, db_index=True,
                                    on_delete=models.CASCADE, verbose_name='设备型号')
    rom_version = models.ForeignKey(RomVersion,  related_name='rds',blank=True, null=True, db_index=True,
                                   on_delete=models.CASCADE, verbose_name='设备系统版本号')
    job_duration = models.FloatField(blank=True, null=True, verbose_name='job执行耗时')
    original_job_duration = models.FloatField(blank=True, null=True, verbose_name='job去除广告的执行耗时')

    power_consumption = models.SmallIntegerField(
        null=True, verbose_name="耗电量",
        help_text="记录该用例运行过程中的电量变化，目前只支持Uniq类的用例，不支持的用例产生的Rds该字段值为null，"
        f"合法的值范围为-100~100。若资料异常无法计算出该值，则以{POWER_CONSUMPTION_ERROR_CODE}记录"
    )
    temp_consumption = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, verbose_name='温度差',
        help_text="记录该用例运行过程中的温度变化，目前只支持Uniq类的用例，不支持的用例产生的Rds该字段值为null，"
                  f"合法的值范围为-199.99~199.99。若资料异常无法计算出该值，则以{TEMP_CONSUMPTION_ERROR_CODE}记录"
    )
    typical_job_temp_consumption = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='特定job的温度差',
        help_text="此温度差由Coral计算，这里只负责更新记录。不支持的用例产生的Rds该字段值为null。"
                  "不同job开始记录温度时间不同"
    )
    start_point = models.IntegerField(null=True, blank=True, verbose_name='性能测试开始点')
    end_point = models.IntegerField(null=True, blank=True, verbose_name='性能测试结束点')
    ads_start_point = models.IntegerField(null=True, blank=True, verbose_name='性能测试广告开始点')
    ads_end_point = models.IntegerField(null=True, blank=True, verbose_name='性能测试广告结束点')
    # url_prefix = models.CharField(null=True, blank=True, max_length=300, verbose_name='图片url前缀')
    picture_count = models.IntegerField(default=0, verbose_name='图片数量')
    time_per_unit = models.FloatField(null=True, blank=True, verbose_name='性能测试单位耗时')
    lose_frame_point = models.CharField(max_length=50, null=True, blank=True, verbose_name='丢帧点')
    filter = models.CharField(
        max_length=50,
        choices=(
            (RDS_FILTER_SERIOUS, RDS_FILTER_SERIOUS),
        ),
        blank=True,
        null=True,
        verbose_name='rds筛选标注'
    )
    rom_version_const = models.CharField(max_length=50, null=True, blank=True, verbose_name='rds创建时设备系统版本号')
    app_info = JSONField(null=True, verbose_name='app信息记录')
    start_method = models.IntegerField(null=True, blank=True, verbose_name='起点检测方式')
    end_method = models.IntegerField(null=True, blank=True, verbose_name='终点检测方式')
    set_fps = models.IntegerField(null=True, blank=True, verbose_name='用户设置帧率')
    set_shot_time = models.FloatField(null=True, blank=True, verbose_name='用户设置时间')
    fps = models.IntegerField(null=True, blank=True, verbose_name='实际帧率')
    frame_data = JSONField(null=True, blank=True, verbose_name='每帧数据')

    objects = ModelManager()

    class Meta:
        verbose_name_plural = "测试结果"
        indexes = [
            BrinIndex(
                autosummarize=True,
                pages_per_range=1,
                fields=['start_time', 'end_time'],
            ),
        ]
        unique_together = [['device', 'job', 'start_time']]


class RdsLog(models.Model):
    rds = models.ForeignKey(Rds, on_delete=models.CASCADE, related_name='rdslog', verbose_name='测试结果')
    log_file = models.FileField(upload_to="rds_logs/%Y_%m_%d", verbose_name='测试结果日志文件')
    # 储存该档案相关讯息，供Coral端使用
    file_name = models.CharField(max_length=100, verbose_name='测试结果日志文件名称')

    def log_content(self):
        if os.path.exists(self.log_file.path):
            with open(self.log_file.path, 'r', encoding='UTF-8') as f:
                return f.read()
        return ''

    class Meta:
        verbose_name_plural = "测试结果日志文件"


def make_thumb(path, new_height=150):
    image = Image.open(path)
    width, height = image.size
    new_width = int(new_height * width * 1.0 / height)
    image.thumbnail((new_height, new_width))
    return image


class RdsScreenShot(models.Model):
    rds = models.ForeignKey(Rds, on_delete=models.CASCADE, related_name='rdsscreenshot', verbose_name='测试结果')
    img_file = models.ImageField(upload_to="screen_shot/%Y_%m_%d", verbose_name='测试结果截图')
    thumbs_file = models.ImageField(upload_to="screen_shot/%Y_%m_%d", blank=True, null=True, verbose_name='测试结果截压缩图')
    # 储存该档案相关讯息，供Coral端使用
    file_name = models.CharField(max_length=100, verbose_name='测试结果截图名称')
    is_resource_file = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "测试结果截图"

    def save(self, **kwargs):
        super(RdsScreenShot, self).save()
        # 大图存在执行
        if os.path.exists(self.img_file.path):
            try:
                thumb_image = make_thumb(self.img_file.path)
                # 保存文件到指定路径 e.g: screen_shot/2021_12_01/f549425fe9871de508718b4c385a2306.jpeg
                dir_name = self.img_file.name.split('/')[1]
                img_name = self.img_file.name.split('/')[2]
                thumb_path = os.path.join(settings.MEDIA_ROOT, 'screen_shot', f'{dir_name}', f'thumb_{img_name}')
                thumb_image.save(thumb_path)
                self.thumbs_file = ImageFieldFile(self, self.thumbs_file, f'screen_shot/{dir_name}/thumb_{img_name}')
                self.save_base()
            except Exception as e:
                logger = logging.getLogger('backend')
                logger.error(f'Image make thumb error:\n rds id: {self.id}\n msg:{e}')
