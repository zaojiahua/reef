from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex

from apiv1.core.constants import PANEVIEW_TYPE_MATRIX, PANEVIEW_TYPE_MAP, PANESLOT_STATUS_OK, PANESLOT_STATUS_EMPTY, \
    PANESLOT_STATUS_ERROR, DEVICE_OCCUPY_TYPE_JOB_EDITOR, PANEVIEW_TYPE_TEST_BOX, DEVICE_TYPE_TEST_BOX, DEVICE_TYPE_ADB
from apiv1.core.model import AbsDescribe
from apiv1.module.device.signal import ModelManager, PowerPortManager, PowerPortAllManager, TempPortAllManager
from apiv1.module.system.models import WoodenBox


class AndroidVersion(models.Model):
    # 添加设备时，若指定的设备安卓版本在数据库中不存在，将会根据传入的信息自动创建AndroidVersion
    version = models.CharField(max_length=50, unique=True, verbose_name="版本号")  # ex: 8.1.0

    class Meta:
        verbose_name_plural = "安卓版本"


class Manufacturer(models.Model):
    # 系统中存在一笔预设的 manufacturer: "ReefDefaultManufacturer"，在系统第一次被启动的时候会自动创建
    manufacturer_name = models.CharField(max_length=50, unique=True, db_index=True, verbose_name='制造商名称')

    class Meta:
        verbose_name_plural = "制造商"


class PhoneModel(models.Model):
    # 添加设备时，若指定的设备型号不存在，将根据传入的信息自动创建PhoneModel
    # 自动创建的PhoneModel将会使用预设的Manufacturer: REEF_DEFAULT_MANUFACTURER
    phone_model_name = models.CharField(max_length=50, unique=True, db_index=True, verbose_name='装置型号名称')
    manufacturer = models.ForeignKey("Manufacturer", on_delete=models.CASCADE, related_name='phonemodel',
                                     verbose_name='制造商')
    cpu_name = models.CharField(max_length=50, null=True, blank=True, verbose_name='装置型号CPU名称')
    # x_border, y_border,   x_dpi,  y_dpi
    x_border = models.FloatField(null=True, default=None, verbose_name='x轴屏幕与边框间距')
    y_border = models.FloatField(null=True, default=None, verbose_name='y轴屏幕与边框间距')
    x_dpi = models.FloatField(null=True, default=None, verbose_name='x轴像素与距离换算单位')
    y_dpi = models.FloatField(null=True, default=None, verbose_name='y轴像素与距离换算单位')
    ply = models.FloatField(null=True, default=None, verbose_name='设备型号厚度')
    height = models.FloatField(null=True, default=None, verbose_name='设备型号高度')
    width = models.FloatField(null=True, default=None, verbose_name='设备型号宽度')
    height_resolution = models.PositiveSmallIntegerField(null=True, verbose_name='高度分辨率')
    width_resolution = models.PositiveSmallIntegerField(null=True, verbose_name='宽度分辨率')

    class Meta:
        verbose_name_plural = "装置型号"


class PhoneModelCustomCoordinate(models.Model):

    name = models.CharField(max_length=50, verbose_name='属性名称')
    x_coordinate = models.FloatField(null=True, blank=True, verbose_name='x坐标')
    y_coordinate = models.FloatField(null=True, blank=True, verbose_name='y坐标')
    z_coordinate = models.IntegerField(default=0, null=True, blank=True, verbose_name='z坐标')
    is_fixed = models.BooleanField(default=True)
    phone_model = models.ForeignKey(
        PhoneModel,
        on_delete=models.CASCADE,
        related_name='phonemodelcustomcoordinate',
        verbose_name='设备型号'
    )

    class Meta:
        verbose_name_plural = "机型自定义坐标"
        unique_together = [['phone_model', 'name']]


class RomVersion(models.Model):
    # 添加设备时，若指定的Rom版本信息不存在于数据库中，将根据传入的信息自动创建RomVersion
    # 自动创建的RomVersion将会使用预设的Manufacturer: REEF_DEFAULT_MANUFACTURER
    manufacturer = models.ForeignKey("Manufacturer", on_delete=models.CASCADE, related_name='romversion',
                                     verbose_name='制造商')
    version = models.CharField(max_length=50, unique=True, verbose_name='装置系统版本号')

    class Meta:
        verbose_name_plural = "装置系统版本号"


