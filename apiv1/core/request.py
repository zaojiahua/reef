import requests

from apiv1.core.utils import ReefLogger
from apiv1.module.system.models import Cabinet
from reef import settings


def try_ex_decorator(func):
    def wrapper(obj, log_info):
        try:
            return func(obj, log_info)
        except Exception as e:
            reef_logger = ReefLogger('debug')
            reef_logger.debug(
                f"\n"
                f"{'-' * 50}\n"
                f"Info: {log_info}\n"
                f"Exception info: {e}\n"
            )
    return wrapper


class Empty:

    pass


class ReefRequest:
    """
    封装请求，使用decorator捕获请求错误，写入debug log中。
    """

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_singleton"):
            setattr(ReefRequest, "_singleton", super().__new__(cls))
        return cls._singleton

    def __init__(self, url, **kwargs):
        self.url = url
        self.kwargs = kwargs

    @try_ex_decorator
    def post(self, log_info):
        rep = requests.post(self.url, **self.kwargs)
        return rep

    @try_ex_decorator
    def get(self, log_info):
        rep = requests.get(self.url, **self.kwargs)
        return rep


def sync_info_to_coral(body_data, log_info=Empty):
    """
    通知reef下的所有corl主机
    """
    for ip_address in Cabinet.objects.filter(is_delete=False).values_list('ip_address', flat=True):
        url = f"http://{ip_address}:{settings.CORAL_PORT}/door/door_info/"
        parameter = {"json": body_data, "timeout": 0.2}
        req = ReefRequest(url, **parameter)
        dict_data = {"coral_ip": ip_address, "body": body_data}
        if log_info is not Empty:
            dict_data.update(log_info)
        req.post(dict_data)

