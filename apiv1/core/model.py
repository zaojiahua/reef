import re

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.translation import ugettext_lazy as _
from rest_framework.relations import RelatedField


class AbsBase(models.Model):

    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    update_time = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    class Meta:
        abstract = True


class AbsDescribe(AbsBase):

    describe = models.CharField(max_length=100, blank=True, null=True, verbose_name='描述')

    class Meta:
        abstract = True


class CustomPatternCharField(RelatedField):

    default_error_messages = {
        'invalid': _('Invalid value. Str format: 10,20'),
        'required': _('This field is required.'),
        'does_not_exist': _('Invalid pk "{pk_value}" - object does not exist.'),
    }

    def __init__(self, **kwargs):
        super(CustomPatternCharField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        pattern = "^([0-9]+,)*[0-9]+$"
        if isinstance(data, str) and re.match(pattern, data):
            id_list = []
            for item in data.split(','):
                try:
                    obj = self.get_queryset().get(id=item)
                    id_list.append(obj.id)
                except ObjectDoesNotExist:
                    self.fail('does_not_exist', pk_value=item)
            return self.get_queryset().filter(id__in=id_list)
        else:
            self.fail('invalid')

    def to_representation(self, obj):
        return str(getattr(obj, 'id'))


from django.db.models import Func, Value


class Convert(Func):
    def __init__(self, expression, transcoding_name, **extra):
     super(Convert, self).__init__(
      expression=expression, transcoding_name=transcoding_name, **extra)

    def as_mysql(self, compiler, connection):
     self.function = 'convert_to'
     self.template = ' %(function)s(%(expression)s,%(transcoding_name)s)'
     # self.template = f'{self.function}({self.expression},{self.transcoding_name})'
     return super(Convert, self).as_sql(compiler, connection)

