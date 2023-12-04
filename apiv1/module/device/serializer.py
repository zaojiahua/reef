import collections
from abc import ABC

from django.db import transaction
from django.db.models import QuerySet
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator

from apiv1.core.constants import REEF_DEFAULT_MANUFACTURER, DEVICE_TYPE_TEST_BOX, DEVICE_TYPE_ADB, DEVICE_STATUS_IDLE, \
    DEVICE_STATUS_ERROR, DEVICE_STATUS_OFFLINE
from apiv1.core.response import reef_400_response
from apiv1.module.device.models import Device, DeviceScreenshot, AndroidVersion, RomVersion, Manufacturer, PhoneModel, \
    DeviceCoordinate, DevicePower, DeviceTemperature, PaneView, DeviceCutCoordinate, SubsidiaryDevice, \
    PhoneModelCustomCoordinate, PowerStrategy
from apiv1.module.system.models import Cabinet
from apiv1.module.device.models import MonitorPort, PowerPort, TempPort
from apiv1.module.device.validator import DeviceSourceValidator


class AndroidVersionSerializer(serializers.ModelSerializer):
    """
    Generic Serializer
    """

    class Meta:
        model = AndroidVersion
        fields = '__all__'


class DeviceSerializer(serializers.ModelSerializer):
    """
    Generic Serializer
    """
    # 当device的更新有涉及到相应的tempport，powerport时，相应的tempport，powerport关联的device也要改变
    tempport = serializers.PrimaryKeyRelatedField(
        queryset=TempPort.objects.all(), many=True, required=False)
    powerport = serializers.PrimaryKeyRelatedField(
        queryset=PowerPort.objects.all(), required=False, allow_null=True)
    monitor_index = serializers.PrimaryKeyRelatedField(
        queryset=MonitorPort.objects.all(), many=True, allow_empty=True)

    class Meta:
        model = Device
        fields = '__all__'


class DeviceCoordinateSerializer(serializers.ModelSerializer):
    """
    Generic Serializer
    """

    class Meta:
        model = DeviceCoordinate
        fields = '__all__'


class DevicePowerSerializer(serializers.ModelSerializer):
    """
    Generic Serializer
    """

    class Meta:
        model = DevicePower
        fields = '__all__'


class DeviceScreenshotSerializer(serializers.ModelSerializer):
    """
    Generic Serializer
    """

    class Meta:
        model = DeviceScreenshot
        fields = '__all__'


class DeviceTemperatureSerializer(serializers.ModelSerializer):
    """
    Generic Serializer
    """
    device = serializers.PrimaryKeyRelatedField(
        queryset=Device.objects.all(),
        required=False
    )
    cabinet = serializers.PrimaryKeyRelatedField(
        queryset=Cabinet.objects.all(),
        required=False
    )

    class Meta:
        model = DeviceTemperature
        fields = '__all__'

    def validate(self, attrs):
        p = DeviceSourceValidator(device_field='device', port_field='temp_port')
        if not self.partial:
            p(attrs)
        else:
            instance_field = collections.OrderedDict()
            instance = self.instance
            for k, v in attrs.items():
                setattr(instance, k, v)
            all_field = [field_name for field_name in self.fields]
            for field in all_field:
                instance_field[field] = getattr(instance, field, None)
            p(instance_field)
        return attrs

    def create(self, validated_data):
        if 'device' not in validated_data:
            validated_data['device'] = validated_data['temp_port'].device
        if 'cabinet' not in validated_data:
            validated_data['cabinet'] = validated_data['device'].cabinet
        return super(DeviceTemperatureSerializer, self).create(validated_data)


class ManufacturerSerializer(serializers.ModelSerializer):
    """
    Generic Serializer
    """

    class Meta:
        model = Manufacturer
        fields = '__all__'


class PhoneModelSerializer(serializers.ModelSerializer):
    """
    Generic Serializer
    """

    class Meta:
        model = PhoneModel
        fields = '__all__'


