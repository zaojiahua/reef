from django.dispatch import receiver, Signal

from apiv1.core.response import reef_400_response
from apiv1.module.job.tasks.tasks import update_job_res_file

# 自定义job_res_file导出更新信号
job_res_file_export = Signal(providing_args=['job'])


@receiver(job_res_file_export)
def job_res_file_handle(sender, **kwargs):
    """
    在media下会维护一个job资源文件的文件夹(job_res_file_export)，提供coral文件资源下载
                                |---job_label1.zip
    /media/job_res_file_export  |---job_label2.zip
                                |---job_label3.zip

    资源文件会在下发任务的接口，传入给coral，coral端也会缓存job的资源包，coral根据job的update_time
    判断是否需要下拉更新coral端资源包

    1、服务起来之前会判断job_res_file_export文件夹下是否有文件，如果没有则在uwsgi.ini的hook-pre-app的配置关联的
       preapp文件下做一次所有job_res_file 资源包下载
    2、请求cedar/job_upload_multi_res_file/ api 触发此信号异步更新, 创建或更新对应的job zip
    3、请求cedar/job_import/ 触发此信号异步更新，创建或更新对应的job zip
    4、jobflow 通用API update、create 触发此信号异步更新，ui_json_file字段更新需要创建或更新对应的job zip
    5、jobflow copy 及 job copy 触发此信号异步更新
    """
    jobs = list(kwargs['job'])
    is_job_import = kwargs.get('is_job_import', False)
    num = 20  # job分成20个一组创建一个异步任务
    for i in range(0, len(jobs), num):
        if is_job_import:
            update_job_res_file.delay(jobs[i:i + num], is_job_import)
        else:
            try:
                update_job_res_file(jobs[i:i + num])
            except Exception as e:
                reef_400_response(message=e, description='用例保存异常，请联系管理员解决！！！')
    return


