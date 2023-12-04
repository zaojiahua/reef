import collections

from django.core.files.base import ContentFile
from django.core.management import BaseCommand, CommandParser
from django.db import transaction
from django.utils import timezone

from apiv1.module.job.models import Job, JobResourceFile
from apiv1.module.job.models import JobFlow

from apiv1.module.job.tasks.tasks import update_job_res_file


class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser):
        pass

    @transaction.atomic
    def handle(self, *args, **options):
        all_job = Job.objects.all()
        abnormal_job = collections.defaultdict(list)
        inner_job_dict = {}

        for job in all_job:
            instance = JobFlow.objects.create(
                name="UI_JSON_FILE",
                flow_type='NormalFlow',
                job=job,
                order=0,
                description='transfer'
            )

            if job.job_type == 'InnerJob':
                instance.flow_type = 'InnerFlow'
                instance.save()

            try:
                instance.ui_json_file.save("ui.json", ContentFile(job.ui_json_file.read()))
                job.updated_time = timezone.now()
                job.save()
            except Exception:
                abnormal_job['uijson'].append(job.id)

            inner_job_dict[job] = job.inner_job.all()

        for job, inner_jobs in inner_job_dict.items():
            if inner_jobs:
                flow_list = [i.job_flow.all()[0] for i in inner_jobs]
                job.job_flow.all()[0].inner_flow.add(*flow_list)

        job_res_files = JobResourceFile.objects.all()
        for job_res_file in job_res_files:
            try:
                job_res_file.job_flow = job_res_file.job.job_flow.all()[0]
                job_res_file.save()
            except Exception :
                abnormal_job['resfile'].append(job_res_file.id)

        job_ids = Job.objects.filter(job_deleted=False).exclude(ui_json_file='').values_list('id', flat=True)
        update_job_res_file(job_ids)

        print(abnormal_job)
        return
