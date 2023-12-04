import itertools, logging
import os.path

import numpy as np
import pandas as pd
from datetime import timedelta, date, datetime
from distutils.util import strtobool

import pytz
from django.utils import timezone
from django.db.models.query import QuerySet
from django.db.models.manager import Manager
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.throttling import AnonRateThrottle

from reef import settings
from reef.settings import TIME_ZONE


def yn_prompt(prompt: str, default: bool = True) -> bool:
    """Give yes or no prompt to user and get answer"""
    default_str = "y" if default else "n"
    while True:
        yn: str = input(f"{prompt} (Y/n)" if default else f"{prompt} (y/N)")
        if yn == "":
            yn = default_str
        try:
            yn: bool = strtobool(yn)
            break
        except ValueError:
            continue
    return yn


def serialize_response_into_str_dict(ret: Response) -> dict:
    """Serialize response object to dict with string key and string value"""
    json_render = JSONRenderer()
    return {
        "data": json_render.render(ret.data),
        "status": ret.status_code,
        "headers": json_render.render(ret.items()),
        "content_type": ret.content_type if ret.content_type else "application/json"
    }


def daterange(start_date: date, end_date: date):
    """
    return a datetime generator for loop

    NOTICE: returned datetime will discard hour:minute:sec information

    Example:
        daterange(datetime(2018, 11, 11, 20, 20, 20), datetime(2018, 11, 12, 21, 21, 21))
        will return
        datetime(2018, 11, 11, 0, 0, 0)
        datetime(2018, 11, 12, 0, 0, 0)

    You should handle detail of time yourself (ex: append 23:59:59 for date)
    """
    s = timezone.datetime(start_date.year, start_date.month, start_date.day, tzinfo=timezone.get_current_timezone())
    e = timezone.datetime(end_date.year, end_date.month, end_date.day, tzinfo=timezone.get_current_timezone())

    for deltaday in range((e - s).days + 1):
        yield s + timedelta(deltaday)


def date_format_transverter(date, format='%Y-%m-%d %H:%M:%S'):

    """
    date transverter
    Result Setting TIME_ZONE conf

    """
    if date is None:
        return None
    return timezone.localtime(date).strftime(format)


def get_timezone_date(datetime):
    """
    get settings timezone
    """

    default_timezone = timezone.get_current_timezone() if settings.USE_TZ else None
    if default_timezone:
        return datetime.astimezone(default_timezone)
    else:
        return datetime.astimezone(pytz.timezone(TIME_ZONE))


def create_matching_rule(device, is_subsidiary=False):
    if is_subsidiary:
        str_template = f'subsidiary_device_{device.order}'
        matching_rule_template = {
            str_template: {
                "account_resource": {

                }
            }
        }
        # add account info
        account_info = device.device.account.all().values_list('app_name', 'name')
        account_dict = {item[0]: item[1] for item in account_info}
        device_app_name_list = account_dict.keys()
        _ = [
            matching_rule_template[str_template]['account_resource'].update(
                {account.app_name: 'account_alike_true'}   # 僚机和主机同一app账号相同
            )
            if account.app_name in device_app_name_list and account.name == account_dict[account.app_name] else
            matching_rule_template[str_template]['account_resource'].update(
                {account.app_name: 'account_alike_false'}  # 僚机和主机同一app账号不相同
            )
            for account in device.account.all()

        ]
    else:
        str_template = 'device'
        matching_rule_template = {
            str_template: {
                "account_resource": {

                }
            }
        }
        # add account info
        _ = [
            matching_rule_template[str_template]['account_resource'].update(
                {account.app_name: None}  # device 不需要标注是否相同。
            )
            for account in device.account.all()
        ]
    # add sim card info
    sim_card_slot_list = [1, 2]     # 标注sim card插槽位置是否被占用。
    device_all_simcard_obj = device.simcard.all()
    _ = {
        matching_rule_template[str_template].update(
            {
                f"simcard_{sim_card.order}": {
                    "operator": sim_card.operator,
                    "volte": sim_card.is_volte
                }
            }
        ): sim_card_slot_list.remove(sim_card.order)
        for sim_card in device_all_simcard_obj
    }
    _ = [
        matching_rule_template[str_template].update(
            {
                f"simcard_{item}": {
                    "operator": 'nothing',
                }
            }
        )
        for item in sim_card_slot_list
    ]
    return matching_rule_template


