from rest_framework import serializers

from apiv1.core.constants import DEVICE_STATUS_OFFLINE, DEVICE_STATUS_ERROR
from apiv1.core.response import reef_400_response
from apiv1.core.view.relations import PrimaryKeyRelatedPkField
from apiv1.module.resource.models import SIMCard, Account, APPGather, TGuard
from apiv1.module.device.models import Device, SubsidiaryDevice


class SIMCardSerializer(serializers.ModelSerializer):

    class Meta:
        model = SIMCard
        fields = "__all__"


class FilterDeviceSIMCardSerializer(serializers.ModelSerializer):
    device = serializers.PrimaryKeyRelatedField(
        queryset=Device.objects.exclude(status__in=[DEVICE_STATUS_OFFLINE, DEVICE_STATUS_ERROR]),
        required=False
    )

    class Meta:
        model = SIMCard
        fields = "__all__"


class AccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = Account
        fields = "__all__"


class APPGatherSerializer(serializers.ModelSerializer):

    max_login_num = serializers.IntegerField(min_value=1)

    class Meta:
        model = APPGather
        fields = "__all__"


class BindAccountSourceSerializer(serializers.ModelSerializer):

    ids = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=Account.objects.all()
        )
    )
    device = serializers.SlugRelatedField(
        slug_field='id',
        queryset=Device.objects.exclude(status__in=[DEVICE_STATUS_OFFLINE, DEVICE_STATUS_ERROR]),
        required=False
    )
    subsidiary_device = serializers.SlugRelatedField(
        slug_field='id',
        queryset=SubsidiaryDevice.objects.all(),
        required=False
    )

    class Meta:
        model = Account
        fields = ('ids', 'device', 'subsidiary_device')


class UnbindAccountSourceSerializer(serializers.ModelSerializer):

    account_id = serializers.PrimaryKeyRelatedField(
        queryset=Account.objects.all()
    )

    device = serializers.SlugRelatedField(
        slug_field='id',
        queryset=Device.objects.all(),
        required=False
    )
    subsidiary_device = serializers.SlugRelatedField(
        slug_field='id',
        queryset=SubsidiaryDevice.objects.all(),
        required=False
    )

    class Meta:
        model = Account
        fields = ('account_id', 'device', 'subsidiary_device')


class BlockUnbindResourceSerializer(serializers.Serializer):
    device = serializers.SlugRelatedField(
        slug_field='id',
        queryset=Device.objects.all(),
        required=False
    )
    subsidiary_device = serializers.SlugRelatedField(
        slug_field='id',
        queryset=SubsidiaryDevice.objects.all(),
        required=False
    )
    resource_type = serializers.ChoiceField(
        choices=['SIMCard', 'Account']
    )

    class Meta:
        fields = ('device', 'subsidiary_device', 'resource_type')


class ResourceExportSerializer(serializers.Serializer):

    resource_type = serializers.ChoiceField(
        choices=['SIMCard', 'Account']
    )


class SimCardExportSerializer(serializers.Serializer):

    sim_card = serializers.ListField(
        child=PrimaryKeyRelatedPkField(
            queryset=SIMCard.objects.all()
        )
    )


class AccountExportSerializer(serializers.Serializer):

    account = serializers.ListField(
        child=PrimaryKeyRelatedPkField(
            queryset=Account.objects.all(),
        )
    )


class ResourceImportSerializer(serializers.Serializer):

    import_file = serializers.FileField()

    def validate_import_file(self, value):
        file_name = value.name
        file_suffix = file_name.split('.')[len(file_name.split('.'))-1]
        if file_suffix not in ['xlsx', 'xls']:
            return reef_400_response(description=f'上传文件{file_name}:文件格式不正确，必须为xlsx或xls格式文件')
        return value


class TGuardSerializer(serializers.ModelSerializer):

    class Meta:
        model = TGuard
        fields = ('id', 'name')
        read_only_fields = ('id',)

