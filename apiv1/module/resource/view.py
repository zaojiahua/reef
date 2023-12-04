import logging
import os

import pandas as pd
import numpy as np
from datetime import datetime
from itertools import chain
from collections import Counter

import requests
from django.apps import apps
from django.core.files.uploadhandler import TemporaryFileUploadHandler
from django.utils import timezone
from pypinyin import pinyin, Style

from rest_framework import generics
from django.db import transaction
from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins

from apiv1.module.resource.models import Account, SIMCard, APPGather, TGuard
from apiv1.module.resource.serializer import BindAccountSourceSerializer, UnbindAccountSourceSerializer, \
    BlockUnbindResourceSerializer, ResourceExportSerializer, SimCardExportSerializer, AccountExportSerializer, \
    ResourceImportSerializer, TGuardSerializer
from apiv1.core.constants import DEVICE_STATUS_BUSY, DEVICE_STATUS_IDLE
from apiv1.core.response import ReefResponse, reef_400_response, reef_500_response
from apiv1.module.system.models import Cabinet
from reef import settings
from reef.settings import RESOURCE_EXCEL_FILE_EXPORT_PATH, SIM_CARD_EXPORT_TABLE_HEAD, ACCOUNT_EXPORT_TABLE_HEAD, \
    MEDIA_URL, RESOURCE_EXCEL_FILE_EXPORT


class BindAccountSourceView(generics.GenericAPIView):

    serializer_class = BindAccountSourceSerializer
    queryset = Account.objects.all()

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        accounts = validated_data.get('ids', None)
        device = validated_data.get('device', None)
        subsidiary_device_obj = validated_data.get('subsidiary_device', None)

        bind_fail_list = []
        for account in accounts:
            # 校验账号最大登录数
            max_login_num = account.app.max_login_num
            usage_num = account.device.all().count() + account.subsidiary_device.all().count()
            # 存在旧数据，可能使用数大于最大登录数
            if usage_num >= max_login_num:
                bind_fail_list.append(f'{account.app_name}:{account.name}')
                continue
            if device:
                account.device.add(device)
            if subsidiary_device_obj:
                account.subsidiary_device.add(subsidiary_device_obj)
        return ReefResponse(data=bind_fail_list)


class UnbindAccountSourceView(generics.GenericAPIView):

    serializer_class = UnbindAccountSourceSerializer
    queryset = Account.objects.all()

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        account = validated_data.get('account_id', None)
        device = validated_data.get('device', None)
        subsidiary_device_obj = validated_data.get('subsidiary_device', None)
        if device:
            account.device.remove(device)
        if subsidiary_device_obj:
            account.subsidiary_device.remove(subsidiary_device_obj)
        device_gather = account.device.all()
        subsidiary_device_gather = account.subsidiary_device.all()
        if not device_gather and not subsidiary_device_gather:
            account.status = DEVICE_STATUS_IDLE
            account.save()
        return ReefResponse()


class BlockUnbindSimCardView(generics.GenericAPIView):

    serializer_class = BlockUnbindResourceSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        device = validated_data.get('device', None)
        subsidiary_device = validated_data.get('subsidiary_device', None)
        resource_type = validated_data.get('resource_type', None)
        # 有资源 批量解除绑定
        if resource_type:
            if device:
                if resource_type == 'SIMCard':
                    release_sim_card_resource(device)
                elif resource_type == 'Account':
                    release_account_resource(device)
            if subsidiary_device:
                if resource_type == 'SIMCard':
                    release_sim_card_resource(subsidiary_device)
                elif resource_type == 'Account':
                    release_account_resource(subsidiary_device)
        return ReefResponse()


class GetOrderAppNameView(generics.GenericAPIView):

    def _to_pinyin(self, data):
        '''
        转拼音
        '''
        data = data['name']
        return ''.join(chain.from_iterable(pinyin(data, style=Style.TONE3)))

    def get(self, request):
        name_list = APPGather.objects.all().values('name', 'id')
        name_list = sorted(name_list, key=self._to_pinyin)
        return ReefResponse({'result': name_list})


class ResourceExportView(generics.GenericAPIView):

    serializer_class = ResourceExportSerializer

    def get_queryset(self):
        super().get_queryset()

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        resource_type = serializer.validated_data.get('resource_type', None)
        export_fields = []
        filter_list = []
        if resource_type == 'SIMCard':
            serializer = SimCardExportSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            filter_list = serializer.validated_data.get('sim_card', [])
            export_fields = SIM_CARD_EXPORT_TABLE_HEAD
        elif resource_type == 'Account':
            serializer = AccountExportSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            filter_list = serializer.validated_data.get('account', [])
            export_fields = ACCOUNT_EXPORT_TABLE_HEAD
        if resource_type and export_fields:
            model = apps.get_model('apiv1', f'{resource_type}')
            resource_data = model.objects.filter(id__in=filter_list).values_list(*export_fields)
            df = pd.DataFrame(resource_data, columns=export_fields)
            excel_file_name = f'{resource_type}-{timezone.localtime().strftime("%Y-%m-%d-%H:%M:%S")}.xlsx'
            execl_file = os.path.join(RESOURCE_EXCEL_FILE_EXPORT_PATH, excel_file_name)
            df.to_excel(execl_file, sheet_name=f'{resource_type}', index=False)
        else:
            return reef_400_response(description='没有可以导出的资源')
        return ReefResponse(os.path.join(MEDIA_URL, RESOURCE_EXCEL_FILE_EXPORT, excel_file_name))


