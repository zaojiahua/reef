from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from apiv1.core.response import reef_400_response, reef_500_response
from apiv1.module.device.models import Device, PhoneModel
from apiv1.module.job.models import Job, TestGather
from apiv1.module.tboard.business import insert_get_battery_job
from apiv1.module.tboard.models import TBoard, TBoardJob, TBoardStatisticsResult
from apiv1.module.tboard.validator import validate_device_battery_level, validate_uniq_job
from apiv1.module.user.models import ReefUser


class TBoardSerializer(serializers.ModelSerializer):
    """
    Generic Serializer
    """
    job = serializers.PrimaryKeyRelatedField(many=True, queryset=Job.objects.all())

    class Meta:
        model = TBoard
        fields = '__all__'

    def validate(self, attrs):
        if not self.partial:
            validate_device_battery_level(attrs["device"], attrs["job"])
            validate_uniq_job(
                attrs["repeat_time"] if "repeat_time" in attrs else TBoard._meta.get_field('repeat_time').get_default(),
                attrs["job"])
        return attrs

    def save(self, **kwargs):
        jobs = self.validated_data.pop("job", [])
        tboard = super(TBoardSerializer, self).save(**kwargs)
        tboardjobs = []
        order = 0
        for job in jobs:
            tboardjobs.append(TBoardJob(
                tboard=tboard,
                job=job,
                order=order
            ))
            order += 1
        TBoardJob.objects.bulk_create(tboardjobs, batch_size=100)
        insert_get_battery_job(tboard)
        return tboard


class CreateTBoardSerializer(serializers.ModelSerializer):
    """
    Coral创建tboard接口
    """
    owner_label = serializers.SlugRelatedField(
        queryset=ReefUser.objects.all(),
        slug_field='id',
        source='author'
    )
    finished_flag = serializers.BooleanField(
        required=False
    )
    board_stamp = serializers.DateTimeField(
        default=timezone.now
    )
    device_label_list = serializers.ListField(
        child=serializers.SlugRelatedField(
            queryset=Device.objects.filter(status='idle'),
            slug_field='device_label'
        ),
        source='device'
    )
    job_label_list = serializers.ListField(
        child=serializers.SlugRelatedField(
            queryset=Job.objects.filter(job_deleted=False),
            slug_field='job_label'
        ),
        source='job'
    )
    end_time = serializers.DateTimeField(
        required=False
    )
    repeat_time = serializers.IntegerField(
        min_value=1
    ),
    cabinet_dict = serializers.JSONField(
        required=False
    )

    job_prior_data = serializers.DictField(
        child=serializers.ListField(
            child=serializers.SlugRelatedField(
                queryset=Job.objects.filter(job_deleted=False),
                slug_field='job_label'
            )
        ),
        required=False
    )

    test_gather_name = serializers.CharField(allow_blank=True, required=False)

    class Meta:
        model = TBoard
        fields = (
            'id',
            'owner_label',
            'repeat_time',
            'board_name',
            'finished_flag',
            'board_stamp',
            'device_label_list',
            'job_label_list',
            'end_time',
            'cabinet_dict',
            'tboard_type',
            'tboard_second_type',
            'job_prior_data',
            'job_random_order',
            'test_gather_name',
            'belong'
        )
        extra_kwargs = {
            'id': {'read_only': True},
            'repeat_time': {'write_only': True},
            'board_name': {'write_only': True},
            'owner_label': {'write_only': True},
            'finished_flag': {'write_only': True},
            'board_stamp': {'write_only': True},
            'device_label_list': {'write_only': True},
            'job_label_list': {'write_only': True},
            'end_time': {'write_only': True},
            'cabinet_dict': {'write_only': True},
            'tboard_type': {'write_only': True},
            'tboard_second_type': {'write_only': True}
        }

    def validate(self, attrs):
        validate_device_battery_level(attrs["device"], attrs["job"])
        validate_uniq_job(
            attrs["repeat_time"] if "repeat_time" in attrs else TBoard._meta.get_field('repeat_time').get_default(),
            attrs["job"])
        return attrs

    @transaction.atomic
    def save(self, **kwargs):
        devices = self.validated_data.pop("device")
        jobs = self.validated_data.pop("job")
        self.validated_data.pop('job_prior_data', {})
        try:
            tboard = TBoard(**self.validated_data)
            tboard.save()

            # Create tboard-device relation
            tboard.device.set(devices)

            # Create tboard-job relation
            order = 0
            tboardjobs = []
            for job in jobs:
                tboardjobs.append(TBoardJob(
                    tboard=tboard,
                    job=job,
                    order=order
                ))
                order += 1

            TBoardJob.objects.bulk_create(tboardjobs, batch_size=1)
            insert_get_battery_job(tboard)
        except Exception as e:
            reef_500_response(message=f'create tboard db error: {e}', description='创建任务异常，数据创建失败，请联系管理员解决')
        else:
            return tboard


