import copy
import re
from collections import namedtuple

import time
from django.contrib.auth.models import Group
from django.db.models import Func, Value
from django.core.exceptions import FieldError, FieldDoesNotExist
from django.db.models import Model
from django.db.models.fields.related_descriptors import ReverseManyToOneDescriptor, ReverseOneToOneDescriptor
from rest_framework import status, mixins
from rest_framework import generics, serializers
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, ListSerializer
from rest_framework.viewsets import GenericViewSet as RestFrameworkGenericViewSet
from rest_framework.relations import (  # NOQA # isort:skip
    HyperlinkedIdentityField, HyperlinkedRelatedField, ManyRelatedField,
    PrimaryKeyRelatedField, RelatedField, SlugRelatedField, StringRelatedField,
)
from rest_framework.utils import html
from rest_framework.fields import empty

from apiv1.module.job.models import TestProject
from reef import settings
from apiv1.core.response import reef_400_response


#########################################################
# helper class and function                             #
#########################################################

def _get_model_fields(model: Model):
    model_properties = []
    for attr in dir(model):
        attr_obj = getattr(model, attr)
        if isinstance(attr_obj, property):
            model_properties.append(attr)
        elif isinstance(attr_obj, ReverseManyToOneDescriptor):
            if attr.endswith('_set'):
                # TODO 该判断式为User及LogEntry的反响关系名称查找不到问题的临时解决方案 By Raymond
                if attr.startswith('logentry'):
                    continue
                # TODO 该判断为针对Group 读取filed错误的暴力解决方案，需优化 By Raymond
                elif attr == 'user_set' and model is Group:
                    continue
                elif attr == 'testgathership_set' and model is TestProject:
                    continue
                # End
                model_properties.append(attr[:-4])
            else:
                model_properties.append(attr)
        elif isinstance(attr_obj, ReverseOneToOneDescriptor):
            model_properties.append(attr)

    return tuple(
        sorted(
            [field.name for field in model._meta.fields] + model_properties
        )
    )


class HelperModelSerializer(ModelSerializer):
    def __init__(self, *args, **kwargs):
        assert 'model' in kwargs, 'Need argument model'
        assert 'depth' in kwargs, 'Need argument depth'
        assert 'wanted_fields' in kwargs, 'Need argument wanted_fields'
        _model = kwargs.pop('model')
        self.Meta = type('Meta', (), {
            'depth': kwargs.pop('depth'),
            'model': _model,
            'fields': _get_model_fields(_model)
        })

        wanted_fields = kwargs.pop('wanted_fields', None)
        exclude_fields = kwargs.pop('exclude_fields', None)
        super(HelperModelSerializer, self).__init__(*args, **kwargs)
        if wanted_fields is None and exclude_fields is None:
            exclude_fields_list = (HyperlinkedIdentityField, HyperlinkedRelatedField, ManyRelatedField,
                                    PrimaryKeyRelatedField, RelatedField, SlugRelatedField, StringRelatedField)
            for field_name in list(self.fields.values()):
                if isinstance(field_name, exclude_fields_list):
                    self.fields.fields.pop(field_name.field_name)
            return
        if exclude_fields is not None:
            for field in exclude_fields:
                if field in self.fields:
                    self.fields.pop(field)
            return
        list_wanted_fields = [field.split('.') for field in wanted_fields]
        for row in list_wanted_fields:
            f = self.fields
            for item in row:
                if isinstance(f, ModelSerializer):
                    setattr(f, 'wanted', True)
                    f = f.fields.get(item)
                elif isinstance(f, ListSerializer):
                    setattr(f, 'wanted', True)
                    f = f.child.fields.get(item)
                else:
                    f = f.get(item)
                if f is None:
                    raise ValidationError("Cannot find field: '{}'".format('.'.join(row)))
            setattr(f, 'wanted', True)

        Field = namedtuple('Field', 'instance path')
        queue = [Field(instance=field, path=[]) for field in self.fields.values()]

        # Travel fields tree, delete field without 'wanted' mark
        while queue:
            field = queue.pop(0)
            name = field.instance.field_name
            wanted = getattr(field.instance, 'wanted', False)

            if not wanted:
                # del field
                del_field_parent = self.fields
                for f in field.path:
                    del_field_parent = del_field_parent.get(f).child.fields if isinstance(del_field_parent.get(f),
                                                                                          ListSerializer) else del_field_parent.get(
                        f).fields
                del_field_parent.pop(name)
                continue

            if isinstance(field.instance, ModelSerializer):
                childs = field.instance.fields
                path = field.path + [str(field.instance.field_name)]
                queue.extend([Field(instance=child, path=path) for child in childs.values()])
            elif isinstance(field.instance, ListSerializer):
                childs = field.instance.child.fields
                path = field.path + [str(field.instance.field_name)]
                queue.extend([Field(instance=child, path=path) for child in childs.values()])


