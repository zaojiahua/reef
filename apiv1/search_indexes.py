# encoding: utf-8
from haystack import indexes

from apiv1.module.rds.models import RdsLog


class RdsLogIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    start_time = indexes.DateTimeField(model_attr='rds__start_time')
    device_id = indexes.IntegerField(model_attr='rds__device_id')
    job_id = indexes.IntegerField(model_attr='rds__job_id')

    def get_model(self):
        return RdsLog

    def index_queryset(self, using=None):
        return self.get_model().objects.all()