class OpenCreateTBoardSerializer(CreateTBoardSerializer):
    owner_label = serializers.SlugRelatedField(
        queryset=ReefUser.objects.all(),
        slug_field='username',
        source='author'
    )


class CoolPadCreateTBoardSerializer(serializers.ModelSerializer):

    owner_label = serializers.SlugRelatedField(
        default='admin',
        queryset=ReefUser.objects.all(),
        slug_field='id',
        source='author',
        required=False
    )
    finished_flag = serializers.BooleanField(
        default=False,
        required=False
    )
    board_stamp = serializers.DateTimeField(
        default=timezone.now
    )
    phone_model = serializers.SlugRelatedField(
        queryset=PhoneModel.objects.all(),
        slug_field='phone_model_name'
    )
    fastboot_job = serializers.SlugRelatedField(
        queryset=Job.objects.filter(job_deleted=False),
        slug_field='job_label'
    )
    jobs = serializers.ListField(
        child=serializers.DictField()
    )

    finis_job = serializers.SlugRelatedField(
        queryset=Job.objects.filter(job_deleted=False),
        slug_field='job_label'
    )

    file_path = serializers.CharField()

    description = serializers.CharField()
    belong = serializers.CharField(default='coolpad', required=False)
    ftp_ip = serializers.CharField(
        default='10.80.5.80',
        required=False
    )
    ftp_port = serializers.IntegerField(
        default=21,
        required=False
    )
    ftp_user = serializers.CharField(
        default='yulong\\tmach',
        required=False
    )
    ftp_passwd = serializers.CharField(
        default='CP@20*&22%tm',
        required=False
    )
    special_job = serializers.SlugRelatedField(
        queryset=Job.objects.filter(job_deleted=False),
        slug_field='job_label'
    )

    class Meta:
        model = TBoard
        fields = (
            'id',
            'owner_label',
            'board_name',
            'finished_flag',
            'board_stamp',
            'phone_model',
            'jobs',
            'end_time',
            'cabinet_dict',
            'tboard_type',
            'tboard_second_type',
            'belong',
            'fastboot_job',
            'description',
            'file_path',
            'finis_job',
            'ftp_ip',
            'ftp_port',
            'ftp_user',
            'ftp_passwd',
            'special_job'
        )
        extra_kwargs = {
            'id': {'read_only': True}
        }

    def validate(self, attrs):
        jobs = attrs.get('jobs')
        for job in jobs:
            try:
                job['job_label'] = Job.objects.get(job_label=job['job_label'])
            except Exception as e:
                from rest_framework.exceptions import ValidationError
                raise ValidationError(f'Object with jobs_job_label={job["job_label"]} does not exist.')
        return attrs

    @transaction.atomic
    def save(self, **kwargs):
        phone_model = self.validated_data.pop("phone_model")
        jobs = self.validated_data.pop("jobs")
        fastboot_job = self.validated_data.pop("fastboot_job")
        description = self.validated_data.pop("description")
        devices = self.validated_data.pop("devices")
        file_path = self.validated_data.pop("file_path")
        ftp_ip = self.validated_data.pop("ftp_ip")
        ftp_port = self.validated_data.pop("ftp_port")
        ftp_user = self.validated_data.pop("ftp_user")
        ftp_passwd = self.validated_data.pop("ftp_passwd")
        special_job = self.validated_data.pop("special_job")
        finis_job = self.validated_data.pop("finis_job")
        author = self.validated_data.pop('author')
        if isinstance(author, str) and author == 'admin':
            self.validated_data['author'] = ReefUser.objects.filter(username='admin').first()
        try:
            tboard = TBoard(**self.validated_data)
            tboard.save()

            # Create tboard-device relation
            tboard.device.set(devices)

            # Create tboard-job relation
            order = 0
            tboardjobs = []
            for job in jobs:
                tboardjobs.append(TBoardJob(
                    tboard=tboard,
                    job=job,
                    order=order
                ))
                order += 1

            TBoardJob.objects.bulk_create(tboardjobs, batch_size=1)
            insert_get_battery_job(tboard)
        except Exception as e:
            reef_500_response(message=f'create tboard db error: {e}', description='创建任务异常，数据创建失败，请联系管理员解决')
        else:
            return tboard


