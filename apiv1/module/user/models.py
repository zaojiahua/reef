import time

from django.contrib.auth.models import AbstractUser
from django.db.models import Sum
from django.utils.functional import cached_property

from apiv1.module.job.models import Job


class ReefUser(AbstractUser):
    """
    This is user model, no thing.
    """

    @property
    def job_amount(self):
        return Job.objects.filter(author=self.id, job_deleted=False).count()

    @property
    def job_contribution(self):
        contribution_dict = Job.objects.filter(author=self.id, job_deleted=False).aggregate(
            sum_contribution=Sum("complexity"))
        return contribution_dict.get("sum_contribution", 0) if contribution_dict.get("sum_contribution") is not None else 0

    class Meta:
        verbose_name_plural = "系统用户"