class DeviceCoordinate(models.Model):
    # 设备在机柜内的位置信息
    upper_left_x = models.PositiveSmallIntegerField(verbose_name='左上角X轴坐标')
    upper_left_y = models.PositiveSmallIntegerField(verbose_name='左上角Y轴坐标')
    upper_right_x = models.PositiveSmallIntegerField(verbose_name='右上角X轴坐标')
    upper_right_y = models.PositiveSmallIntegerField(verbose_name='右上角Y轴坐标')
    bottom_left_x = models.PositiveSmallIntegerField(verbose_name='左下角X轴坐标')
    bottom_left_y = models.PositiveSmallIntegerField(verbose_name='左下角Y轴坐标')
    bottom_right_x = models.PositiveSmallIntegerField(verbose_name='右下角X轴坐标')
    bottom_right_y = models.PositiveSmallIntegerField(verbose_name='右下角Y轴坐标')

    class Meta:
        verbose_name_plural = "装置角点坐标"


# 用户  AI系统  Cabinet   editor     Old            New
# a 1       1       0       0    =   error       error
# b 1       0       0       0    =   error       error
# c 0       1       0       0    =   error       error
# d 0       0       0       0    =   offline     offline
# e 1       1       1       0    =   busy        busy
# f 1       0       1       0    =   busy        busy
# g 0       1       1       0    =   idle   =>     ai
# h 0       0       1       0    =   idle        idle
# i 1       1       0       1    =               error
# j 1       0       0       1    =               error
# k 0       1       0       1    =               error
# l 0       0       0       1    =               error
# m 1       1       1       1    =               error
# n 1       0       1       1    =               error
# o 0       1       1       1    =               error
# p 0       0       1       1    =               editing
#
#
# h -> d


# Coral在使用Device编辑Job时，会将该Device的Cabinet属性移除，使其成为offline状态

class Device(models.Model):
    """裝置"""

    """
    -----设备的唯一识别性-----
    对于一台准备注册进系统的设备来说，我们希望知道这台设备是否曾经注册过，如果我们不能辨识这台设备，会导
    致数据库以多笔不同的设备信息记录一台物理设备
    eg：
    Device1注册进系统中并取得了一个唯一ID: 1，后来用户将设备移除，并重新将该设备注册进系统，则对于系统来
    说，会将该设备视为一个全新的设备并分配一个新的唯一ID: 2，对于同一台设备数据库就会存在2笔记录（ID 1 和 2）
    
    因此，在设备注册时，我们使用cpu_name, phone_model_name, cpu_id来拼成device_label属性，并以此属性
    作为设备的识别ID
    """
    device_label = models.CharField(max_length=50, unique=True, db_index=True, verbose_name='装置标签')
    device_name = models.CharField(max_length=50, default='Device', null=True, verbose_name='装置名称')
    cabinet = models.ForeignKey(
        "Cabinet",
        on_delete=models.CASCADE,
        null=True,
        related_name='cabinet',
        verbose_name='机柜'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='装置IP地址')
    android_version = models.ForeignKey(
        "AndroidVersion",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='device',
        verbose_name='装置安卓版本'
    )
    # 即product_name
    phone_model = models.ForeignKey(
        "PhoneModel",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='device',
        verbose_name='装置型号'
    )
    cpu_id = models.CharField(max_length=50, verbose_name='装置IP地址')
    rom_version = models.ForeignKey(
        "RomVersion",
        on_delete=models.CASCADE,
        related_name='device',
        verbose_name='装置系统版本号'
    )

    # 装置进入系统的时间
    start_time_key = models.CharField(max_length=50, null=True, blank=True, verbose_name='装置进入系统时间')
    coordinate = models.OneToOneField(
        "DeviceCoordinate",
        on_delete=models.SET_NULL,
        related_name='device',
        null=True,
        blank=True,
        verbose_name='装置四个角点坐标'
    )

    monitor_index = models.ManyToManyField("MonitorPort", related_name='device', verbose_name='相机编号')

    # status 设备当前状态，目前有5种状态（busy、idle、error、offline, occupied)
    """
    发起任务 idle --> busy fun:insert_tboard_update_device_status
    任务完成 busy --> idle coral 维护变更
    设备异常 idle/busy --> error coral 维护变更
    注册设备 offline --> idle  api: create_update_device
    注销设备 idle --> offline  api: release_device
    页面释放设备 occupied --> idle api: release_occupy_device
    页面抢占设备 idle/occupied --> occupied api：control_device
    """
    status = models.CharField(max_length=50, blank=True, null=True, verbose_name='装置当前状态')
    status_update_time = models.DateTimeField(blank=True, null=True, verbose_name="设备状态更新时间")

    # 该字段的计算依赖其它字段，由signal触发保存时自动填入
    ai_occupy = models.CharField(max_length=50, blank=True, null=True, verbose_name='装置是否被AI_test用户占用')
    auto_test = models.BooleanField(default=False, verbose_name='系统是否自动分派任务给该设备')
    occupy_type = models.CharField(max_length=150,
                                   choices=(
                                       (DEVICE_OCCUPY_TYPE_JOB_EDITOR, DEVICE_OCCUPY_TYPE_JOB_EDITOR),
                                   ),
                                   default='', blank=True,
                                   verbose_name='设备被占用的类型')
    device_type = models.CharField(max_length=50,
                                   choices=(
                                       (DEVICE_TYPE_TEST_BOX, DEVICE_TYPE_TEST_BOX),
                                       (DEVICE_TYPE_ADB, DEVICE_TYPE_ADB),
                                   ),
                                   default=DEVICE_TYPE_ADB,
                                   verbose_name='设备执行类型'
                                   )
    subsidiary_device_count = models.SmallIntegerField(default=0, verbose_name='设备附属设备数量')
    matching_rule = JSONField(null=True, verbose_name='device匹配job规则')
    custom_number = models.CharField(max_length=100, default='', blank=True, verbose_name='自定义编号')

    def __str__(self):
        if self.device_name is not None and self.cabinet is not None:
            return self.device_name + " in " + self.cabinet.cabinet_name
        else:
            return self.device_label

    def save(self, **kwargs):
        # 修改status 字段时，更新status_update_time 字段。
        if hasattr(self, 'status') and self.status is not None:
            setattr(self, 'status_update_time', timezone.now())
        super().save(**kwargs)

    @property
    def subsidiary_device_info(self):
        subsidiary_device_obj_list = SubsidiaryDevice.objects.filter(device=self).order_by('order')
        results = []
        for subsidiary_device in subsidiary_device_obj_list:
            sim_card_list = subsidiary_device.simcard.order_by('order').values('operator', 'phone_number', 'order')
            sim_card_list = list(sim_card_list)
            account_info = subsidiary_device.account.all().values('app_name', 'name')
            account_info = list(account_info)
            data = {
                'subsidiary_device_name': subsidiary_device.serial_number,
                'subsidiary_device_id': subsidiary_device.id,
                'subsidiary_device_order': subsidiary_device.order,
                'subsidiary_device_custom_name': subsidiary_device.custom_name,
                'SIMCard_info': sim_card_list, 'account_info': account_info
            }
            results.append(data)
        return results

    class Meta:
        verbose_name_plural = "装置"
        indexes = [
            GinIndex(
                fields=['matching_rule']
            )
        ]


