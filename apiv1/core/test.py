"""
这是Reef项目的单元测试工具模块
提供各类测试工具，协助撰写单元测试
"""
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils import timezone

from apiv1.core.constants import PANESLOT_STATUS_EMPTY, NORMAL_JOB_FLOW
from apiv1.module.device.models import Manufacturer, AndroidVersion, PhoneModel, RomVersion, Device, DeviceCoordinate, \
    DevicePower, DeviceTemperature, DeviceScreenshot, PaneSlot, PaneView
from apiv1.module.device.models import MonitorPort, PowerPort, TempPort
from apiv1.module.user.models import ReefUser
from apiv1.module.job.models import CustomTag, Job, JobTestArea, Unit, JobResourceFile, JobFlow
from apiv1.module.rds.models import Rds
from apiv1.module.system.models import System, Cabinet
from apiv1.module.tboard.models import TBoard


class TestTool:
    @staticmethod
    def create_test_user(user_number: int, **kwargs) -> ReefUser:
        """
        创建一个用户以供测试使用
        :param user_number: 流水编号，用以区分不同的用户
        :param kwargs: ReefUser参数，用以初始化ReefUser实例。例如: 若传入password=123456，则该用户将以123456作为用户密码
        :return: 创建好的ReefUser
        """
        user = ReefUser.objects.create_user(
            "test_user{}".format(user_number),
            "test_user{}@tests.com".format(user_number),
            "test_user{}".format(user_number),
        )

        for k, v in kwargs.items():
            setattr(user, k, v)
        user.save()
        return user

    @staticmethod
    def load_default_data(create_label: str = '0'):
        """
        提供预设的资料集合，并预先建立好数据关联
        :param create_label: 流水编号，用以区分Uniq字段。
        """
        created_model = {}
        created_model['user'] = ReefUser.objects.create_user(
            username='user{}'.format(create_label),
            email='user{}@tests.com',
            password='user{}'.format(create_label)
        )
        created_model['system'] = System.objects.create(
            system_name='system{}'.format(create_label),
            ip_address='192.168.1.100'
        )
        created_model['cabinet'] = Cabinet.objects.create(
            cabinet_name='cabinet{}'.format(create_label),
            ip_address='192.168.1.100',
            belong_to=created_model['system']
        )
        created_model['manufacturer'] = Manufacturer.objects.create(
            manufacturer_name='manufacturer{}'.format(create_label)
        )
        created_model['android_version'] = AndroidVersion.objects.create(
            version='8.1.0',
        )
        created_model['phone_model'] = PhoneModel.objects.create(
            phone_model_name='phone_model{}'.format(create_label),
            manufacturer=created_model['manufacturer'],
            cpu_name='Intel Core i7 8650 U'
        )
        created_model['rom_version'] = RomVersion.objects.create(
            manufacturer=created_model['manufacturer'],
            version='rom_version{}'.format(create_label)
        )
        created_model['temp_port'] = TempPort.objects.create(
            port='PA-{}'.format(create_label),
            description='top{}'.format(create_label),
        )
        created_model['power_port'] = PowerPort.objects.create(
            port='PA-{}'.format(create_label),
        )
        created_model['monitor_port'] = MonitorPort.objects.create(
            port='PA-{}'.format(create_label),
        )
        created_model['device'] = Device.objects.create(
            device_label='device{}'.format(create_label),
            device_name='device{}'.format(create_label),
            cabinet=created_model['cabinet'],
            ip_address='192.168.1.1',
            android_version=created_model['android_version'],
            phone_model=created_model['phone_model'],
            cpu_id='CPU-Z',
            rom_version=created_model['rom_version']
        )
        created_model['device_coordinate'] = DeviceCoordinate.objects.create(
            bottom_left_x=0,
            bottom_left_y=0,
            upper_left_x=0,
            upper_left_y=0,
            bottom_right_x=0,
            bottom_right_y=0,
            upper_right_x=0,
            upper_right_y=0
        )
        created_model['device'].coordinate = created_model['device_coordinate']

        created_model['device'].tempport.add(created_model['temp_port'])

        created_model['custom_tag'] = CustomTag.objects.create(
            custom_tag_name='custom_tag_name{}'.format(create_label)
        )

        created_model['device_power'] = DevicePower.objects.create(
            device=created_model['device'],
            cabinet=created_model['cabinet'],
            battery_level=50,
            charging=False,
            power_port=created_model['power_port']
        )
        created_model['device_tempurature'] = DeviceTemperature.objects.create(
            device=created_model['device'],
            cabinet=created_model['cabinet'],
            temperature=40,
            temp_port=created_model['temp_port']
        )
        created_model['device-screenshot'] = DeviceScreenshot.objects.create(
            device=created_model['device'],
            snap_timestamp=timezone.now(),
        )

        created_model['job'] = Job.objects.create(
            job_label='job{}'.format(create_label),
            job_name='job{}'.format(create_label),
            description='description',
            author=created_model['user']
        )
        ui_json_file = TestTool.create_memory_uploaded_file('apiv1/module/job/tests/file/ui.json', 'ui.json')
        created_model['job_flow'] = JobFlow.objects.create(
            name='job_flow{}'.format(create_label),
            job=created_model['job'],
            flow_type=NORMAL_JOB_FLOW,
            order=1,
            ui_json_file=ui_json_file
        )
        ui_json_file.close()
        created_model['job'].custom_tag.add(created_model['custom_tag'])
        created_model['job'].phone_models.add(created_model['phone_model'])
        created_model['job'].android_version.add(created_model['android_version'])

        created_model['job_test_area'] = JobTestArea.objects.create(
            description='description{}'.format(create_label)
        )

        created_model['tboard'] = TBoard.objects.create(
            author=created_model['user'],
            repeat_time=2,
            board_name='tboard{}'.format(create_label),
            finished_flag=False,
            board_stamp=timezone.now(),
            end_time=timezone.now()
        )

        created_model['rds'] = Rds.objects.create(
            device=created_model['device'],
            job=created_model['job'],
            tboard=created_model['tboard']
        )

        created_model['unit'] = Unit.objects.create(
            unit_name='job{}'.format(create_label),
            unit_content={'unit': 'content'},
            type='ADBC'
        )
        job_resource_file = open('apiv1/module/job/tests/file/4c-blueTooth.png', 'rb')
        up_file = InMemoryUploadedFile(job_resource_file, None, '4c-blueTooth.png', None, None, None, None)
        created_model['job_res_file'] = JobResourceFile.objects.create(
            job_flow=created_model['job_flow'],
            file=up_file,
            type='png',
            name='4c-blueTooth.png'
        )
        job_resource_file.close()

        created_model['paneview'] = PaneView.objects.create(
            name="paneview",
            type="matrix",
            cabinet=created_model["cabinet"],
            width=2,
            height=2
        )

        paneslots = []
        for i in range(created_model["paneview"].width):
            for j in range(created_model["paneview"].height):
                ps = PaneSlot.objects.create(
                    paneview=created_model['paneview'],
                    row=j,
                    col=i,
                    status=PANESLOT_STATUS_EMPTY
                )
                paneslots.append(ps)

        created_model['paneslot'] = paneslots[0]

        return created_model

    @staticmethod
    def temp_cabinet(operate, cabinet, **kwargs):
        if operate == 'create':
            parameter = {
                'cabinet_name': 'cabinet{}'.format(111),
                'ip_address': '111.11.1.1'
            }
            parameter.update(kwargs)
            cabinet = Cabinet.objects.create(
                **parameter
            )
            return cabinet
        elif operate == 'delete':
            cabinet.delete()

    @classmethod
    def create_memory_uploaded_file(cls, path, filename):
        f = open(path)
        up_file = InMemoryUploadedFile(f, None, filename, None, None, None, None)
        return up_file

#################################
# Decorators                    #
#################################

# 支持的Http Method
VALID_METHOD = ("get", "head", "post", "put", "delete", "connect", "options", "trace", "patch")


# Testcase Counter
def tccounter(name: str, method: str, enable: bool):
    """
    测试用例信息装饰器，用以提供测试用例的相关信息
    name: api viewname
    method: http method
    enable: 是否启用，启用时，用例函数不再执行测试代码，而是简单的返回 viewname 和 http method
    """
    method = method.lower()
    if method not in VALID_METHOD:
        raise ValueError(f"method: {method} not valid! The valid method is one of {VALID_METHOD}")

    def wrapper(func):
        if enable:
            def show(*args, **kwargs):
                return name, method

            return show
        else:
            def original_func(*args, **kwargs):
                return func(*args, **kwargs)

            return original_func

    return wrapper
