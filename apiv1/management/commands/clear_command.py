import sys, time, os
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from apiv1.module.job.models import JobResourceFile
from reef.settings import MEDIA_ROOT

media_path = Path(MEDIA_ROOT)


class Command(BaseCommand):

    def handle(self, *args, **options):
        file_name_list = [i.split('/')[1] for i in JobResourceFile.objects.all().values_list('file', flat=True)]
        job_resource_file_path = media_path / 'job_resource_file'
        if job_resource_file_path.exists() and job_resource_file_path.is_dir() and os.listdir(os.fspath(job_resource_file_path)):
            count = len(list(job_resource_file_path.iterdir()))
            process = ShowProcess(count)
            self.stdout.write(self.style.SUCCESS(f'Database num:{len(file_name_list)}'))
            self.stdout.write(self.style.SUCCESS(f'Dir file num:{count}'))
            for child in job_resource_file_path.iterdir():
                process.show_process()
                if child.is_file and child.name not in file_name_list:
                    # self.stdout.write(self.style.SUCCESS(f'{child.name}'))
                    child.unlink()
                    # time.sleep(0.05)
            process.close()
        else:
            raise CommandError(f'提示：{job_resource_file_path} path not exist or not dir and dir is empty')


class ShowProcess():
    """
    显示处理进度的类
    调用该类相关函数即可实现处理进度的显示
    """
    i = 0  # 当前的处理进度
    max_steps = 0  # 总共需要处理的次数
    max_arrow = 50  # 进度条的长度

    # 初始化函数，需要知道总共的处理次数
    def __init__(self, max_steps):
        self.max_steps = max_steps
        self.i = 0

    # 显示函数，根据当前的处理进度i显示进度
    # 效果为[>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>]100.00%
    def show_process(self, i=None):
        if i is not None:
            self.i = i
        else:
            self.i += 1

        num_arrow = int(self.i * self.max_arrow / self.max_steps)  # 计算显示多少个'>'
        num_line = self.max_arrow - num_arrow  # 计算显示多少个'-'
        percent = self.i * 100.0 / self.max_steps  # 计算完成进度，格式为xx.xx%
        process_bar = '[' + '>' * num_arrow + '-' * num_line + ']' \
                      + '%.2f' % percent + '%' + '\r'  # 带输出的字符串，'\r'表示不换行回到最左边
        sys.stdout.write(process_bar)  # 这两句打印字符到终端
        sys.stdout.flush()

    def close(self, words='done'):
        print('')
        print(words)
        self.i = 0





