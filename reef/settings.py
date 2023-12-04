import os
import platform
import re
import socket

from pathlib import Path

#####################################################################
# 基本配置                                                          #
#####################################################################
import redis
from django_redis import get_redis_connection

DEBUG = True
ROOT_URLCONF = 'reef.urls'  # 根URL
GENERIC_VIEW_DEPTH = 0  # 若未指定任何通用接口的字段， 预设的返回关联深度
CORAL_PORT = 5000
REEF_USE_CACHE = True
SHOW_SWAGGER = bool(os.environ.get('SHOW_SWAGGER', 0))
REEF_VERSION = "feature/add-special-job-api"
REEF_SERVER_IP = '10.5.41.9'

#####################################################################
# 测试配置                                                           #
#####################################################################
ENABLE_TCCOUNTER = False  # 启用时，可透过export_testcase_count命令统计单元测试数量


#####################################################################
# 基本配置 (几乎不会修改的基本配置)                                   #
#####################################################################
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = '5dyrwk3r60her_jv8lu@q^u$qdf$ait&0k_a$i%gh-9&6$qmtw'
WSGI_APPLICATION = 'reef.wsgi.application'
AUTH_USER_MODEL = 'apiv1.ReefUser'
# DEFAULT_CONTENT_TYPE = 'application/json'

#####################################################################
# Redis连接                                                       #
#####################################################################
REDIS_IP = '172.80.0.7' if platform.system() == 'Linux' else '127.0.0.1'
REDIS_PORT = 6379
redis_connect = redis.Redis(host=REDIS_IP, port=REDIS_PORT, db=0)
# 这边并未处理连接池，而是偷懒都使用同一个连接，要注意若在多
# 个地方开启事务, Watch可能会有问题，有空的话建议改写成连接池

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{REDIS_IP}:{REDIS_PORT}/0",
        "OPTIONS": {
            "CONNECTION_POOL_KWARGS": {"max_connections": 100},
            "SOCKET_CONNECT_TIMEOUT": 2,  # seconds
            "SOCKET_TIMEOUT": 2
        }
    }
}

r_client = get_redis_connection('default')
connection_pool = r_client.connection_pool
redis_pool_connect = redis.Redis(connection_pool=connection_pool)


#####################################################################
# Celery配置                                                        #
#####################################################################
# see http://docs.celeryproject.org/en/latest/userguide/configuration.html#broker-settings
CELERY_BROKER_URL = f"redis://{REDIS_IP}:{REDIS_PORT}/3"

# see http://docs.celeryproject.org/en/latest/userguide/configuration.html#redis-backend-settings

CELERY_RESULT_BACKEND = f"redis://{REDIS_IP}:{REDIS_PORT}"

# task result data_done 时间是utc时间，不受配置控制，位置 _store_result 函数。
CELERY_ENABLE_UTC = False
CELERY_TIMEZONE = 'Asia/Shanghai'
# see https://docs.celeryproject.org/en/master/userguide/configuration.html
# worker num
CELERY_WORKER_CONCURRENCY = 6
# worker use max memory 500M
CELERY_WORKER_MAX_MEMORY_PER_CHILD = 500000
# worker 可执行任务最大次数
CELERY_WORKER_MAX_TASKS_PER_CHILD = 20
# task 运行最大时间, 超时会被kill，日志中会有记录，单位秒
CELERY_TASK_TIME_LIMIT = 3600


#####################################################################
# Channels                                                       #
#####################################################################
ASGI_APPLICATION = 'reef.routing.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(REDIS_IP, REDIS_PORT)],
        },
    },
}

#####################################################################
# 文件                                                              #
#####################################################################
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static" + os.sep)

MEDIA_ROOT = os.path.join(os.path.split(BASE_DIR)[0], 'media')
MEDIA_URL = '/media/'

# 上传文件大小(小于存在内存，大于存在硬盘)
# FILE_UPLOAD_MAX_MEMORY_SIZE  default 2621440 (i.e. 2.5 MB)

# 上传文件权限设置
FILE_UPLOAD_PERMISSIONS = 0o644

# job导出压缩包存放位置
JOB_EXPORT = 'job_export'
JOB_EXPORT_ZIP_ROOT = os.path.join(MEDIA_ROOT, JOB_EXPORT)
os.makedirs(JOB_EXPORT_ZIP_ROOT, exist_ok=True)

# job导入文件临时存放位置
JOB_IMPORT = 'job_import'
JOB_IMPORT_TMP_ROOT = os.path.join(MEDIA_ROOT, JOB_IMPORT)
os.makedirs(JOB_IMPORT_TMP_ROOT, exist_ok=True)

# job res file导出位置
JOB_RES_FILE_EXPORT = 'job_res_file_export'
JOB_RES_FILE_EXPORT_PATH = os.path.join(MEDIA_ROOT, JOB_RES_FILE_EXPORT)
os.makedirs(JOB_RES_FILE_EXPORT_PATH, exist_ok=True)