def update_device_matching_rule(device_list: list):
    for device in device_list:
        matching_rule = create_matching_rule(device)
        # subsidiary_device
        _ = [
            matching_rule.update(create_matching_rule(subsidiary_device, True))
            for subsidiary_device in device.subsidiarydevice.all()
        ]
        device.matching_rule = matching_rule
        device.save()


class SimilarityMatrixMonitor:

    def __init__(self, *args, **kwargs):
        self.device_queryset = kwargs.get('device_queryset', None)
        self.job_queryset = kwargs.get('job_queryset', None)
        self._useful_feature = {"author": "username", "test_area": "description"}
        self._muti_item_name = "test_area"

        self.job_feature_df = None

    def calculate_matrix(self, rds_queryset):
        # todo modify this function for adding job-lifetime and deltT into matrix

        if not all([isinstance(self.device_queryset, QuerySet), isinstance(self.job_queryset, QuerySet)]):
            return np.zeros(shape=(0, 0)), [], []
        matrix = np.zeros(shape=(self.device_queryset.count(), self.job_queryset.count()))
        device_label_list = list(self.device_queryset.values_list('device_label', flat=True))
        job_label_list = list(self.job_queryset.values_list('job_label', flat=True))
        for rds in rds_queryset:
            if rds.job not in self.job_queryset:  # remove deleted&sysJob
                continue
            job_first_use_time = rds.job.earliest_used_time
            job_last_using_time = rds.job.recently_used_time

            if not all([job_first_use_time, job_last_using_time]):
                continue
            rds_create_time = timezone.datetime.strftime(timezone.localtime(rds.start_time),
                                              settings.REST_FRAMEWORK['DATETIME_FORMAT'])
            matrix[device_label_list.index(rds.device.device_label)][job_label_list.index(rds.job.job_label)]\
                += self.cal_time_weight(job_first_use_time, job_last_using_time,rds_create_time)
        return matrix, device_label_list, job_label_list

    def cal_time_weight(self, job_first_use_time, job_last_using_time, rds_create_time):
        # todo verify this function when back to company
        k = 1  # auto set this k&a when we have feedback data
        a = 4
        job_time_interval = (self.strftTime(job_last_using_time) - self.strftTime(rds_create_time))
        job_life_time = (self.strftTime(job_last_using_time) - self.strftTime(job_first_use_time))
        return k * np.exp(a * (-job_time_interval / (job_life_time + timedelta(seconds=1))))

    def strftTime(self, timeStr):
        return datetime.strptime(timeStr, "%Y-%m-%d %H:%M:%S")

    def form_job_feature_matrix(self):
        """
        :param job_feature_list: job attribute get from reef
        :return: df with index of device_label and columns of all feature in featureNameList
        eg:
                                                                  author                   test_area
            job-1911c35b-fb8d-47fa-9676-f6db02d341d5                  tingting                      [wifi]
            job-4a5977fa-c309-4984-9456-45b5f6b9ad00                  tingting                   [browser]
            job-removePhoneCall                       user-default000000000001                 [machBrain]
            job-a03de750-6739-4e35-8a31-5a60ca01cf8a  user-default000000000001                   [browser]
            job-fa6fe5c1-7bfa-4615-a74d-0a43c100a399                  tingting           [machBrain, wifi]
            job-f20c2da7-2fed-49d8-93a8-1afbf0780f13                  tingting                      [wifi]
            job-e7a0a491-c1ab-4159-a806-c62796d4cd98  user-default000000000001                 [machBrain]

        """
        feature_matrix = []
        job_label_list = []
        for job in self.job_queryset:
            inside_list = []
            for feature, name in self._useful_feature.items():
                job_fields_obj = getattr(job, feature)
                if isinstance(job_fields_obj, Manager):
                    content = [i.strip() for i in job_fields_obj.all().values_list(name, flat=True)]
                else:
                    field = getattr(job_fields_obj, name)
                    content = field.strip() if field is not None and isinstance(field, str) else None
                inside_list.append(content)
            feature_matrix.append(inside_list)
            job_label_list.append(job.job_label)
        self.job_feature_df = pd.DataFrame(feature_matrix, index=job_label_list, columns=self._useful_feature)
        return self.job_feature_df, job_label_list

    def deal_with_multi_item(self, feature_list, job_label_list):
        """
        :param feature_list: 2d-ndarray
        after change:
                                                    author  ...  have_Calendar    have_camera ....
        job-1911c35b-fb8d-47fa-9676-f6db02d341d5   tingting  ...              0           1
        job-4a5977fa-c309-4984-9456-45b5f6b9ad00   tingting  ...              0           0
        """
        # list all feature's name
        all_item_list = list(itertools.chain.from_iterable(feature_list))
        for name in set(all_item_list):
            # set 1 if this line have this feature
            featurValue = [1 if name in i else 0 for i in feature_list]
            self.job_feature_df = pd.concat(
                [self.job_feature_df, pd.DataFrame({"have_" + name: featurValue}, index=job_label_list)],
                join="outer", axis=1)
        self.job_feature_df = self.job_feature_df.drop(self._muti_item_name, axis=1)

    def deal_with_str_item(self, series, colunm_name):
        """
        after change:
                                                    author  ...  have_Calendar    have_camera ....
        job-1911c35b-fb8d-47fa-9676-f6db02d341d5     0  ...              0           1
        job-4a5977fa-c309-4984-9456-45b5f6b9ad00     0  ...              0           0
        """
        series = self.fill_in_blank_with_mode(series)
        if len(set(series.values)) <= 5:
            dummyColumn = pd.get_dummies(series, prefix=colunm_name)
        else:
            dummyColumn = pd.factorize(series)[0]
        self.job_feature_df = pd.concat([self.job_feature_df, dummyColumn], axis=1, join="outer")
        self.job_feature_df = self.job_feature_df.drop(colunm_name, axis=1)

    def fill_in_blank_with_mode(self, series):
        if len(series[series.isnull()].values) > 0:
            series = series.copy()
            series[series.isnull()] = series.dropna().mode().values[0]
        return series

    @staticmethod
    def _deal_with_abnormal_item(df):
        # del value(num) which is bigger than 2*std
        for column, std in df.std().items():
            df = df.drop(df[abs(df[column] - df.mean()[column]) >= 2 * std].index, axis=0)
        return df