class ResourceImportView(generics.GenericAPIView):

    serializer_class = ResourceImportSerializer

    def get_queryset(self):
        super().get_queryset()

    def post(self, request):
        """
        导入校验：
        a. 共有特性校验
            1. sheet name 是否在指定范围内
            2. chekcout 表头
            3. 必填字段不能为空
            4. 校验导入冲突，（数据库已有此条数据）
        b. 根据表数据特性校验
            1. app名称在范围内，app 外键字段通过名称获取 (Account)

        注：文档校验提示，一次返回所有存在错误。全部数据校验完成后执行导入操作，有错误不执行导入。
        """
        request.upload_handlers = [TemporaryFileUploadHandler(request)]
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        import_file = serializer.validated_data.get('import_file', None)
        df = pd.read_excel(f'{import_file.file.name}', sheet_name=None)
        # checkout excel validity
        sheet_names = list(df)
        error_list = checkout_excel_data(sheet_names, import_file)
        if not error_list:
            # 校验完成没有错误信息导入数据
            insert_data(sheet_names, import_file)
            return ReefResponse()
        else:
            return reef_400_response(data=error_list)


class TGuardViewSet(mixins.DestroyModelMixin,
                    mixins.CreateModelMixin,
                    mixins.ListModelMixin,
                    GenericViewSet):

    serializer_class = TGuardSerializer
    queryset = TGuard.objects.all()

    def list(self, request, *args, **kwargs):
        t_guard_data = get_t_guard_data()
        return ReefResponse(data=t_guard_data)

    def perform_create(self, serializer):
        super().perform_create(serializer)
        broadcast_fail_list = broadcast_coral('post', {serializer.data['id']: serializer.data['name']})
        if broadcast_fail_list:
            self.response_data(broadcast_fail_list)

    def perform_destroy(self, instance):
        broadcast_fail_list = broadcast_coral('delete', [instance.id])
        super().perform_destroy(instance)
        if broadcast_fail_list:
            self.response_data(broadcast_fail_list)

    def response_data(self, broadcast_fail_list):
        cabinet_name_list = []
        for ip in broadcast_fail_list:
            try:
                cabinet = Cabinet.objects.get(ip_address=ip)
                cabinet_name_list.append(cabinet.cabinet_name)
            except:
                pass
        return reef_500_response(data=cabinet_name_list)


@transaction.atomic()
def insert_data(sheet_name_list, import_file):
    for sheet_name in sheet_name_list:
        df = pd.read_excel(f'{import_file.file.name}', sheet_name=sheet_name)
        # 非必填字段处理为null
        df = df.where(df.notnull(), None)
        column, row = df.shape
        model = apps.get_model('apiv1', sheet_name)
        # 提前提取数据，避免多次查询
        app_dict = {}
        if sheet_name == "Account":
            app_dict = {app.name: app.id for app in APPGather.objects.all()}
        for i in range(column):
            column_data = df.loc[i]
            res_data = column_data.to_dict()
            if sheet_name == "Account":
                # 创建数据添加app 字段
                res_data['app_id'] = app_dict[res_data['app_name']]
            try:
                model_obj = model.objects.create(**res_data)
                model_obj.save()
            except Exception as e:
                return reef_400_response(
                    message=f'import {sheet_name} resource error: {e}',
                    data=[f'{sheet_name}页，第{i + 1} 行存在重复行数据，请修改重复数据！！！']
                )