class ListModelMixin:
    def _check_mixin_class(self):
        assert hasattr(self, 'get_queryset'), \
            "Cannot get function 'get_queryset', does mixins use with GenericAPIView?"

        assert getattr(self, 'return_key', None) is not None, (
                "'%s' should include a `return_key` attribute "
                % self.__class__.__name__
        )
        assert getattr(self, 'queryset_filter', None) is not None, (
                "'%s' should include a `queryset_filter` attribute "
                % self.__class__.__name__
        )

    def _get_depth(self, wanted_fields):
        default_depth = settings.GENERIC_VIEW_DEPTH
        depth = max([item.count('.') for item in wanted_fields]) + 1 if wanted_fields is not None else default_depth
        return depth

    def _prepare_params(self, query_params):
        reeflist_re_pattern = re.compile(r'^ReefList\[.*\]$')
        for k, v in query_params.items():
            if re.match(reeflist_re_pattern, v) is not None:
                query_params[k] = v[9:-1].split('{%,%}')
            elif v == 'True':
                query_params[k] = True
            elif v == 'False':
                query_params[k] = False
        return query_params

    def _filter_out_queryset(self, queryset, query_params, queryset_filter, queryset_filter_vals):
        try:
            queryset = queryset.filter(**query_params)
        except FieldError as e:
            raise ValidationError(
                {"field_error": f"query filtering error for input: {query_params} \nError detail: {e}"},
                code=status.HTTP_400_BAD_REQUEST)

        for k, func in queryset_filter.items():
            if k not in queryset_filter_vals:
                continue
            queryset = func(queryset, queryset_filter_vals[k])

        return queryset.distinct()

    def list(self, request):
        self._check_mixin_class()
        return_key = getattr(self, 'return_key')
        queryset_filter = getattr(self, 'queryset_filter')
        queryset = getattr(self, 'get_queryset')()
        model = queryset.model

        query_params: dict = request.query_params.dict()

        query_params.pop('limit', None)
        query_params.pop('offset', None)
        query_params.pop('ordering', None)

        wanted_fields = query_params['fields'].split(',') if 'fields' in query_params else None
        exclude_fields = query_params['exclude'].split(',')if 'exclude' in query_params else None
        query_params.pop('fields', None)
        query_params.pop('exclude', None)

        queryset_filter_vals = {key: query_params.pop(key).split(',') for key in queryset_filter if key in query_params}

        query_params = self._prepare_params(query_params)

        queryset = self._filter_out_queryset(queryset, query_params, queryset_filter, queryset_filter_vals)

        depth = self._get_depth(wanted_fields)

        count = queryset.count()
        if 'ordering' in request.query_params.dict():
            filter_ordering = OrderingFilter()
            queryset = filter_ordering.filter_queryset(request, queryset, self)

        if 'limit' in request.query_params.dict() or 'offset' in request.query_params.dict():
            pagination = LimitOffsetPagination()
            queryset = pagination.paginate_queryset(queryset, request, view=None)
        try:
            serializer = HelperModelSerializer(
                queryset, many=True, wanted_fields=wanted_fields, model=model, depth=depth,exclude_fields=exclude_fields)
        except FieldDoesNotExist as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({return_key: serializer.data}, headers={"Total-Count": count})


class RetrieveModelMixin:
    def retrieve(self, request, pk):
        wanted_fields = None
        if 'fields' in request.query_params:
            wanted_fields = request.query_params['fields'].split(',')
        queryset = getattr(self, 'get_queryset')()
        model = queryset.model
        instance = getattr(self, 'get_object')()
        default_depth = settings.GENERIC_VIEW_DEPTH
        depth = max([item.count('.') for item in wanted_fields]) + 1 if wanted_fields is not None else default_depth
        serializer = HelperModelSerializer(instance, wanted_fields=wanted_fields, model=model, depth=depth)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BulkCreateModelMixin:
    def bulk_create(self, request):
        serializer = getattr(self, 'get_serializer')(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_bulk_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_bulk_create(self, serializer):
        serializer.save()


############################################################################
# 通用型API接口，包含create, update, partial_update, list, retrieve, delete #
############################################################################

class GenericViewSet(mixins.CreateModelMixin,
                     BulkCreateModelMixin,
                     RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     ListModelMixin,
                     RestFrameworkGenericViewSet):
    queryset = None
    return_key = None
    queryset_filter = None

    def __init__(self, *args, **kwargs):
        super(GenericViewSet, self).__init__(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        bulk = isinstance(request.data, list)
        handler = self.bulk_create if bulk else super(GenericViewSet, self).create
        return handler(request, *args, **kwargs)


class AutoExecuteSerializerGenericAPIView(generics.GenericAPIView):

    def execute(self, request, action='post'):
        if action == 'post':
            serializer = self.get_serializer(data=request.data)
        else:
            serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return serializer


class CustomStrField(serializers.ListField):

    def to_representation(self, data):
        """
        List of object instances -> List of dicts of primitive datatypes.
        """
        return [self.child.to_representation(item) if item is not None else None for item in data.rsplit(',')]

    def to_internal_value(self, data):

        data = [int(d) for d in data[0].rsplit(',')]
        super(CustomStrField, self).to_internal_value(data)

    def get_value(self, dictionary):
        if self.field_name not in dictionary:
            if getattr(self.root, 'partial', False):
                return empty
        # We override the default field access in order to support
        # lists in HTML forms.
        if html.is_html_input(dictionary):
            val = dictionary.getlist(self.field_name, [])
            if len(val) > 0:
                # Support QueryDict lists in HTML input.
                return val
            return html.parse_html_list(dictionary, prefix=self.field_name, default=empty)

        return dictionary.get(self.field_name, empty)