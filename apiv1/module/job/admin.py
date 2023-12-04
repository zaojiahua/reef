from django.contrib import admin

from apiv1.module.job.models import Job
from reef.settings import DEBUG


class JobAdmin(admin.ModelAdmin):
    search_fields = ("job_name",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


if DEBUG:
    admin.site.register(Job, JobAdmin)
