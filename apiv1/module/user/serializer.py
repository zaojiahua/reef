from django.contrib.auth.models import Group
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError

from apiv1.core.constants import REEF_ADMIN_GROUP_NAME
from apiv1.module.user.models import ReefUser


class GroupSerializer(serializers.ModelSerializer):
    """
    Generic Serializer
    """

    class Meta:
        model = Group
        fields = '__all__'


class ReefUserSerializer(serializers.ModelSerializer):
    """
    Generic Serializer
    """

    groups = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Group.objects.all(),
        many=True
    )

    class Meta:
        model = ReefUser
        fields = '__all__'

    def validate(self, attrs):
        # Admin role is_active field can not change to false
        if not self.partial or not self.update:
            return attrs

        if REEF_ADMIN_GROUP_NAME in list(self.instance.groups.all().values_list('name', flat=True)):
            is_active = attrs.get('is_active', None)
            if is_active is not None and is_active is False:
                raise ValidationError('superuser login status can not change')
        return attrs


class LoginSerializer(serializers.Serializer):
    """
    Cedar登入
    """
    username = serializers.CharField()
    password = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    """
    Cypress登入
    """
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    groups = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name'
    )
    port = serializers.ReadOnlyField()

    class Meta:
        model = ReefUser
        fields = ('username', 'password', 'port', 'groups')


class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = '__all__'