class RomVersionSerializer(serializers.ModelSerializer):
    """
    Generic Serializer
    """

    class Meta:
        model = RomVersion
        fields = '__all__'


class CreateDeviceScreenshotSerializer(serializers.ModelSerializer):
    """
    新增设备截图
    """
    device = serializers.SlugRelatedField(
        queryset=Device.objects.all(),
        slug_field='device_label'
    )
    snap_timestamp = serializers.DateTimeField(
        input_formats=['%Y_%m_%d_%H_%M_%S', '%Y-%m-%d %H:%M:%S']
    )

    class Meta:
        model = DeviceScreenshot
        fields = '__all__'


class CoordinateSerializer(serializers.Serializer):
    # 基于向前相容的考量，保留原属性命名风格
    LowerRight = serializers.ListField(child=serializers.IntegerField())
    UpperLeft = serializers.ListField(child=serializers.IntegerField())
    UpperRight = serializers.ListField(child=serializers.IntegerField())
    LowerLeft = serializers.ListField(child=serializers.IntegerField())

    def _len_eq2(self, value):
        if len(value) != 2:
            raise ValidationError('Field should has 2 elements')
        return value

    def validate_LowerRight(self, value):
        return self._len_eq2(value)

    def validate_UpperLeft(self, value):
        return self._len_eq2(value)

    def validate_UpperRight(self, value):
        return self._len_eq2(value)

    def validate_LowerLeft(self, value):
        return self._len_eq2(value)


class CoralDeviceReconnectSerializer(serializers.Serializer):

    rom_version = serializers.CharField()
    android_version = serializers.CharField()
    manufacturer = serializers.SlugRelatedField(
        slug_field="manufacturer_name", queryset=Manufacturer.objects.all(),
        required=False
    )
    device_label = serializers.SlugRelatedField(slug_field='device_label', queryset=Device.objects.all())
    ip_address = serializers.IPAddressField(required=False)
    status = serializers.CharField(required=False)


