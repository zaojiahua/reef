import json
import os.path
import pathlib
from collections import OrderedDict

import numpy as np
import pandas as pd
from openpyxl.styles import Alignment

from apiv1.core.constants import COOLPAD_UPLOAD_TBOARD_DATA, COOLPAD_GET_CRUMB, REDIS_COOLPAD_POWER_LAST_TIME
from apiv1.core.request import ReefRequest
from apiv1.core.utils import ReefLogger
from apiv1.module.abnormity.models import Abnormity
from apiv1.module.job.models import JobParameter
from apiv1.module.rds.models import Rds, RdsLog
from apiv1.module.tboard.models import TBoardStatisticsResult
from reef.settings import redis_pool_connect, MEDIA_ROOT, REEF_SERVER_IP, RESOURCE_EXCEL_FILE_EXPORT


class CoolPadObj:

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_singleton"):
            setattr(CoolPadObj, "_singleton", super().__new__(cls))
        return cls._singleton

    def __init__(self):
        self.statistics_data = []
        self.upload_data = {}

    def handle_tboard_data(self, tboard):
        device_list = tboard.device.all()
        job_count = tboard.job.all().count()
        file_path = ''
        job_parameter_obj = JobParameter.objects.filter(tboard=tboard).order_by('create_time').first()
        if job_parameter_obj:
            parameter_fields = job_parameter_obj.parameter
            file_path = parameter_fields.get('file_path', '')
        self.upload_data = {'file_path': file_path, 'phones': []}
        for index, device in enumerate(device_list):
            crash = Abnormity.objects.filter(device=device, tboard=tboard, abnormity_type__title='Crash').count()
            anr = Abnormity.objects.filter(device=device, tboard=tboard, abnormity_type__title='ANR').count()
            rds_queryset = Rds.objects.filter(tboard=tboard, device=device).order_by('create_time')
            rds_count = rds_queryset.count()
            if rds_count == job_count:
                status = 'success'
            else:
                status = 'fail'
            # uft
            performance_file_name = f"performance_result_{device.device_label.split('---')[-1]}.txt"
            rds_log = RdsLog.objects.filter(rds__tboard=tboard, file_name__contains=performance_file_name).first()
            if rds_log:
                performance_result_file_path = os.path.join(MEDIA_ROOT, rds_log.log_file.path)
                if pathlib.Path(performance_result_file_path).is_file():
                    with open(performance_result_file_path, 'r') as f:
                        uft_list = f.read().strip('\n').split('\n')
                    uft = 0
                    for uft_val in uft_list:
                        uft_val = uft_val.strip()
                        if not uft_val:
                            # 空值跳过
                            continue
                        if isinstance(uft_val, str) and uft_val.isdigit():
                            uft += int(uft_val)
                        else:
                            uft = -1
                            break
                else:
                    uft = -1
            else:
                uft = -1

            redis_key = f"{REDIS_COOLPAD_POWER_LAST_TIME}:{tboard.id}:{device.device_label}"
            # seconds 值小于0为无效数据
            seconds: bytes = redis_pool_connect.hmget(redis_key, 'power_last_time')[0]
            if not seconds or not seconds.isdigit():
                seconds = -1
            else:
                seconds: int = int(seconds)
                if seconds < 0:
                    seconds = -1
            device_ret = {
                'FC': crash,
                'ANR': anr,
                'UFT': uft,
                'status': status,
                'number': index + 1,
                'power_last_time': seconds
            }
            self.upload_data['phones'].append(device_ret)

            # get excel table data
            if redis_pool_connect.exists(redis_key):
                redis_data = redis_pool_connect.hmget(redis_key, ['task_run_time', 'standby_time'])
                task_run_time, standby_time = redis_data[0], redis_data[1]
            else:
                task_run_time, standby_time = None, None
            rom_version_file = f"new_version_{device.device_label.split('---')[-1]}"
            rom_version_rds_log = RdsLog.objects.filter(
                rds__tboard=tboard, file_name__contains=rom_version_file
            ).first()
            if not rom_version_rds_log:
                rom_version_val = ''
            else:
                rom_version_file_path = os.path.join(MEDIA_ROOT, rom_version_rds_log.log_file.path)
                p = pathlib.Path(rom_version_file_path)
                if p.is_file():
                    with open(p, 'r') as f:
                        rom_version_val = f.read().strip('\n')
                else:
                    rom_version_val = ''

            bugreport_list = RdsLog.objects.filter(
                rds__tboard=tboard, file_name__contains='bugreport', rds__device=device
            ).values_list('log_file', flat=True)
            bugreport_url_dict = {}
            for index, bugreport_file_path in enumerate(bugreport_list):
                bugreport_ulr = f"http://{REEF_SERVER_IP}:8000/media/{bugreport_file_path}"
                bugreport_url_dict[f'日志{index + 1}'] = '=HYPERLINK("%s", "%s")' % (bugreport_ulr, bugreport_ulr)

            device_dict_info = {
                '设备名称': device.device_name,
                '续航时间': seconds,
                '前台任务时间': -1 if task_run_time is None else int(task_run_time),
                '待机时间': -1 if standby_time is None else int(standby_time),
                'FC': crash,
                'ANR': anr,
                'UFT': uft,
                'RomVersion': rom_version_val,
                '刷机路径': file_path,
            }
            device_dict_info.update(bugreport_url_dict)
            self.statistics_data.append(device_dict_info)

        self.crete_statistics_xlsx(tboard)

    def end_tboard_upload_data(self, tboard):
        crumb, crumb_request_field = self.get_crumb_value()
        if (crumb or crumb_request_field) is None:
            logger = ReefLogger('backend')
            logger.error(f'get crumb val fail: \n'
                         f'crumb, crumb_request_field: {crumb, crumb} \n'
                         f'tboard id: {tboard.id}')
            return
        url = COOLPAD_UPLOAD_TBOARD_DATA
        headers = {crumb_request_field: crumb}
        req = ReefRequest(url, **{'data': {"Message": json.dumps(self.upload_data)}, 'headers': headers})
        res = req.post({'url': COOLPAD_UPLOAD_TBOARD_DATA, 'headers': headers})
        reef_logger = ReefLogger('debug')
        reef_logger.debug(f'coolpad data upload success \n'
                          f'crumb, crumb_request_field: {crumb, crumb} \n'
                          f'tboard id: {tboard.id} \n'
                          f'upload data: {self.upload_data} \n'
                          f'res code: {getattr(res, "status_code", None)}')

    def get_crumb_value(self):
        url = COOLPAD_GET_CRUMB
        crumb = None
        crumb_request_field = None
        reef_request = ReefRequest(url, **{'timeout': 3})
        res = reef_request.get({'url': COOLPAD_GET_CRUMB})
        try:
            crumb = res.json().get('crumb', None)
            crumb_request_field = res.json().get('crumbRequestField', None)
        except Exception as e:
            logger = ReefLogger('backend')
            if res is None:
                logger.error(f'get CoolPad crumb parameter fail: res is None\n'
                             f'e:{e}'
                             )
            else:
                logger.error(f'get CoolPad crumb parameter fail: \n'
                             f'response text: {res.text} \n'
                             f'response status_code: {res.status_code} \n'
                             f'e:{e}'
                             )
        return crumb, crumb_request_field

    def crete_statistics_xlsx(self, tboard):
        df = pd.DataFrame(self.statistics_data)
        computer_columns = ['续航时间', '前台任务时间', '待机时间', 'FC', 'ANR', 'UFT']
        # 无效数据处理
        df = df.replace(-1, np.NaN)
        mean_dict = OrderedDict({'设备名称': '平均值'})
        for columns in computer_columns:
            if columns in ['FC', 'ANR', 'UFT']:
                mean_data = df[columns].mean()
                mean_dict[columns] = mean_data if pd.isnull(mean_data) else int(mean_data)
            else:
                mean_data = df[columns].mean()
                if pd.isnull(mean_data):
                    mean_dict[columns] = mean_data
                else:
                    mean_data = int(mean_data)
                    mean_dict[columns] = f"{mean_data // 60 // 60}h{mean_data // 60 % 60}min{mean_data % 60}s"
                for index, data in enumerate(df[columns]):
                    if not pd.isnull(data) and data:
                        data = int(data)
                        second = data % 60
                        minute = data // 60 % 60
                        hours = data // 60 // 60
                        df.loc[index, columns] = f"{hours}h{minute}min{second}s"

        df = df.append(mean_dict, ignore_index=True)
        # NaN 转为空值
        df.fillna('', inplace=True)
        xlsx_file_path = os.path.join(RESOURCE_EXCEL_FILE_EXPORT, f'{tboard.board_name}_{tboard.id}.xlsx')
        excel_file_path = os.path.join(MEDIA_ROOT, xlsx_file_path)
        with pd.ExcelWriter(excel_file_path) as writer:
            df.to_excel(writer, index=False)
            worksheet = writer.sheets['Sheet1']
            for index in range(1, worksheet.max_row + 1):
                row = worksheet.row_dimensions[index]
                # 数据居中
                row.alignment = Alignment(horizontal='center', vertical='center')
            # for cell in worksheet['J']:
            #
            #     cell.alignment = Alignment(horizontal='center', wrapText=True)
        TBoardStatisticsResult.objects.create(tboard=tboard, file_path=xlsx_file_path)

