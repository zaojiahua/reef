from rest_framework import serializers

from apiv1.module.device.models import Device
from apiv1.module.system.models import Cabinet, System, WoodenBox


class CabinetSerializer(serializers.ModelSerializer):
    """
    Generic Serializer
    """

    class Meta:
        model = Cabinet
        fields = '__all__'


class SystemSerializer(serializers.ModelSerializer):
    """
    Generic Serializer
    """

    class Meta:
        model = System
        fields = '__all__'


class GetReefSpaceUsageSerialzier(serializers.Serializer):
    """
    取得Reef主机硬盘信息
    """
    # Used for auto documenting
    total = serializers.CharField(read_only=True)
    used = serializers.CharField(read_only=True)
    free = serializers.CharField(read_only=True)


class CabinetRegistSerializer(serializers.ModelSerializer):
    """
    Coral向Reef注册机柜信息
    """
    cabinet_name = serializers.CharField(required=False)
    belong_to_id = serializers.PrimaryKeyRelatedField(
        queryset=System.objects.all(),
        required=False
    )
    is_delete = serializers.BooleanField(default=False, required=False)
    ip_address = serializers.IPAddressField()
    id = serializers.IntegerField(min_value=1)
    m_location_x = serializers.FloatField(required=False)
    m_location_y = serializers.FloatField(required=False)
    m_location_z = serializers.FloatField(required=False)

    def validate(self, value):
        ip_address = value.get('ip_address', None)
        id = value.get('id', None)
        if ip_address:
            queryset = Cabinet.objects.exclude(id=id).filter(ip_address=ip_address)
            if queryset.exists():
                raise serializers.ValidationError(f'Key (ip_address)=({ip_address}) already exists!!')
        return value

    class Meta:
        model = Cabinet
        fields = (
            'id',
            "cabinet_name",
            "ip_address",
            "belong_to_id",
            "type",
            "is_delete",
            "m_location_x",
            "m_location_y",
            "m_location_z"
        )


class WoodenBoxSerializer(serializers.ModelSerializer):

    class Meta:
        model = WoodenBox
        fields = ('name',
                  'type',
                  'ip',
                  'config',
                  'cabinet')


class CreateWoodenBoxSerializer(serializers.ModelSerializer):

    class Meta:
        model = WoodenBox
        fields = ('name',
                  'type',
                  'ip',
                  'config',
                  'cabinet')


class GetCabinetTypeInfoSerializer(serializers.Serializer):

    data_type = serializers.ChoiceField(
        ("cabinet_type_data", "cabinet_type_data"),
        required=False
    )

    class Meta:
        model = Cabinet
        fields = ('data_type',)


class UpdateCabinetMLocationSerializer(serializers.Serializer):

    cabinet_id = serializers.PrimaryKeyRelatedField(
        queryset=Cabinet.objects.filter(is_delete=False)
    )
    m_location_x = serializers.FloatField()
    m_location_y = serializers.FloatField()
    m_location_z = serializers.FloatField(min_value=-34, max_value=4)
    device_label = serializers.SlugRelatedField(
        slug_field="device_label",
        queryset=Device.objects.all()
    )


class DeleteLogSerializer(serializers.Serializer):

    start_date = serializers.DateField()
    end_date = serializers.DateField()



