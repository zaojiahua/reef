import logging
import os
from os import path

from PIL import Image

from reef.settings import MEDIA_ROOT, JOB_RES_FILE_EXPORT_PATH

JOB_ASSETS = f"{MEDIA_ROOT}{os.sep}job_assets{os.sep}"
if not path.exists(JOB_ASSETS):
    os.mkdir(JOB_ASSETS)

num = 10


def create_image_job_assets(level):
    # ========================
    # Make images job assets
    # ========================

    # Args Start---
    base_size = (480, 800)
    # Args End---

    file_name = f"{JOB_ASSETS}stress{level}.png"
    if path.exists(file_name):
        return
    img = Image.new('RGB', ((base_size[0] * level), (base_size[1] * level)), color='red')
    img.save(file_name)


def create_text_job_assets(level):
    # ========================
    # Make text job assets
    # ========================

    # Args Start---
    step = 2
    base_size = 1 * 1024 * 1024  # 1MB
    batch_size = 100 * 1024  # 100KB
    # Args End---

    times = base_size // batch_size
    txtbatch = "A" * batch_size  #
    file_name = f"{JOB_ASSETS}stress{level}.txt"
    if path.exists(file_name):
        return
    with open(file_name, 'w') as f:
        for _ in range(times * level * step):
            f.write(txtbatch)


def create_zip_job_assets(level):
    # ========================
    # Make zip job assets
    # ========================

    # Args Start---
    step = 2
    base_size = 10 * 1024 * 1024  # 10MB
    batch_size = 100 * 1024  # 100KB
    # Args End---

    times = base_size // batch_size
    txtbatch = "A" * batch_size  #
    file_name = f"{JOB_ASSETS}stress{level}.zip"
    if path.exists(file_name):
        return
    with open(file_name, 'w') as f:
        for _ in range(times * level * step):
            f.write(txtbatch)


def create_job_res_file_export_zip():
    job_ids = Job.objects.filter(job_deleted=False).exclude(ui_json_file='').values_list('id', flat=True)
    update_job_res_file(job_ids)
    return


# noinspection PyBroadException
if __name__ == "__main__":
    try:
        for i in range(1, num + 1):
            create_image_job_assets(i)
            create_text_job_assets(i)
            create_zip_job_assets(i)
    except Exception as e:
        logging.error(f"生成job assets的过程中发生错误， 已跳过资源生成的步鄹\n{e}")

    # 生成job_res_file资源包
    import django
    from django.conf import settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reef.settings')
    settings._setup()
    django.setup()

    from apiv1.module.job.models import Job
    from apiv1.module.job.tasks.tasks import update_job_res_file

    if not os.listdir(JOB_RES_FILE_EXPORT_PATH):
        create_job_res_file_export_zip()
