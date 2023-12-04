from django.urls import path, include

from apiv1.core import routers
from apiv1.module.device.view import DeviceTemperatureView, DeviceCreateUpdateView, CreateDeviceScreenshotView, \
    LogoutDeviceView, GetDeviceTemperatureRapidView, GetDevicePowerRapidView, GetDevicePowerBatteryLevel, \
    GetDevicePhoneModel, ReleaseDevice, CreateDeviceTempByPortNameView, CheckoutDeviceView, ControlDeviceCutCoordinate, \
    CreateOrUpdateSubsidiaryDeviceView, FilterSubsidiaryDeviceCount, BindSubsidiaryDeviceView, \
    UnbindSubsidiaryDeviceView, RegisterSubsidiaryDeviceView, CancelSubsidiaryDeviceView, UpdatePhoneModelView, \
    DeviceUpdateView, GetDeviceBat, UpdatePhoneModelCustomCoordinateView, AddPowerStrategy, UpdateDeviceResolution
from apiv1.module.device.views.create_paneview import CreatePaneViewView
from apiv1.module.device.views.create_text_box_paneview import CreateTestBoxPaneview
from apiv1.module.device.views.get_paneview import GetPaneViewView
from apiv1.module.device.views.link_paneview_device import LinkPaneViewDeviceView
from apiv1.module.device.views.remove_paneview import RemovePaneViewView
from apiv1.module.device.views.set_device_config_view import SetDeviceConfig
from apiv1.module.device.views.unlink_paneview_device import UnlinkPaneViewDeviceView
from apiv1.module.device.views.job_editor_control_device import ControlDevice
from apiv1.module.device.views.release_device import ReleaseOccupyDevice
from apiv1.module.device.viewset import DynamicDeviceViewSet, DynamicAndroidVersionViewSet, DynamicManufacturerViewSet, \
    DynamicPhoneModelViewSet, DynamicDeviceCoordinateViewSet, DynamicDevicePowerViewSet, \
    DynamicDeviceTemperatureViewSet, DynamicDeviceScreenshotViewSet, DynamicRomVersionViewSet, DynamicPaneViewViewSet, \
    DeviceCutCoordinateViewViewSet, SubsidiaryDeviceView, PhoneModelCustomCoordinateView, PowerStrategyView
from apiv1.module.device.viewset import DynamicMonitorPortViewSet, DynamicPowerPortViewSet, DynamicTempPortViewSet

router = routers.ReefDefaultRouter()

router.register(r'device', DynamicDeviceViewSet)
router.register(r'android_version', DynamicAndroidVersionViewSet)
router.register(r'manufacturer', DynamicManufacturerViewSet)
router.register(r'phone_model', DynamicPhoneModelViewSet)
router.register(r'device_coordinate', DynamicDeviceCoordinateViewSet)
router.register(r'device_power', DynamicDevicePowerViewSet)
router.register(r'device_temperature', DynamicDeviceTemperatureViewSet)
router.register(r'device_screenshot', DynamicDeviceScreenshotViewSet)
router.register(r'rom_version', DynamicRomVersionViewSet)
router.register(r'temp_port', DynamicTempPortViewSet)
router.register(r'power_port', DynamicPowerPortViewSet)
router.register(r'monitor_port', DynamicMonitorPortViewSet)
router.register(r'paneview', DynamicPaneViewViewSet)
router.register(r'devicecutcoordinate', DeviceCutCoordinateViewViewSet)
router.register(r'subsidiary_device', SubsidiaryDeviceView)
router.register(r'phone_model_custom_coordinate', PhoneModelCustomCoordinateView)
router.register(r'power_strategy', PowerStrategyView)

