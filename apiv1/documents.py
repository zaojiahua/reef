from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from apiv1.module.rds.models import RdsLog


# @registry.register_document
class RdsLogDocument(Document):
    rds = fields.ObjectField(properties={
        'start_time': fields.DateField(),
        'device_id': fields.IntegerField(),
        'job_id': fields.IntegerField(),
    })
    file_content = fields.TextField(attr='log_content')

    class Index:
        # Name of the Elasticsearch index
        name = 'rds_logs'
        # See Elasticsearch Indices API reference for available settings
        settings = {
            "highlight.max_analyzed_offset": 60000000,
            'number_of_shards': 3,
            'number_of_replicas': 1
        }

    class Django:
        model = RdsLog  # The model associated with this Document

        # The fields of the model you want to be indexed in Elasticsearch
        fields = [
            'file_name',
            'log_file'
        ]
