"""
记录Reef项目经常使用到的各种常数变量
"""

# Job Module
JOB_TYPE_UNIQ = "Uniq"
JOB_TYPE_JOB_LIB = "Joblib"
JOB_TYPE_SYS_JOB = "Sysjob"
JOB_TYPE_UNKNOWN = "UnKnow"
JOB_TYPE_INNER_JOB = "InnerJob"
JOB_TYPE_PERF_JOB = "PerfJob"
JOB_TYPE_PRIOR_JOB = "PriorJob"
JOB_TYPE_MULTI_DEVICE_JOB = "MultiDevice"
JOB_TYPE_COMBO_JOB = 'ComboJob'
JOB_SECOND_TYPE_TIME_JOB = "TimeJob"
JOB_SECOND_TYPE_SMOOTHLY_JOB = 'SmoothJob'

# Job Flow Execute Module
JOB_FLOW_EXECUTE_SPLIT = 'SingleSplit'
JOB_FLOW_EXECUTE_MULTI = 'MultiSet'

# Job Flow Type
NORMAL_JOB_FLOW = 'NormalFlow'
INNER_JOB_FLOW = 'InnerFlow'

# Device Module
DEVICE_STATUS_OFFLINE = "offline"
DEVICE_STATUS_BUSY = "busy"
DEVICE_STATUS_ERROR = "error"
DEVICE_STATUS_IDLE = "idle"
DEVICE_STATUS_OCCUPIED = "occupied"
DEVICE_OCCUPY_TYPE_JOB_EDITOR = "job_editor"
DEVICE_TYPE_TEST_BOX = 'test_box'
DEVICE_TYPE_ADB = 'adb'

# PowerPort Status
POWER_PORT_STATUS_BUSY = 'busy'
POWER_PORT_STATUS_IDLE = 'idle'

# PaneView Type
PANEVIEW_TYPE_MATRIX = "matrix"
PANEVIEW_TYPE_MAP = "map"
PANEVIEW_TYPE_TEST_BOX = 'test_box'

# PaneSlot Status
PANESLOT_STATUS_OK = "ok"
PANESLOT_STATUS_EMPTY = "empty"
PANESLOT_STATUS_ERROR = "error"

# WoodenBox Type
WOODENBOX_TYPE_POWER = "power"
WOODENBOX_TYPE_TEMP = "temp"

RDS_FILTER_SERIOUS = 'serious'

POWER_CONSUMPTION_ERROR_CODE = "-101"
TEMP_CONSUMPTION_ERROR_CODE = "-999.99"

REEF_DEFAULT_MANUFACTURER = "Xiaomi"

JOB_RESOURCE_FILE_TYPE = ['txt', 'json', 'java', 'lua', 'py', 'pl', 'png', 'jpg',
                          'bmp', 'jpeg', 'gif', 'mp4', 'mov', 'mp3', 'apk', 'img', 'log', 'zip']

# channel group
TBOARD_DELETE_GROUP = 'tboard_delete'
TBOARD_DELETE_FAIL_GROUP = 'tboard_deleted_fail'
LOG_DELETE_GROUP = 'log_delete'

# redis
REDIS_TBOARD_DELETE = 'tboard:delete'
REDIS_TBOARD_DELETE_FAIL = 'tboard:deleted_fail'
REDIS_LOG_DELETE = 'log:delete'
REDIS_COOLPAD_POWER_LAST_TIME = 'coolpad:power_last'

# cache leading key
REDIS_CACHE_GET_DATA_VIEW = 'cache:get_data_view'
REDIS_CACHE_GET_DATA_VIEW_SUMMERY = 'cache:get_data_view_summery'
REDIS_CACHE_GET_TBOARD_STATISTIC = 'cache:get_tboard_statistic'
REDIS_CACHE_GET_DEVICE_TEMPERATURE_RAPID = 'cache:get_device_temperature_rapid'
REDIS_CACHE_GET_DEVICE_POWER_RAPID = 'cache:get_device_power_rapid'
REDIS_CACHE_GET_RDS_RAPID = 'cache:get_rds_rapid'
REDIS_CACHE_GET_DATA_VIEW_CALENDAR = 'cache:get_data_view_calendar'

# celery delayed task
REDIS_DEVICE_PREFIX = 'device'
DELAYED_TASK_TIME = 1800
DELAYED_TASK_EXPIRES_TIME = 1850

# user
REEF_SUPER_USER = 'admin'
REEF_DEFAULT_USER = 'user-default000000000001'
REEF_USER_DEFAULT_PASSWORD = 'default123'

REEF_ADMIN_GROUP_NAME = 'Admin'
REEF_MANAGER_GROUP_NAME = 'Manager'
REEF_DATA_VIEWER_GROUP_NAME = 'DataViewer'
REEF_TEST_OPERATOR_GROUP_NAME = 'TestOperator'

CABINET_TYPE_LIST = [
    ('Tcab_1', 'Tcab_1'),
    ('Tcab_2', 'Tcab_2'),
    ('Tcab_3', 'Tcab_3'),
    ('Tcab_4', 'Tcab_4'),
    ('Tcab_5', 'Tcab_5'),
]

# Open API
# CoolPad API

# get crumb 每次请求前重新获取
COOLPAD_GET_CRUMB = 'http://172.16.3.129:8080/crumbIssuer/api/json'
# 上传用例结果数据到酷派
COOLPAD_UPLOAD_TBOARD_DATA = 'http://172.16.3.129:8080/job/ODVB_cloud_TMach_result/buildWithParameters'