class CoralDeviceSerializer(serializers.ModelSerializer):
    """
    Coral创建/更新设备所使用的接口
    """
    android_version = serializers.CharField()
    device_label = serializers.CharField()
    rom_version = serializers.CharField()
    phone_model_name = serializers.CharField()
    manufacturer = serializers.CharField(required=False)
    cpu_name = serializers.CharField()
    power_port = serializers.CharField(required=False, allow_null=True)
    temp_port = serializers.ListSerializer(
        child=serializers.CharField(),
        required=False
    )
    monitor_index = serializers.CharField(required=False, allow_null=True)
    coordinate = CoordinateSerializer(required=False, allow_null=True)
    auto_test = serializers.BooleanField(required=False)
    x_border = serializers.FloatField(max_value=20, min_value=0, required=False)
    y_border = serializers.FloatField(max_value=20, min_value=0, required=False)
    y_dpi = serializers.FloatField(max_value=1000, min_value=100, required=False)
    x_dpi = serializers.FloatField(max_value=1000, min_value=100, required=False)
    device_type = serializers.ChoiceField(
        choices=[DEVICE_TYPE_TEST_BOX, DEVICE_TYPE_ADB],
        default=DEVICE_TYPE_ADB
    )
    status = serializers.CharField(required=False, default=DEVICE_STATUS_IDLE)
    width = serializers.FloatField(min_value=0, required=False)
    height = serializers.FloatField(min_value=0, required=False)
    ply = serializers.FloatField(min_value=0, required=False)
    height_resolution = serializers.IntegerField(min_value=0, required=False)
    width_resolution = serializers.IntegerField(min_value=0, required=False)
    custom_number = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Device
        fields = (
            'android_version',
            'cabinet',
            'cpu_id',
            'cpu_name',
            'device_label',
            'device_name',
            'ip_address',
            'monitor_index',
            'rom_version',
            'start_time_key',
            'temp_port',
            'power_port',
            'phone_model_name',
            'coordinate',
            'auto_test',
            'manufacturer',
            'x_border',
            'y_border',
            'x_dpi',
            'y_dpi',
            'device_type',
            'status',
            'width',
            'height',
            'ply',
            'width_resolution',
            'height_resolution',
            'custom_number'
        )

    @transaction.atomic
    def create(self, validated_data):
        """
        在Device创建时，会自动侦测部分资源是否存在，若对应的资源不存在则自动创建。
        拥有自动创建逻辑的资源如下:
        AndroidVersion / MonitorPort / RomVersion
        PhoneModel/ TempPort/ PowerPort
        其中，RomVersion，PhoneModel在创建的时候关联的是预设的Manufacturer: REEF_DEFAULT_MANUFACTURER
        """
        if 'manufacturer' not in validated_data:
            manufacturer = Manufacturer.objects.get(manufacturer_name=REEF_DEFAULT_MANUFACTURER)
        else:
            manufacturer, created = Manufacturer.objects.get_or_create(manufacturer_name=validated_data['manufacturer'])
            validated_data.pop("manufacturer")

        android_version = AndroidVersion.objects.get_or_create(
            defaults={
                'version': validated_data['android_version']
            },
            version=validated_data['android_version']
        )[0]
        validated_data['android_version'] = android_version

        # device : monitorport = n : n
        # monitorport get or create
        monitor_port = validated_data.pop('monitor_index', None)
        if monitor_port is not None:
            monitor_port = MonitorPort.objects.get_or_create(
                defaults={
                    'port': monitor_port
                },
                port=monitor_port
            )[0]

        # device : romversion = n : 1
        # romversion get or create
        rom_version = validated_data.pop('rom_version')
        rom_version = RomVersion.objects.get_or_create(
            defaults={
                'version': rom_version,
                'manufacturer': manufacturer
            },
            version=rom_version
        )[0]
        validated_data['rom_version'] = rom_version

        # device : phonemodel = n : 1
        # phonemodel get or create
        phone_model_name = validated_data.pop('phone_model_name')
        cpu_name = validated_data.pop('cpu_name')
        phone_model_data = {
            'phone_model_name': phone_model_name,
            'cpu_name': cpu_name,
            'manufacturer': manufacturer
        }
        # 一下字段传入才做更新
        fields_list = ['x_border', 'y_border', 'x_dpi', 'y_dpi', 'height', 'ply', 'width', 'height_resolution', 'width_resolution']
        _ = [
            phone_model_data.update({fields: validated_data.pop(fields, None)})
            if validated_data.get(fields, None) is not None else validated_data.pop(fields, None)
            for fields in fields_list
        ]

        phone_model = PhoneModel.objects.update_or_create(
            defaults=phone_model_data,
            phone_model_name=phone_model_name
        )[0]
        validated_data['phone_model'] = phone_model

        # device : tempport = 1 : n
        # tempport get or create
        temp_port = validated_data.pop('temp_port', None)
        temp_ports = []
        if temp_port is not None:
            for tp in temp_port:
                temp_port = TempPort.objects.get_or_create(
                    defaults={
                        'port': tp
                    },
                    port=tp
                )[0]
                temp_ports.append(temp_port)

        # device : powerport = 1 : 1
        # powerport get or create
        clear_power_port = "power_port" in validated_data and validated_data["power_port"] is None
        power_port = validated_data.pop('power_port', None)
        power_port_created = False
        if power_port is not None:
            power_port, power_port_created = PowerPort.objects.get_or_create(
                defaults={
                    'port': power_port,
                },
                port=power_port
            )

        coordinate = validated_data.pop('coordinate', None)

        # device create or update
        device, device_created = Device.objects.update_or_create(
            defaults=validated_data,
            device_label=validated_data.get('device_label')
        )

        if device_created and coordinate is not None:  # Create
            dc = DeviceCoordinate.objects.create(
                upper_left_x=coordinate['UpperLeft'][0],
                upper_left_y=coordinate['UpperLeft'][1],
                upper_right_x=coordinate['UpperRight'][0],
                upper_right_y=coordinate['UpperRight'][1],
                bottom_left_x=coordinate['LowerLeft'][0],
                bottom_left_y=coordinate['LowerLeft'][1],
                bottom_right_x=coordinate['LowerRight'][0],
                bottom_right_y=coordinate['LowerRight'][1]
            )
            device.coordinate = dc
            device.save()
        elif not device_created and coordinate is not None:  # Update
            device.coordinate.upper_left_x = coordinate['UpperLeft'][0]
            device.coordinate.upper_left_y = coordinate['UpperLeft'][1]
            device.coordinate.upper_right_x = coordinate['UpperRight'][0]
            device.coordinate.upper_right_y = coordinate['UpperRight'][1]
            device.coordinate.bottom_left_x = coordinate['LowerLeft'][0]
            device.coordinate.bottom_left_y = coordinate['LowerLeft'][1]
            device.coordinate.bottom_right_x = coordinate['LowerRight'][0]
            device.coordinate.bottom_right_y = coordinate['LowerRight'][1]
            device.coordinate.save()

        # device : powerport = 1 : 1
        if power_port is not None:
            for powerport in PowerPort.objects.filter(device_id=device.id):
                powerport.device_id = None
                powerport.save()
            power_port.device_id = device.id
            power_port.save()
        elif clear_power_port:
            for p in PowerPort.objects.filter(device_id=device.id):
                p.device_id = None
                p.save()

        # device : tempport = 1 : n
        if temp_port is not None:
            for tp in device.tempport.all():
                tp.device = None
                tp.save()
            for tp in temp_ports:
                tp.device = device
                tp.save()

        # device : monitor_index = n : n
        if monitor_port is not None:
            device.monitor_index.clear()
            device.monitor_index.add(monitor_port)

        return device


class LogoutDeviceSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Device.objects.all())


class MonitorPortSerializer(serializers.ModelSerializer):
    """
    Generic Serializer
    """

    class Meta:
        model = MonitorPort
        fields = '__all__'


class PowerPortSerializer(serializers.ModelSerializer):
    """
    Generic Serializer
    """

    class Meta:
        model = PowerPort
        fields = '__all__'


class TempPortSerializer(serializers.ModelSerializer):
    """
    Generic Serializer
    """
    description = serializers.CharField(allow_null=False)

    class Meta:
        model = TempPort
        fields = '__all__'


class TempPortCreateSerializer(TempPortSerializer):
    """
    Generic Serializer
    """
    description = serializers.CharField(allow_null=False, required=False)


class ReleaseDeviceSerializer(serializers.Serializer):
    ip_address = serializers.CharField()
    device_label = serializers.SlugRelatedField(
        slug_field='device_label',
        queryset=Device.objects.all()
    )
    tempport = serializers.ListField(required=False)
    unbind_resource = serializers.BooleanField(
        default=False
    )
    force = serializers.BooleanField()


class CreateDeviceTempByPortNameSerializer(serializers.ModelSerializer):
    device = serializers.PrimaryKeyRelatedField(
        queryset=Device.objects.all(),
        required=False
    )
    cabinet = serializers.PrimaryKeyRelatedField(
        queryset=Cabinet.objects.all(),
        required=False
    )
    temp_port = serializers.SlugRelatedField(
        queryset=TempPort.objects.all(),
        slug_field='port'
    )

    class Meta:
        model = DeviceTemperature
        fields = '__all__'
        validators = [
            DeviceSourceValidator(
                device_field='device',
                port_field='temp_port'
            )
        ]

    def create(self, validated_data):
        if 'device' not in validated_data:
            validated_data['device'] = validated_data['temp_port'].device
        if 'cabinet' not in validated_data:
            validated_data['cabinet'] = validated_data['device'].cabinet
        return super(CreateDeviceTempByPortNameSerializer, self).create(validated_data)


class CheckoutDeviceSerializer(serializers.Serializer):
    devices = serializers.PrimaryKeyRelatedField(
        queryset=Device.objects.all(),
        many=True
    )


