from rest_framework import serializers


class DeviceSourceValidator:
    """
    验证数据类API中
    Device讯息是否有合理的来源
    1. 直接指定Device讯息
    2. 提供的port类资源有绑定的Device讯息
    
    port  |    device   |    cabinet   ||      valid     ||  cannot be null item
    =========================================================================================================
      v   |      v      |      v       ||        v       ||
      v   |      v      |      x       ||        v       ||  device.cabinet
      v   |      x      |      v       ||        v       ||  port.device
      v   |      x      |      x       ||        v       ||  port.device, port.device.cabinet
      x   |      v      |      v       ||        v       ||  device.port
      x   |      v      |      x       ||        v       ||  device.port, device.cabinet
      x   |      x      |      v       ||        x       ||
      x   |      x      |      x       ||        x       ||

    验证失败的情况： device is None或者没有传 并且 temp_port.device is None
    """
    def __init__(self, device_field, port_field):
        self.device_field = device_field
        self.port_field = port_field

    def __call__(self, attr):
        if (self.device_field not in attr or attr[self.device_field] is None) \
                and attr[self.port_field].device is None:
            raise serializers.ValidationError('There is no device info source!\n'
                                              'Both device and port.device are None\n')
