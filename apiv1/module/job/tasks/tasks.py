import logging
import os
import random
import shutil
import string
import time

from celery import shared_task
from celery._state import get_current_task
from celery.app.task import Task

from apiv1.module.job.models import Job
from apiv1.module.job.serializer import JobResFileExportSerializer
from reef.celery import register_task_logger
from reef.settings import JOB_RES_FILE_EXPORT_PATH, MEDIA_ROOT


class PackZipTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        super(PackZipTask, self).on_failure(exc, task_id, args, kwargs, einfo)

        task = get_current_task()
        logger = logging.getLogger('backend')
        logger.error(
            f'\n'
            f'update_job_res_file error:\n'
            f'task_nmae: {task.name}\n'
            f'task_id: {task_id}\n'
            f'except:{exc}\n'
            f'func args: {args}\n'
            f'func kwargs: {kwargs}\n'
            f'einfo: {einfo}\n'
        )


@register_task_logger(__name__)
@shared_task(bind=True, default_retry_delay=3, base=PackZipTask)
def update_job_res_file(self, job_ids: list, is_job_import=False):
    try:
        # 解决循环导入
        from apiv1.module.job.view import zip_file
        # job 导入使用事物
        jobs = Job.objects.filter(id__in=job_ids)
        if jobs.count() != len(job_ids):
            # retry 3次，sleep时间不好控制。retry 3次后数据库job还没有保存成功，判定为导入失败，需要再次导入解决此问题。
            self.retry(exc=f'Import job list: {job_ids}, Query job list: {list(jobs)}')
        job_attrs = JobResFileExportSerializer(jobs, many=True).data

        for job_attr in job_attrs:
            job_path = os.path.join(JOB_RES_FILE_EXPORT_PATH, job_attr['job_label'] + _random_str())
            # 每个job生成一个目录
            os.makedirs(job_path)

            # job_flow
            for job_flow in job_attr['job_flow']:
                job_flow_path = os.path.join(job_path, str(job_flow['id']))
                # 每个flow按id生成一个目录
                os.makedirs(job_flow_path)

                # ui_json_file 文件全路径
                ui_json_file_path = os.path.join(MEDIA_ROOT, 'ui_json_file', job_flow['ui_json_file'].split('/')[-1])
                try:
                    # 将ui_json_file 文件复制为ji。json文件
                    shutil.copy(ui_json_file_path, os.path.join(job_flow_path, 'ui.json'))
                except Exception as e:
                    raise FileNotFoundError(f'pack zip file error:{e}')

                # job_res_file
                job_res_files = job_flow.pop('job_res_file')
                for job_res_file in job_res_files:
                    try:
                        # 将job_resource_file目录下文件copy到 临时job_flow 目录下
                        res_file_path = os.path.join(MEDIA_ROOT, 'job_resource_file', job_res_file["file"].split("/")[-1])
                        shutil.copy(res_file_path, os.path.join(job_flow_path, job_res_file['name']))
                    except Exception as e:
                        raise FileNotFoundError(
                            f'pack zip file error{e}\n'
                            f'res_file: {job_res_file["file"].split("/")[-1]}\n'
                            f'job_flow_path : {os.path.join(job_flow_path, job_res_file["name"])}'
                        )
            # 拼接打包.zip 文件路径
            job_res_zip_path = os.path.join(JOB_RES_FILE_EXPORT_PATH, job_attr['job_label'] + '.zip')

            # 如果job_res_zip_path存在删除再更新
            if os.path.exists(job_res_zip_path):
                os.remove(job_res_zip_path)

            zip_file(job_res_zip_path, job_path)
            shutil.rmtree(job_path)

            # job_import导入的draft默认True，更新完成将job置为可用
            if is_job_import:
                Job.objects.filter(job_label=job_attr['job_label']).update(job_deleted=False)
    except Exception as e:
        raise Exception(f'pack zip file error{e}')
    return 'success'


def _random_str():
    ran_str = ''.join(random.sample(string.ascii_letters + string.digits, 8))
    return ran_str