def checkout_excel_data(sheet_name_list, import_file):
    error_list = []
    sheet_name_restrain_list = ['SIMCard', 'Account']
    for sheet_name in sheet_name_list:
        # checkout sheet name
        if sheet_name not in sheet_name_restrain_list:
            error_list.append(f'Excel sheet_name 名称: {sheet_name} 不合法，必须是 SIMCard 或 Account')
            return reef_400_response(data=error_list)
        # checkout table head
        df = pd.read_excel(f'{import_file.file.name}', sheet_name=sheet_name)
        column, row = df.shape

        table_head = df.columns.values
        table_head_error_list, model = checkout_table_head(sheet_name, table_head)
        if table_head_error_list:
            error_list.extend(table_head_error_list)
            # 表头错误影响后续可插入判断，直接返回错误信息
            return reef_400_response(data=error_list)
        # checkout NaN value
        # Account phone_number column no verification nan value
        if sheet_name == 'Account':
            cut_df = cut_not_checkout_nan_column(df, ['phone_number'])
        else:
            cut_df = df
        is_none = cut_df.isnull().values.any()
        if is_none:
            nan_index = set(np.where(cut_df.isna())[0])
            for index in nan_index:
                error_list.append(f'{sheet_name}页,第{index + 1}行存在空值，请补全后重新导入')
        # checkout app name, 根据不同表数据特性进行校验。
        if sheet_name == 'Account':
            if 'app_name' in df.columns:
                app_names = df['app_name'].values
                db_app_name_list = list(APPGather.objects.all().values_list('name', flat=True))
                error_app_name_list = [f'{app_name} 名称不在选择范围内！！!' for app_name in app_names if
                                       app_name not in db_app_name_list and not (pd.isnull(app_name))]
                if error_app_name_list:
                    error_list.extend(error_app_name_list)
            # checkout import clash
            target_db_account_list = [
                f'{account.name}-{account.app_name}'
                for account in
                Account.objects.all()
            ]
            for i in range(column):
                column_data = df.loc[i]
                res_data = column_data.to_dict()
                if f'{res_data["name"]}-{res_data["app_name"]}' in target_db_account_list:
                    error_list.append(f'{sheet_name}页,第{i + 2} 行数据:{res_data["name"]}-{res_data["app_name"]}已存在于数据库！！！')
        elif sheet_name == 'SIMCard':
            # checkout import clash
            target_db_sim_card_list = SIMCard.objects.all().values_list('phone_number', flat=True)
            for i in range(column):
                column_data = df.loc[i]
                res_data = column_data.to_dict()
                if str(res_data['phone_number']) in target_db_sim_card_list:
                    error_list.append(f'{sheet_name}页,第{i + 2} 行数据:{res_data["operator"]}-{res_data["phone_number"]}已存在于数据库！！！')
        return error_list


def cut_not_checkout_nan_column(df, cut_column_list):
    # cut have no use for checkout column
    cut_df = df
    for column_name in cut_column_list:
        if column_name in df.columns.values:
            cut_df = cut_df.drop(column_name, axis=1)
    return cut_df


def checkout_table_head(model_name: str, table_head_list):
    table_head_error_list = []
    checkout_list = Counter(table_head_list)
    if model_name == 'Account':
        if not checkout_list == Counter(ACCOUNT_EXPORT_TABLE_HEAD):
            table_head_error_list.append(f'表头: {table_head_list}存在错误项！！！')
    elif model_name == "SIMCard":
        if not checkout_list == Counter(SIM_CARD_EXPORT_TABLE_HEAD):
            table_head_error_list.append(f'表头: {table_head_list}存在错误项！！！')
    model = apps.get_model('apiv1', model_name)
    for data in table_head_list:
        if data not in [field.column for field in model._meta.fields]:
            table_head_error_list.append(f'表头: {data} 不在选择范围内！！！')
    return table_head_error_list, model


def release_sim_card_resource(device):
    for simcard in device.simcard.all():
        simcard.status = DEVICE_STATUS_IDLE
        simcard.order = None
        if hasattr(device, 'device_name'):
            simcard.history_relevance = device.device_name
            simcard.device = None
        if hasattr(device, 'custom_name'):
            simcard.history_relevance = device.custom_name
            simcard.subsidiary_device = None
        simcard.save()


def release_account_resource(device):
            account_queryset = list(device.account.all())
            if account_queryset:
                device.account.clear()
            for account in account_queryset:
                device_gather = account.device.all()
                subsidiary_device_gather = account.subsidiary_device.all()
                if not device_gather and not subsidiary_device_gather:
                    account.status = DEVICE_STATUS_IDLE
                    account.save()


def get_t_guard_data():
    t_guard_list = list(TGuard.objects.filter(is_system=True).order_by('id').values('id', 'name', 'is_system'))
    t_guard_list.extend(TGuard.objects.filter(is_system=False).order_by('id').values('id', 'name', 'is_system'))
    # [{'id':1, 'name': "你好"}]
    return t_guard_list


def broadcast_coral(r_method, r_body):
    ip_list = Cabinet.objects.filter(is_delete=False).values_list('ip_address', flat=True)
    broadcast_fail_list = []
    for ip in ip_list:
        try:
            if r_method == 'post':
                method = getattr(requests, 'post')
            elif r_method == 'delete':
                method = getattr(requests, 'delete')
            else:
                return reef_500_response()
            response = method(
                url=f"http://{ip}:{settings.CORAL_PORT}/eblock/bounced_words",
                json=r_body,
                timeout=1
            )
        except Exception as e:
            # HTTPError 不影响后续coral的通知
            broadcast_fail_list.append(ip)
    return broadcast_fail_list