class PaneviewSerializer(serializers.Serializer):
    class Meta:
        model = PaneView
        fields = '__all__'


class DeviceCutCoordinateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceCutCoordinate
        fields = '__all__'
        read_only = '__all__'


class GetDeviceCutCoordinateSerializer(serializers.Serializer):
    pane_view = serializers.PrimaryKeyRelatedField(
        queryset=PaneView.objects.all()
    )
    phone_model = serializers.PrimaryKeyRelatedField(
        queryset=PhoneModel.objects.all()
    )

    class Meta:
        model = DeviceCutCoordinate
        fields = ('pane_view', 'phone_model')


class CrtOrUptDeviceCutCoordinateSerializer(serializers.ModelSerializer):
    pane_view = serializers.PrimaryKeyRelatedField(
        queryset=PaneView.objects.all()
    )
    phone_model = serializers.PrimaryKeyRelatedField(
        queryset=PhoneModel.objects.all()
    )

    inside_upper_left_x = serializers.FloatField(required=True)
    inside_upper_left_y = serializers.FloatField(required=True)
    inside_under_right_x = serializers.FloatField(required=True)
    inside_under_right_y = serializers.FloatField(required=True)

    def get_unique_together_validators(self):
        """取消联合唯一校验，允许update操作"""
        return []

    class Meta:
        model = DeviceCutCoordinate
        fields = '__all__'


class SubsidiaryDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubsidiaryDevice
        fields = '__all__'


class CreateOrUpdateSubsidiaryDeviceSerializer(serializers.ModelSerializer):
    serial_number = serializers.CharField()

    class Meta:
        model = SubsidiaryDevice
        fields = '__all__'


class SubsidiaryDevicePhoneModelSerializer(serializers.ModelSerializer):
    manufacturer = serializers.CharField(required=False)
    phone_model_name = serializers.CharField()

    class Meta:
        model = PhoneModel
        exclude = ('id',)


class RegisterSubsidiaryDeviceSerializer(serializers.ModelSerializer):
    serial_number = serializers.CharField()
    phone_model = SubsidiaryDevicePhoneModelSerializer()
    custom_name = serializers.CharField(
    )
    ip_address = serializers.IPAddressField(
    )
    is_active = serializers.BooleanField(default=True)
    cabinet = serializers.SlugRelatedField(
        slug_field='id',
        queryset=Cabinet.objects.all(),
        required=True
    )
    custom_number = serializers.CharField(default='', required=False, allow_blank=True)


    # def validate(self, value):
    #     # ip_address unique checkout, 暂时不用
    #     serial_number = value.get('serial_number', None)
    #     ip_address = value.get('ip_address', None)
    #     queryset = SubsidiaryDevice.objects.exclude(
    #         serial_number=serial_number
    #     ).filter(ip_address=ip_address)
    #     if queryset.exists():
    #         raise ValidationError(
    #             {
    #                 "ip_address": [
    #                     "This field must be unique."
    #                 ]
    #             }
    #         )
    #     return value

    class Meta:
        model = SubsidiaryDevice
        fields = ('ip_address', 'custom_name', 'phone_model', 'serial_number', 'is_active', 'cabinet', 'custom_number')
        depth = 1

    @transaction.atomic()
    def create(self, validated_data):
        phone_model = validated_data['phone_model']
        if 'manufacturer' not in phone_model:
            manufacturer = Manufacturer.objects.get(manufacturer_name=REEF_DEFAULT_MANUFACTURER)
        else:
            manufacturer, created = Manufacturer.objects.get_or_create(manufacturer_name=phone_model['manufacturer'])
        phone_model['manufacturer'] = manufacturer
        phone_model, created = PhoneModel.objects.update_or_create(
            phone_model_name=phone_model['phone_model_name'],
            defaults=phone_model
        )
        validated_data['phone_model'] = phone_model
        serial_number = validated_data['serial_number']
        # 根据serial_number 更新或创建
        instance, created = SubsidiaryDevice.objects.update_or_create(
            serial_number=serial_number,
            defaults=validated_data,
        )
        return instance


class CancelSubsidiaryDeviceSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=SubsidiaryDevice.objects.all()
    )

    class Meta:
        model = SubsidiaryDevice
        fields = ('id',)


class BindSubsidiaryDeviceSerializer(serializers.Serializer):
    device_id = serializers.PrimaryKeyRelatedField(
        queryset=Device.objects.exclude(status__in=[DEVICE_STATUS_ERROR, DEVICE_STATUS_OFFLINE])
    )

    subsidiary_device_id = serializers.PrimaryKeyRelatedField(
        queryset=SubsidiaryDevice.objects.all()
    )

    order = serializers.IntegerField(min_value=1)

    class Meta:
        model = SubsidiaryDevice
        fields = ('device_id', 'subsidiary_device_id', 'order')


class UnbindSubsidiaryDeviceSerializer(serializers.Serializer):
    subsidiary_device_id = serializers.PrimaryKeyRelatedField(
        queryset=SubsidiaryDevice.objects.all()
    )

    class Meta:
        model = SubsidiaryDevice
        fields = ('subsidiary_device_id',)


class UpdatePhoneModelSerializer(serializers.ModelSerializer):
    phone_model_id = serializers.SlugRelatedField(
        slug_field='id',
        queryset=PhoneModel.objects.all()
    )
    x_dpi = serializers.FloatField(max_value=1000, min_value=100, required=False)
    y_dpi = serializers.FloatField(max_value=1000, min_value=100, required=False)
    x_border = serializers.FloatField(max_value=20, min_value=0, required=False)
    y_border = serializers.FloatField(max_value=20, min_value=0, required=False)
    phone_model_name = serializers.SlugRelatedField(
        slug_field='phone_model_name',
        queryset=PhoneModel.objects.all()
    )

    class Meta:
        model = PhoneModel
        fields = ('x_dpi', 'y_dpi', 'x_border', 'y_border', 'phone_model_id', 'phone_model_name')


class PhoneModelCustomCoordinateSerializer(serializers.ModelSerializer):

    class Meta:
        model = PhoneModelCustomCoordinate
        fields = '__all__'


class UpdatePhoneModelCustomCoordinateSerializer(serializers.Serializer):

    delete_list = serializers.ListField(required=False)
    create_or_update_list = serializers.ListField(required=False)

    def validate_create_or_update_list(self, value):
        if value:
            phone_model_id = value[0].get('phone_model')
            try:
                phone_model = PhoneModel.objects.get(id=phone_model_id)
            except Exception as e:
                reef_400_response(message=f'phone model id: {phone_model_id} not exit, {e}', description='机型信息不存在')
            for dict_data in value:
                dict_data['phone_model'] = phone_model
        return value


class PowerStrategySerializer(serializers.ModelSerializer):

    class Meta:
        model = PowerStrategy
        fields = '__all__'


class PowerPortStrategySerializer(serializers.ModelSerializer):

    powerstrategy = PowerStrategySerializer(many=True)

    class Meta:
        model = PowerPort
        fields = ('port', 'powerstrategy')


class PowerStrategyCheck(serializers.Serializer):

    min_value = serializers.IntegerField(min_value=0, max_value=100)
    max_value = serializers.IntegerField(min_value=0, max_value=100)
    start_time = serializers.TimeField(required=False)
    end_time = serializers.TimeField(required=False)
    is_default = serializers.BooleanField()


class AddPowerStrategySerializer(serializers.Serializer):

    power_port = serializers.PrimaryKeyRelatedField(
        queryset=PowerPort.objects.all()
    )

    power_strategy = PowerStrategyCheck(many=True)


class UpdateDeviceResolutionSerializer(serializers.Serializer):

    device_label = serializers.SlugRelatedField(
        slug_field='device_label',
        queryset=Device.objects.all()
    )

    height_resolution = serializers.IntegerField(min_value=0, required=False)
    width_resolution = serializers.IntegerField(min_value=0, required=False)


