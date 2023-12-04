import logging

from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework import status

from reef.settings import FILE_LOG_LEVEL


class SwaggerUrlCheckMiddleware(MiddlewareMixin):
    """
    自动文档检查，若有新开发的API含有url参数，而没有宣告core fields
    抛出异常
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        url_param = request.GET.keys()
        pagination_param = ('limit', 'offset')

        method = request.method.lower()
        if not hasattr(view_func, 'cls'):   # 排除view_func不存在cls的情况（eg:localhost:8000/admin）
            return
        view = view_func.cls

        action = getattr(view, 'action', method)
        action_method = getattr(view, action, None)
        overrides = getattr(action_method, '_swagger_auto_schema', {})

        # overrides eg:
        # {'get':{'manual_parameters':[Paramter([('name','tboard_id'),('in','query'),
        #                                         ('description','tboard_id'),('type','integer')])]}}

        if overrides is None:                 # 判断overrides是否为空
            return

        if method not in overrides:           # 判断overrides中是否有请求方式
            return

        if 'manual_parameters' not in overrides[method]:    # 判断是否有额外添加的参数（manual_parameters）
            return

        extra_param = [i.name for i in overrides[method]['manual_parameters']]
        missing_param = set(url_param) - (set(url_param) & set(extra_param) | set(pagination_param))

        if len(missing_param) != 0:
            return HttpResponse('Please Check you view_cls core_api_fields',
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return


class DataRecordLogMiddleware(MiddlewareMixin):
    """
    Log所有的Request信息(根据Log Level)
    """

    def __init__(self, *args):
        super(DataRecordLogMiddleware, self).__init__(*args)
        self.request_parameter = None
        self.logger = logging.getLogger('backend')

    def process_request(self, request):
        request_method = request.method
        if request_method == 'POST':
            try:
                self.request_parameter = str(request.body, encoding='utf-8')
            except:
                self.request_parameter = ''
        elif request_method == 'GET':
            self.request_parameter = request.GET.dict()

    def process_response(self, request, response):
        user = request.user
        api = request.get_full_path()
        request_method = request.method
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        if FILE_LOG_LEVEL == 'DEBUG':
            meta = request.META
            header = ''
            for k, v in meta.items():
                if type(meta[k]) == str:
                    header = header + '\n' + k + ': ' + v
            self.logger.debug("\n"
                              f"Api: {api}\n"
                              f"User: {user}\n"
                              f"Ip: {ip}\n"
                              f"Method: {request_method}\n"
                              f"Path: {request.path}\n"
                              f"Request_header: {header}\n"
                              f"Parameter: {self.request_parameter}\n"
                              f"Response_headers: {response._headers}\n"
                              f"Status_code: {response.status_code}\n"
                              f"Reason_phrase: {response.reason_phrase}")
        elif FILE_LOG_LEVEL == 'ERROR':
            if response.status_code // 100 != 2:
                try:
                    response_data = response.data
                except:
                    response_data = None
                log_data = (
                    f'\n'
                    f'Api: {api}\n'
                    f'Ip:{ip}\n'
                    f'Method: {request_method}\n'
                    f'Response_Code: {response.status_code}\n'
                    f'Response_body: {response_data}\n'
                    f'User: {user}\n'
                )
                # GET方法不添加parameter
                if request_method != 'GET':
                    log_data = log_data + f'Parameter: {self.request_parameter}\n'
                self.logger.error(log_data)

        return response