class DevicePower(models.Model):
    device = models.ForeignKey("Device", on_delete=models.CASCADE, related_name='devicepower', verbose_name='装置')
    cabinet = models.ForeignKey("Cabinet", on_delete=models.CASCADE, related_name='devicepower', verbose_name='机柜')
    power_port = models.ForeignKey("PowerPort",
                                   on_delete=models.PROTECT,
                                   related_name='devicepower',
                                   null=True,
                                   verbose_name='电量端口号'
                                   )
    """
    不同于created_time, record_datetime是由客户端发送来的记录产生时间，
    created_time则是数据库中的资料产生时间
    """
    record_datetime = models.DateTimeField(default=timezone.now, verbose_name='客户端发送的记录时间')
    battery_level = models.PositiveSmallIntegerField(verbose_name='电量值')
    charging = models.BooleanField(verbose_name='是否在充电')
    battery_file = models.FileField(upload_to='device', max_length=100, blank=True, null=True, verbose_name='电量文件')

    class Meta:
        verbose_name_plural = "装置电量"

    def save(self, **kwargs):
        # devicepower表中power_port字段可以为null，如果表中device字段有关联到powerport
        # 则在保存的时候会将device的powerport填入power_port字段中
        super(DevicePower, self).save()
        if self.power_port is not None:
            return
        if not hasattr(self.device, 'powerport'):
            return
        self.power_port = self.device.powerport
        self.save()


class DeviceScreenshot(models.Model):
    device = models.ForeignKey("Device", on_delete=models.CASCADE, related_name='devicescreenshot', verbose_name='装置')
    snap_timestamp = models.DateTimeField(verbose_name='装置截图时间')
    screenshot = models.ImageField(upload_to='device_screenshot', verbose_name='装置截图图片')

    class Meta:
        verbose_name_plural = "装置页面截图"