# resource excel file space
RESOURCE_EXCEL_FILE_EXPORT = 'resource_excel_export'
RESOURCE_EXCEL_FILE_EXPORT_PATH = os.path.join(MEDIA_ROOT, RESOURCE_EXCEL_FILE_EXPORT)
os.makedirs(RESOURCE_EXCEL_FILE_EXPORT_PATH, exist_ok=True)

# excel table head
SIM_CARD_EXPORT_TABLE_HEAD = [
    'operator', 'is_volte', 'phone_number'
]
ACCOUNT_EXPORT_TABLE_HEAD = [
    'name', 'username', 'password', 'phone_number', 'app_name'
]

#####################################################################
# 国际化                                                             #
# https://docs.djangoproject.com/en/2.0/topics/i18n/                #
#####################################################################
# 语言
LANGUAGE_CODE = 'en-us'
USE_I18N = True
USE_L10N = True

# 时间
TIME_ZONE = 'Asia/Shanghai'
USE_TZ = True

#####################################################################
# App配置                                                           #
#####################################################################
INSTALLED_APPS = [
    # core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # reef apps
    'apiv1.apps.Apiv1Config',

    # third party
    'channels',
    'rest_framework',
    'django_elasticsearch_dsl',
    'rest_framework.authtoken',
    'corsheaders',
    'drf_yasg',
]

#####################################################################
# Middleware                                                        #
#####################################################################
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if SHOW_SWAGGER:
    MIDDLEWARE += [
        'apiv1.middleware.SwaggerUrlCheckMiddleware',
    ]

#####################################################################
# 跨域请求头配置                                                     #
#####################################################################
ALLOWED_HOSTS = ['*']
CORS_ORIGIN_ALLOW_ALL = True
CORS_EXPOSE_HEADERS = ["Total-Count"]
CORS_ALLOW_CREDENTIALS = True

#####################################################################
# 模板配置                                                          #
#####################################################################
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

#####################################################################
# 数据库配置                                                         #
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases     #
#####################################################################
DATABASE_DEV_ENV = False
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        # reef db ip config(for mark)
        'HOST': '172.80.0.2' if platform.system() == 'Linux' else '127.0.0.1',
        'NAME': 'reef',
        'PORT': '5432',
        'USER': 'postgres',
        'PASSWORD': 'Hy1Nv9LX',
        'CONN_MAX_AGE': 300,
        'TEST': {
            'NAME': 'reef_test'
        },
    } if not DATABASE_DEV_ENV else
    {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3'
    }

}

#####################################################################################
# 密码验证配置                                                                       #
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators      #
#####################################################################################
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

#####################################################################
# Logger配置                                                        #
#####################################################################
FILE_LOG_LEVEL = 'ERROR'
CONSOLE_LOG_LEVEL = 'INFO'
DEBUG_LOG_LEVEL = 'DEBUG'

if platform.system() == 'Linux':
    LOG_DIR = Path('/app').joinpath('log')
else:
    LOG_DIR = r'./log'
if not os.path.exists(LOG_DIR):
    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

if platform.system() != 'Windows':
    MIDDLEWARE.append('apiv1.middleware.DataRecordLogMiddleware')
    REEF_LOG_FILE = os.path.join(LOG_DIR, 'reef.log')
    DEBUG_LOG_FILE = os.path.join(LOG_DIR, 'debug_reef.log')

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,

        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(name)s:%(filename)s:%(lineno)d][%(levelname)-8s] %(message)s'
            },
            'backend': {
                'format': '%(asctime)s [%(name)s:%(pathname)s:%(lineno)d][%(levelname)-8s] %(message)s'
            },
        },
        'handlers': {
            'console': {
                'level': CONSOLE_LOG_LEVEL,
                'class': 'logging.StreamHandler',
                'formatter': 'standard'
            },
            'file': {
                'level': FILE_LOG_LEVEL,
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'when': 'MIDNIGHT',
                'backupCount': 30,
                'formatter': 'backend',
                'filename': REEF_LOG_FILE
            },
            'debug': {
                'level': DEBUG_LOG_LEVEL,
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'when': 'MIDNIGHT',
                'backupCount': 10,
                'formatter': 'backend',
                'filename': DEBUG_LOG_FILE
            }
        },
        'loggers': {
            'backend': {
                'handlers': ['file'],
                'level': FILE_LOG_LEVEL,
                'propagate': True,
            },
            'django.db.backends': {
                'handlers': ['console'],
                'propagate': True,
                'level': CONSOLE_LOG_LEVEL,
            },
            'django.request': {
                'handlers': ['file'],
                'level': FILE_LOG_LEVEL,
            },
            'debug': {
                'handlers': ['debug'],
                'level': DEBUG_LOG_LEVEL,
                'propagate': True,
            }
        },
    }

#####################################################################
# RestFramework                                                     #
#####################################################################
REST_FRAMEWORK = {
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100,
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'apiv1.authentication.BareTokenAuthentication',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '2000/minute',
        'user': '2000/minute'
    }
}

#####################################################################
# 搜寻引擎                                                           #
#####################################################################
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': '10.0.0.190:9200'
    },
}


from functools import partial

DINGDINGWEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=b59623841c98c3616a7b386e891ebd20464990e847350284e2c1d4187f706a1d"