class JobBindResource:

    def __init__(self, resource_list: list):
        """
        output data:
        {
            "device": {
                "simcard_1":{
                    "operator__in": ["中国移动"],
                    "volte": true
                },
                "simcard_2":{
                    "operator__in": ["中国移动", "中国联通"]
                },
                "account_resource": {

                }
            },
            "subsidiary_device_1":{
                "simcard_1":{
                    "operator__in": ["中国移动"]
                },
                "simcard_2":{
                    "operator__in": ["中国移动", "中国联通"]
                },
                "account_resource":{
                    "OPPO": "account_alike_true"
                    "小米": "unrestrained"
                }
            }
        }

        """
        self.resource_list = resource_list
        self.device_choices = [
            'device', 'subsidiary_device_1', 'subsidiary_device_2', 'subsidiary_device_3'
        ]
        self.resource_type_name = ['sim_card', 'account_resource']
        self.results = {}

    def analysis_operator(self, operator: str):
        """
        operator choices:
        中国移动
        中国联通
        中国电信
        anything
        not_中国移动
        not_中国联通
        not_中国电信
        nothing
        """
        operator_list = ['中国移动', '中国联通', '中国电信']
        if operator == 'anything':
            return operator_list
        elif operator == 'nothing':
            return ['nothing']
        elif operator.startswith('not_'):
            _, operator_name = operator.split('_')
            if operator_name in operator_list:
                operator_list.remove(operator_name)
                return operator_list
            else:
                raise ValidationError(f'{operator}:{operator_name} is not legal！！')
        elif operator in operator_list:
            return [operator]
        else:
            raise ValidationError(f'{operator} is not legal!!')

    def handle_sim_card(self, res_list):
        """
        structure cim card data
        {
              "operator__in": ["中国移动"],
              "volte": true
        }
        """
        try:
            # 处理operator为nothing时，volte没有值的特例。
            true_or_false = res_list[3].split('_')[1]
        except Exception as e:
            true_or_false = None
        result = {
                'operator__in': self.analysis_operator(res_list[2]),
        }
        if true_or_false is not None:
            if true_or_false == 'true':
                result.update({'volte': True})
            elif true_or_false == 'false':
                result.update({'volte': False})
            else:
                raise ValidationError(f"Volte must is true or false, Can't: {true_or_false}")
        return result

    def handle_account_resource(self, res_list):
        """
        structure account_resource data
        {
            "小米": "unrestrained"
        }
        """
        if res_list[0] != 'device':
            if res_list[3] == 'unrestrained':
                account_alike = ['account_alike_true', 'account_alike_false']
            else:
                account_alike = res_list[3]
        # 主机不需要此属性
        else:
            account_alike = None
        if isinstance(account_alike, list):
            result = {
                f'{res_list[2]}__in': account_alike
            }
        else:
            result = {
                    res_list[2]: account_alike
            }
        return result

    def structure_data(self, res_list):
        resource_type_name = res_list[1]
        device_info = res_list[0]
        """
        拼接 1,2层数据
        {
            device:{
                simcard_1 : {},
                account_resource: {}
            }
        }
        """
        if not self.results.get(device_info, None):
            self.results.update({device_info: {}})
        if not self.results[device_info].get(resource_type_name, None):
            self.results[device_info].update({resource_type_name: {}})

        if resource_type_name.startswith('simcard'):
            dict_data = self.handle_sim_card(res_list)
        elif resource_type_name == 'account_resource':
            dict_data = self.handle_account_resource(res_list)
        else:
            raise ValidationError(f'{resource_type_name} not in {self.resource_type_name}')
        self.results[device_info][resource_type_name].update(dict_data)

    def handle(self):
        """
        input data, 处理前端二维数组为json结构。
        【['一级', '二级', '三级'.......]，
        ['device','simcard_1','中国联通', 'volte_true' ]，
        ['subsidiary_device_1','simcard_2','中国移动', 'volte_false' ]，
        ['device','account_resource','微信]，
        'subsidiary_device_2','account_resource','邮箱', '跟主机相同'
         ...】
        """
        # 二维数据去重,device, account_resource and app_name 重复
        self.resource_list = list(set([tuple(t) for t in self.resource_list]))
        for res_list in self.resource_list:
            # 必须有前两个元素
            if res_list and len(res_list) > 2 and isinstance(res_list, tuple):
                if res_list[0] in self.device_choices:
                    self.structure_data(res_list)
                else:
                    raise ValidationError(f'{res_list} not in {self.device_choices}')
        return self.results


class OpenAPIAnonRateThrottle(AnonRateThrottle):

    def __init__(self):
        self.rate = '60/minute'
        super().__init__()


class ReefLogger:

    def __init__(self, loggers):
        self.logger = logging.getLogger(loggers)

    def debug(self, log_content):
        self.logger.debug(log_content)

    def error(self, log_content):
        self.logger.error(log_content)


def join_path(firs_path: str, second_path: str) -> str:

    if firs_path.endswith('/'):
        if not second_path.startswith('/'):
            return firs_path + second_path
        else:
            second_path = second_path.replace('/', '', 1)
            return firs_path + second_path
    else:
        if not second_path.startswith('/'):
            return os.path.join(firs_path, second_path)
        else:
            return firs_path + second_path