urlpatterns = [
    path('cedar/', include(router.urls)),

    # coral 创建/更新device信息
    # DoorKeeper（panedoor）因为一些因素无法简单判断注册的设备是否已经存在于数据库种，
    # 因此将设备的创建和更新聚合成一个接口
    path(
        'coral/create_update_device/',
        DeviceCreateUpdateView.as_view(),
        name='create_update_device'
    ),
    path(
        'coral/update_device/',
        DeviceUpdateView.as_view(),
        name='update_device'
    ),

    # 上传设备截图（monitor设备截图），device_label的原因不能用通用接口
    path(
        'coral/create_device_screenshot/',
        CreateDeviceScreenshotView.as_view(),
        name='create_device_screenshot'
    ),

    # 注销设备信息(没有使用，使用 release_device api)
    path(
        'coral/logout_device/',
        LogoutDeviceView.as_view(),
        name='logout_device'
    ),
    path(
        'cedar/get_bat/',
        GetDeviceBat.as_view(),
        name='get_device_bat'
    ),

    # 取得一个时间段内温度变化信息
    path(
        'cedar/rds/device/device_temperature/',
        DeviceTemperatureView.as_view(),
        name='device_temperature'
    ),

    # 获取设备在一段时间内温度变化信息，以供绘制电量变化折线图
    path('cedar/get_device_temperature_rapid/',
         GetDeviceTemperatureRapidView.as_view(),
         name='get_device_temperature_rapid'
         ),

    # 获取设备在一段时间内电量变化信息，以供绘制温度变折线图
    path('cedar/get_device_power_rapid/',
         GetDevicePowerRapidView.as_view(),
         name='get_device_power_rapid'
         ),

    # 获取设备的最新电量信息
    path(
        'cedar/get_device_power_battery_level/',
        GetDevicePowerBatteryLevel.as_view(),
        name='get_device_power_battery_level'
    ),

    # 获取所有device的phone_model的信息
    path(
        'cedar/get_device_phone_model/',
        GetDevicePhoneModel.as_view(),
        name='get_device_phone_model'
    ),

    # coral set_device_config proxy
    path(
        'coral/set_device_config/',
        SetDeviceConfig.as_view(),
        name='set_device_config'
    ),

    # coral release_device proxy
    path(
        'coral/release_device/',
        ReleaseDevice.as_view(),
        name='release_device'
    ),

    # 添加PaneView
    path(
        'cedar/create_paneview/',
        CreatePaneViewView.as_view(),
        name='create_paneview'
    ),

    # 取得paneview
    path(
        'cedar/get_paneview/',
        GetPaneViewView.as_view(),
        name='get_paneview'
    ),

    # 添加设备到paneview中
    path(
        'cedar/link_paneview_device/',
        LinkPaneViewDeviceView.as_view(),
        name='link_paneview_device'
    ),

    # 解除设备和Paneview的关联
    path(
        'cedar/unlink_paneview_device/',
        UnlinkPaneViewDeviceView.as_view(),
        name='unlink_paneview_device'
    ),

    path(
        'cedar/remove_paneview/',
        RemovePaneViewView.as_view(),
        name='remove_paneview'
    ),

    # 可以根据temp_port的port字段创建device_temperature
    path(
        'coral/create_device_tmp_by_port/',
        CreateDeviceTempByPortNameView.as_view(),
        name='create_device_tmp_by_port'
    ),

    # job editor control device
    path(
        'coral/control_device/',
        ControlDevice.as_view(),
        name='control_device'
    ),

    # release occupy device
    path(
        'coral/release_occupy_device/',
        ReleaseOccupyDevice.as_view(),
        name='release_occupy_device'
    ),

    # 添加test_box Paneview
    path(
        'cedar/create_test_box_paneview/',
        CreateTestBoxPaneview.as_view(),
        name='create_test_box_paneview'
    ),

    path('cedar/checkout_device/',
         CheckoutDeviceView.as_view(),
         name='checkout_device'
         ),

    path('cedar/control_device_cut_coordinate/',
         ControlDeviceCutCoordinate.as_view(),
         name='control_device_cut_coordinate'
         ),

    path('coral/create_or_update_subsidiary_device/',
         CreateOrUpdateSubsidiaryDeviceView.as_view(),
         name='create_or_update_subsidiary_device'
         ),

    path('cedar/filter_subsidiary_device_count/',
         FilterSubsidiaryDeviceCount.as_view(),
         name='filter_subsidiary_device_count'
         ),

    # 注册僚机
    path(
        'coral/register_subsidiary_device/',
        RegisterSubsidiaryDeviceView.as_view(),
        name='register_subsidiary_device'
    ),

    # 注销僚机
    path(
        'coral/cancel_subsidiary_device/',
        CancelSubsidiaryDeviceView.as_view(),
        name='cancel_subsidiary_device'
    ),

    # 绑定僚机
    path(
        'cedar/bind_subsidiary_device/',
        BindSubsidiaryDeviceView.as_view(),
        name='bind_subsidiary_device'
    ),

    # 解绑僚机
    path(
        'cedar/unbind_subsidiary_device/',
        UnbindSubsidiaryDeviceView.as_view(),
        name='unbind_subsidiary_device'
    ),
    # update phone model
    path(
        'cedar/update_phone_model/',
        UpdatePhoneModelView.as_view(),
        name='update_phone_model'
    ),

    path(
        'cedar/update_phone_model_custom_coordinate/',
        UpdatePhoneModelCustomCoordinateView.as_view(),
        name='update_phone_model_custom_coordinate'
    ),

    path(
        'cedar/add_power_strategy/',
        AddPowerStrategy.as_view(),
        name='add_power_strategy'
    ),

    path(
        'coral/update_device_resolution/',
        UpdateDeviceResolution.as_view(),
        name='update_device_resolution'
    )
]