class DeviceTemperature(models.Model):
    device = models.ForeignKey("Device", on_delete=models.CASCADE, related_name='devicetemperature', verbose_name='装置')
    # 这笔纪录是在那一个机柜中产生的
    cabinet = models.ForeignKey("Cabinet", on_delete=models.CASCADE, related_name='devicetemperature',
                                verbose_name='机柜')
    description = models.CharField(max_length=50, verbose_name='描述')
    temp_port = models.ForeignKey("TempPort", on_delete=models.PROTECT, related_name='devicetemperature',
                                  verbose_name='温度端口')

    """
    不同于created_time, record_datetime是由客户端发送来的记录产生时间，
    created_time则是数据库中的资料产生时间
    """
    record_datetime = models.DateTimeField(default=timezone.now, verbose_name='记录温度时间')
    temperature = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='温度值')

    class Meta:
        verbose_name_plural = "装置温度"


class MonitorPort(models.Model):
    port = models.CharField(max_length=50, unique=True, db_index=True, verbose_name='相机编号')

    class Meta:
        verbose_name_plural = "相机编号"


class PowerPort(models.Model):
    port = models.CharField(max_length=50, unique=True, db_index=True, verbose_name='电量端口')
    device = models.OneToOneField(
        Device, models.SET_NULL,
        null=True, blank=True,
        related_name='powerport',
        verbose_name='装置'
    )
    # 该字段的计算依赖其它字段，由signal触发保存时自动填入
    status = models.CharField(max_length=50, blank=True, null=True, verbose_name='电量端口当前状态')
    woodenbox = models.ForeignKey(WoodenBox,
                                  models.SET_NULL,
                                  null=True,
                                  blank=True,
                                  related_name='powerport')
    is_active = models.BooleanField(default=True)

    objects = PowerPortManager()
    all_objects = PowerPortAllManager()

    @property
    def strategy_data(self):
        result = ''
        power_strategy_queryset = self.powerstrategy.all().order_by('is_default')
        if len(power_strategy_queryset) == 1:
            power_strategy = power_strategy_queryset[0]
            show_time = '默认策略'
            result += f'{show_time}: [{power_strategy.min_value}%, {power_strategy.max_value}%]；'
        else:
            for power_strategy in power_strategy_queryset:
                if power_strategy.is_default:
                    show_time = '其他时间'
                else:
                    show_time = f"{power_strategy.start_time.strftime('%H:%M')}" \
                               f"-" \
                               f"{power_strategy.end_time.strftime('%H:%M')}"
                result += f'{show_time}: [{power_strategy.min_value}%, {power_strategy.max_value}%]；'
        return result

    class Meta:
        verbose_name_plural = "电量端口"


class PowerStrategy(models.Model):

    power_port = models.ForeignKey(
        PowerPort,
        models.CASCADE,
        related_name='powerstrategy',
        verbose_name='电量端口'
    )
    min_value = models.SmallIntegerField(verbose_name='电量最小值')
    max_value = models.SmallIntegerField(verbose_name='电量最大值')
    start_time = models.TimeField(blank=True, null=True, verbose_name='策略开始时间')
    end_time = models.TimeField(blank=True, null=True, verbose_name='策略结束时间')
    is_default = models.BooleanField(default=False, verbose_name='是否默认策略')


class TempPort(models.Model):
    port = models.CharField(unique=True, max_length=50, db_index=True, verbose_name='温度端口号')
    # description 設為nullable
    # 在coral讀取到這個感溫片，並將他推進reef的時候，不會包含description訊息（尚未接觸到使用者）
    description = models.CharField(max_length=50, null=True, verbose_name='温度的描述信息')
    device = models.ForeignKey(Device,
                               models.SET_NULL,
                               null=True,
                               blank=True,
                               related_name='tempport',
                               verbose_name='装置'
                               )
    # 该字段的计算依赖其它字段，由signal触发保存时自动填入
    status = models.CharField(max_length=50, blank=True, null=True, verbose_name='温度端口状态')
    woodenbox = models.ForeignKey(WoodenBox,
                                  models.SET_NULL,
                                  null=True,
                                  blank=True,
                                  related_name='tempport')
    is_active = models.BooleanField(default=True)

    objects = ModelManager()
    all_objects = TempPortAllManager()

    class Meta:
        verbose_name_plural = "温度端口"


