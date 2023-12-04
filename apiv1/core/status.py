"""
项目扩展状体码，用以补足Http状态吗无法表达的信息

注意！！！
如果想表达信息能够使用标准Http状态吗表达，应以标准Http状态吗为优先
不宜过度扩充状态吗
"""
from enum import Enum, unique

"""
错误码设计格式说明：
    统一格式: ABBCCC
    A: 错误级别，1代表系统级错误(Example：参数错误，数据不存在...)，2代表服务级错误（Example：设备状态错误...）
    B: 项目或模块名称 (Example: 设备模块，job模块)
    C: 具体错误编号，自增即可。
    
    模块编号定义：
        00 -- Database
        01 -- User
        02 -- Device
        03 -- Job
        04 -- TBoard
        05 -- Abnormity
        06 -- RDS
        20 -- Storage file
        
"""


@unique
class StatusCode(Enum):

    """
    系统级别
    """
    # 请求coral失败
    REQUEST_CORAL_FAILED = 104001
    # 设备请求coral失败
    DEVICE_REQUEST_CORAL_FAILED = 102001
    # Data not exist
    QUERY_DATABASE_DATA_FAILED = 100001
    """
    服务级别
    """
    # 设备不是idle状态
    DEVICE_NOT_IDLE = 204001
    # Job not exist
    JOB_NOT_EXIST = 203001
    # Job cannot delete
    JOB_DELETE_ERROR = 203002
    # 设备是busy状态
    DEVICE_IS_BUSY = 202001
    # 没有管理员权限
    NOT_ADMIN_PERMISSION = 201001




