from django.contrib import admin

from apiv1.module.bug.models import Bug
from apiv1.module.job.models import Job
from apiv1.module.system.models import Cabinet
from reef.settings import DEBUG

search_fields = ("job", "device", "reporter")
class BugAdmin(admin.ModelAdmin):
    list_display = ("reporter", "cabinet", "device", "job", "status")
    fieldsets_all = ("reporter", "cabinet", "device", "job", "description", "happened_time", "status", "level")
    fieldsets_part = ("reporter", "cabinet", "device", "job", "description", "happened_time", "level")
    ordering = ("status", "-happened_time",)
    autocomplete_fields = ["job"]

    def get_fields(self, request, obj=None):
        field_set = self.fieldsets_all if request.user.is_superuser else self.fieldsets_part
        return field_set

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "cabinet":
            kwargs["queryset"] = Cabinet.objects.filter(is_delete=False)
        elif db_field.name == "job":
            kwargs["queryset"] = Job.objects.filter(job_deleted=False)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


if DEBUG:
    admin.site.register(Bug, BugAdmin)
    admin.site.site_header = "Bug上报系统"