class PaneSlot(models.Model):
    paneview = models.ForeignKey("PaneView", on_delete=models.CASCADE, related_name="paneslots")
    row = models.PositiveIntegerField(verbose_name="row", help_text="于paneview中的row位置")
    col = models.PositiveIntegerField(verbose_name="col", help_text="于paneview中的col位置")
    status = models.CharField(max_length=16,
                              choices=(
                                  (PANESLOT_STATUS_OK, PANESLOT_STATUS_OK),
                                  (PANESLOT_STATUS_EMPTY, PANESLOT_STATUS_EMPTY),
                                  (PANESLOT_STATUS_ERROR, PANESLOT_STATUS_ERROR)
                              ),
                              verbose_name="Slot状态", help_text="Slot状态(ok, empty, error)",
                              default=PANESLOT_STATUS_EMPTY)
    device = models.OneToOneField("Device", verbose_name="关联设备", help_text="当前与slot关联的设备",
                                  on_delete=models.SET_NULL, null=True, related_name='paneslot')


class PaneView(models.Model):
    name = models.CharField(max_length=64, verbose_name="PaneView名称", help_text="PaneView名称", unique=True)
    type = models.CharField(max_length=16,
                            choices=(
                                (PANEVIEW_TYPE_MATRIX, PANEVIEW_TYPE_MATRIX),
                                (PANEVIEW_TYPE_MAP, PANEVIEW_TYPE_MAP),
                                (PANEVIEW_TYPE_TEST_BOX, PANEVIEW_TYPE_TEST_BOX)
                            ),
                            verbose_name="PaneView类型",
                            help_text="PaneView的类型(matrix, map)")
    cabinet = models.OneToOneField("Cabinet", on_delete=models.CASCADE, verbose_name="机柜", help_text="PaneView所属机柜",
                                   related_name='paneview', unique=True)
    width = models.PositiveIntegerField(verbose_name="PaneView宽度",
                                        help_text="PaneView的宽度，对于matrix类型的PaneView来说，代表的是有多少个column。"
                                                  "对于map类型来说，代表px")
    height = models.PositiveIntegerField(verbose_name="PaneView高度",
                                         help_text="PaneView的高度，对于matrix类型的PaneView来说，代表的是有多少个row。"
                                                   "对于map类型来说，代表px")
    robot_arm = models.CharField(max_length=30, verbose_name="机械臂", blank=True, null=True,
                                 help_text="text box类型paneview独有属性")
    camera = models.PositiveIntegerField(verbose_name="相机port", blank=True, null=True,
                                         help_text="text box类型paneview独有属性")


class DeviceCutCoordinate(models.Model):
    phone_model = models.ForeignKey(PhoneModel, on_delete=models.CASCADE, related_name="devicecutcoordinate")
    pane_view = models.ForeignKey(PaneView, on_delete=models.CASCADE, related_name='devicecutcoordinate')
    inside_upper_left_x = models.FloatField(blank=True, null=True, verbose_name='内框左上x坐标')
    inside_upper_left_y = models.FloatField(blank=True, null=True, verbose_name='内框左上y坐标')
    inside_under_right_x = models.FloatField(blank=True, null=True, verbose_name='内框右下x坐标')
    inside_under_right_y = models.FloatField(blank=True, null=True, verbose_name='内框右下y坐标')

    class Meta:
        verbose_name_plural = "设备裁剪坐标"
        unique_together = [['phone_model', 'pane_view']]
        index_together = [
            ['phone_model', 'pane_view']
        ]


class SubsidiaryDevice(AbsDescribe):
    """
    辅助测试设备 （当前不用于单独测试使用，不记录）
    """

    serial_number = models.CharField(max_length=200, unique=True, verbose_name='设备串口号')
    # ip字段后续迭代可能为空，暂时不添加和serial_number联合唯一限制
    ip_address = models.GenericIPAddressField(verbose_name='ip地址')
    """
    辅助设备相对于主机编号
    编号于主设备方位对应关系（当前规则）：
    1 --> 正后方
    2 --> 正前方
    3 --> 正左方
    """
    order = models.SmallIntegerField(verbose_name='相对于主设备的编号', blank=True, null=True)
    is_active = models.BooleanField(default=True, verbose_name='是否有效')
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='subsidiarydevice',
        verbose_name='关联主设备',
        blank=True,
        null=True
    )
    phone_model = models.ForeignKey(
        PhoneModel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subsidiarydevice',
        verbose_name='装置型号'
    )
    custom_name = models.CharField(max_length=50, null=True)
    """
    僚机定义为三种状态：
    busy, idle, unbound
    僚机状态跟随主机变更，offset，error对应unbound
    """
    status = models.CharField(default='unbound', max_length=50, verbose_name='设备状态')
    cabinet = models.ForeignKey(
        "Cabinet",
        on_delete=models.CASCADE,
        null=True,
        related_name='subsidiarydevice',
        verbose_name='机柜'
    )
    custom_number = models.CharField(max_length=100, default='', blank=True, verbose_name='自定义编号')

