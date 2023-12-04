from django.db import models


class JobFlowQuerySet(models.QuerySet):

    def create(self, **kwargs):
        obj = self.model(**kwargs)
        self._for_write = True
        obj.save(force_insert=True, using=self.db, update_time_fields=False)
        return obj


class JobFlowManager(models.Manager):

    def get_queryset(self):
        return JobFlowQuerySet(self.model)