class EndTBoardSerializer(serializers.ModelSerializer):
    """
    Coral完成一个任务时，会呼叫此接口，结束任务的运行
    """
    end_time = serializers.DateTimeField(
        format='%Y_%m_%d_%H_%M_%S',
        input_formats=['%Y_%m_%d_%H_%M_%S'],
        write_only=True
    )
    finished_flag = serializers.HiddenField(default=True)
    cabinet_dict = serializers.JSONField(binary=True, required=False)
    updated_time = serializers.HiddenField(default=timezone.now)

    class Meta:
        model = TBoard
        fields = (
            'end_time',
            'finished_flag',
            'updated_time',
            'cabinet_dict'
        )

    def validate(self, attrs):
        tboard_cabinet_dict = self.instance.cabinet_dict
        cabinet_dict = attrs.get('cabinet_dict', None)

        if not tboard_cabinet_dict:
            return attrs

        if not cabinet_dict:
            raise serializers.ValidationError('tboard related cabinet instance, should input cabinet to end tboard')

        is_exist = len([0 for key in attrs['cabinet_dict'].keys() if key not in tboard_cabinet_dict]) == 0
        if not is_exist:
            raise serializers.ValidationError('input incorrect cabinet_dict, tboard is not running in this cabinet')

        tboard_cabinet_dict.update(attrs['cabinet_dict'])
        attrs['cabinet_dict'] = tboard_cabinet_dict

        # 判断是否全部更新完成
        vaild_status = list(filter(lambda n: n != -1, list(tboard_cabinet_dict.values())))
        if any(vaild_status):
            attrs.pop('finished_flag')
            attrs.pop('end_time')
        return attrs


class TBoardRunningDetailJobSerializer(serializers.ModelSerializer):
    """
    Nested Serializer for TBoardRunningDetailSerializer
    """

    class Meta:
        model = Job
        fields = (
            'id',
            'job_name',
        )


class TBoardRunningDetailDeviceSerializer(serializers.ModelSerializer):
    """
    Nested Serializer for TBoardRunningDetailSerializer
    """
    has_rds = serializers.BooleanField(default=False)

    class Meta:
        model = Device
        fields = (
            'id',
            'device_name',
            'has_rds'
        )


class TBoardRunningDetailSerializer(serializers.ModelSerializer):
    """
    取得tboard的细节运行结果
    """
    jobs = TBoardRunningDetailJobSerializer(source='job', many=True)
    devices = TBoardRunningDetailDeviceSerializer(source='device', many=True)

    class Meta:
        model = TBoard
        fields = (
            'id',
            'jobs',
            'devices'
        )


class GetTboardStatisticsSerializer(serializers.ModelSerializer):
    """
    取得tboard的整体统计结果
    """
    total = serializers.IntegerField(default=0)
    success = serializers.IntegerField(default=0)
    fail = serializers.IntegerField(default=0)
    na = serializers.IntegerField(default=0)
    failure = serializers.FloatField(default=0)

    class Meta:
        model = TBoard
        fields = (
            'id',
            'board_stamp',
            'total',
            'success',
            'fail',
            'na',
            'failure'
        )


class JobPriorTboardSerializer(serializers.ModelSerializer):
    """
    Job 优先Tboard
    """
    pass


class GetJobPriorTboardSerializer(serializers.ModelSerializer):

    jobs_id = serializers.CharField(
    )

    class Meta:
        model = TBoard
        fields = ('jobs_id',)

    def validate(self, attrs):
        jobs = attrs['jobs_id'].split(',')
        for job_id in jobs:
            try:
                job = Job.objects.get(id=job_id)
            except Exception as e:
                raise serializers.ValidationError('job id not exist')
        return attrs


class RepeatExecuteTBoardSerializer(serializers.ModelSerializer):

    class Meta:
        model = TBoard
        fields = ('id',)


class GetTBoardFieldsSerializer(serializers.ModelSerializer):

    class Meta:
        model = TBoard
        exclude = ('id', 'board_name', 'finished_flag', 'board_stamp', 'end_time', 'success_ratio', 'cabinet_dict')


class CreateRepeatTBoardSerializer(serializers.ModelSerializer):

    job = serializers.PrimaryKeyRelatedField(many=True, queryset=Job.objects.all())

    class Meta:
        model = TBoard
        fields = '__all__'

    def save(self, **kwargs):
        jobs = self.validated_data.pop("job", [])
        tboard = super(CreateRepeatTBoardSerializer, self).save(**kwargs)
        tboardjobs = []
        order = 0
        for job in jobs:
            tboardjobs.append(TBoardJob(
                tboard=tboard,
                job=job,
                order=order
            ))
            order += 1
        TBoardJob.objects.bulk_create(tboardjobs, batch_size=100)
        insert_get_battery_job(tboard)
        return tboard


class RepeatExecuteTBoardCheckSerializer(serializers.Serializer):

    tboard = serializers.PrimaryKeyRelatedField(
        queryset=TBoard.objects.filter(is_to_delete=False)
    )


class ReleaseBusyDeviceSerializer(serializers.Serializer):

    tboard_id = serializers.PrimaryKeyRelatedField(
        queryset=TBoard.objects.all()
    )

    class Meta:
        model = TBoard
        fields = ('tboard_id',)


class TBoardStatisticsResultSerializer(serializers.ModelSerializer):

    class Meta:
        model = TBoardStatisticsResult
        fields = '__all__'