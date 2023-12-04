import json

from django.apps import apps
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import F, Max, Avg
from django.utils import timezone

from apiv1.core.constants import JOB_TYPE_UNIQ, JOB_TYPE_UNKNOWN, JOB_TYPE_SYS_JOB, JOB_TYPE_JOB_LIB, \
    JOB_TYPE_INNER_JOB, JOB_SECOND_TYPE_TIME_JOB, JOB_TYPE_PERF_JOB, JOB_TYPE_MULTI_DEVICE_JOB, JOB_FLOW_EXECUTE_SPLIT, \
    JOB_FLOW_EXECUTE_MULTI, NORMAL_JOB_FLOW, INNER_JOB_FLOW, JOB_SECOND_TYPE_SMOOTHLY_JOB, JOB_TYPE_COMBO_JOB
from apiv1.core.model import AbsDescribe
from apiv1.core.response import reef_400_response
from apiv1.module.job.error import ValidationError
from apiv1.core.managers import JobFlowManager
from reef import settings


class CustomTag(models.Model):
    custom_tag_name = models.CharField(max_length=50, verbose_name='自定义标签名称', unique=True)

    class Meta:
        verbose_name_plural = "自定义标签"


class JobTestArea(models.Model):
    description = models.TextField(unique=True, db_index=True, verbose_name='测试用途描述')

    class Meta:
        verbose_name_plural = "测试用途"


class Job(models.Model):
    # job业务识别标签，coral生成，某些需求下系统会依照job_label去筛选特定的特殊用例
    job_label = models.CharField(max_length=50, unique=True, db_index=True, verbose_name='用例标签')
    job_name = models.CharField(max_length=100, verbose_name='用例名称')
    job_type = models.CharField(
        max_length=10,
        choices=(
            (JOB_TYPE_UNKNOWN, JOB_TYPE_UNKNOWN),
            (JOB_TYPE_SYS_JOB, JOB_TYPE_SYS_JOB),
            (JOB_TYPE_JOB_LIB, JOB_TYPE_JOB_LIB),
            (JOB_TYPE_PERF_JOB, JOB_TYPE_PERF_JOB),
            (JOB_TYPE_UNIQ, JOB_TYPE_UNIQ),
            (JOB_TYPE_INNER_JOB, JOB_TYPE_INNER_JOB),
            (JOB_TYPE_COMBO_JOB, JOB_TYPE_COMBO_JOB),
            (JOB_TYPE_MULTI_DEVICE_JOB, JOB_TYPE_MULTI_DEVICE_JOB)
        ),
        verbose_name='用例类型'
    )
    job_second_type = models.CharField(
        max_length=10,
        choices=(
            (JOB_SECOND_TYPE_TIME_JOB, JOB_SECOND_TYPE_TIME_JOB),
            (JOB_SECOND_TYPE_SMOOTHLY_JOB, JOB_SECOND_TYPE_SMOOTHLY_JOB)
        ),
        null=True, blank=True,
        verbose_name='用例二级分类'
    )
    description = models.TextField(blank=True, verbose_name='用例描述')
    author = models.ForeignKey("ReefUser", on_delete=models.PROTECT, related_name='job', verbose_name='用户')
    test_area = models.ManyToManyField(JobTestArea, related_name='job', verbose_name='用例用途')

    # Job 設備白名單，要運行Job的设备，其属性须在白名单内（全部符合）
    android_version = models.ManyToManyField("AndroidVersion", related_name='job', verbose_name='安卓版本限制')
    phone_models = models.ManyToManyField("PhoneModel", related_name='job', verbose_name='手机机型限制')
    rom_version = models.ManyToManyField("RomVersion", related_name='job', verbose_name='手机系统版本号限制')
    power_upper_limit = models.PositiveSmallIntegerField(null=True, verbose_name='手机电量上限限制')
    power_lower_limit = models.PositiveSmallIntegerField(null=True, verbose_name='手机电量下限限制')

    custom_tag = models.ManyToManyField(CustomTag, related_name='job', verbose_name='自定义标签')
    # TMach系统中所有的用例，目前都不允许用户删除实际数据，提供job_delete字段标记job是否被删除
    job_deleted = models.BooleanField(default=False, verbose_name='用例是否被删除')
    draft = models.BooleanField(default=True, verbose_name='用例是否有效')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='用例最后更新时间')
    ui_json_file = models.FileField(upload_to="ui_json", verbose_name='job编辑完成之后生成的uijson文件')
    case_number = models.CharField(max_length=50, blank=True, null=True, verbose_name='中科创达用例编号')
    priority = models.CharField(max_length=50, blank=True, null=True, verbose_name='中科创达用例的级别')
    matching_rule = JSONField(null=True, verbose_name='job匹配device规则')
    flow_execute_mode = models.CharField(
        max_length=50,
        choices=(
            (JOB_FLOW_EXECUTE_SPLIT, JOB_FLOW_EXECUTE_SPLIT),
            (JOB_FLOW_EXECUTE_MULTI, JOB_FLOW_EXECUTE_MULTI),
        ),
        verbose_name='job执行流执行模式')
    cabinet_type = models.CharField(max_length=50, verbose_name="机柜类型", null=True)

    complexity = models.IntegerField(default=0, verbose_name="复杂度")
    unit_group = models.CharField(max_length=150, blank=True, null=True, verbose_name="使用unit类型")
    is_support_parameter = models.BooleanField(default=False, verbose_name="job是否支持传参")

    class Meta:
        verbose_name_plural = "用例"

    def set_complexity(self):
        # 计算用例的复杂度，依次遍历所有的unit，加和得到最终的复杂度，在用例保存时做计算
        # 下面这个dict是计算的标准，复合unit5分，普通adbunit1分，图像识别unit5分，switchblock5分，innerjob10分
        grade_dict = {"COMPLEX": 5, "ADBC": 1, "IMGTOOL": 5, "switchBlock": 5, "Job": 10}
        final_complexity = 0
        flow_qs = JobFlow.objects.filter(job=self.id).all()
        # job-->flow-->block-->unit 多层级关系
        for job_flow in flow_qs:
            flow_path = job_flow.ui_json_file
            try:
                ui_json = json.loads(str(flow_path.read(), 'utf-8'))
            except (FileNotFoundError, ValueError) as e:
                continue
            for block in ui_json.get("nodeDataArray", []):
                try:
                    if block.get("category") in ["switchBlock", "Job"]:
                        final_complexity += grade_dict.get(block.get("category"), 0)
                    elif block.get("unitLists") is not None:
                        # 兼容新旧unit格式
                        unit_list = json.loads(block.get("unitLists")) if isinstance(block.get("unitLists"),
                                                                                     str) else block.get("unitLists",
                                                                                                         {})
                        node_data = unit_list.get("nodeDataArray", [])
                        for unit in node_data:
                            if unit.get("category") == "Unit":
                                unit_type = unit.get("unitMsg", {}).get("execModName")
                                final_complexity += grade_dict.get(unit_type, 0)
                except AttributeError as e:
                    continue
        return final_complexity

    @property
    def process_time(self):
        calculate_top_n = 4  # 根据最后N个rds的用时，加权计算用例用时
        if self.job_deleted:
            return None
        process_time = 0
        rds = apps.get_model('apiv1', 'Rds')
        rds_qs = rds.objects.filter(job=self.id, end_time__isnull=False,
                                    job_assessment_value__in=["0", "1", "-3", "-4", "-5", "-6", "-7", "-2"])
        # 目前服务器中大多数的job并没有运行过rds或rds小于4个，所以用count可以节省查询。日后如果job都有4个以上rds则不需要count
        count = rds_qs.count()
        if count == 0:
            return None
        elif count < calculate_top_n:
            # 对于不足4个情况，直接聚合得到均值
            qs = rds_qs.aggregate(time=Avg(F('end_time') - F('start_time')))
            return round(qs.get("time").total_seconds())
        # 对于大于4个情况，需要计算加权均值，临近的rds时间权重较大，这个无法用到数据库的聚合函数，效率较低
        qs = rds_qs.order_by("-end_time").values("end_time", "start_time")
        qs_top4 = qs[:calculate_top_n]
        total_rate = 1 / sum(range(1, calculate_top_n + 1))
        for index, rds in enumerate(qs_top4):
            process_time += (rds.get("end_time") - rds.get("start_time")).total_seconds() * (
                    calculate_top_n - index) * total_rate
        return round(process_time)

    @property
    def max_process_time(self):
        sample_num = 4
        if self.job_deleted:
            return None
        Rds = apps.get_model('apiv1', 'Rds')
        rds_queryset = Rds.objects.filter(
            job=self, job_assessment_value__in=['0', '1'], end_time__gt=F('start_time')
        ).exclude(end_time=None).order_by('-end_time')[:sample_num]
        result = rds_queryset.annotate(
            time=F('end_time') - F('start_time')
        ).aggregate(Max('time')).get('time__max', None)
        if not result:
            return None
        return result.seconds

    # def save(self, force_insert=False, force_update=False, using=None,
    #          update_fields=None):
    #     # self.complexity = self.set_complexity()
    #     return super(Job, self).save(force_insert=False, force_update=False, using=None,
    #                                  update_fields=None)

    @property
    # job 最近被使用的开始时间
    def recently_used_time(self, in_str=True):
        # job --> rds  1:n
        # 一个job可以测多次产生多个rds，rds记录开始和结束时间，则可以算出job最近被使用的时间
        rds_model = apps.get_model('apiv1', 'Rds')
        try:
            rds = rds_model.objects.filter(job_id=self.id). \
                exclude(tboard__author__username='AITester'). \
                latest('start_time')
        except rds_model.DoesNotExist:
            return None
        local_recently_used_time = timezone.localtime(rds.start_time)
        if in_str:
            return timezone.datetime.strftime(local_recently_used_time,
                                              settings.REST_FRAMEWORK['DATETIME_FORMAT'])
        else:
            return local_recently_used_time

    @property
    # job 最先被使用的的开始时间
    def earliest_used_time(self, in_str=True):
        # job --> rds  1:n
        # 一个job可以测多次产生多个rds，rds记录开始和结束时间，则可以算出job最先被使用的时间
        rds_model = apps.get_model('apiv1', 'Rds')
        try:
            rds = rds_model.objects.filter(job_id=self.id). \
                exclude(tboard__author__username='AITester'). \
                earliest('start_time')
        except rds_model.DoesNotExist:
            return None
        local_earliest_used_time = timezone.localtime(rds.start_time)
        if in_str:
            return timezone.datetime.strftime(local_earliest_used_time,
                                              settings.REST_FRAMEWORK['DATETIME_FORMAT'])
        else:
            return local_earliest_used_time

    def __str__(self):
        return self.job_name + "----" + self.author.username


class JobParameter(AbsDescribe):
    from apiv1.module.tboard.models import TBoard

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='job_parameter', verbose_name='用例')
    tboard = models.ForeignKey(TBoard, blank=True, null=True, on_delete=models.CASCADE, related_name="job_parameter",
                               verbose_name="任务关联")
    parameter = JSONField(blank=True, null=True, verbose_name='job参数')


class JobFlow(models.Model):
    name = models.CharField(max_length=100, verbose_name='用例执行流名称')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='job_flow', verbose_name='用例')
    flow_type = models.CharField(
        max_length=10,
        choices=(
            (NORMAL_JOB_FLOW, NORMAL_JOB_FLOW),
            (INNER_JOB_FLOW, INNER_JOB_FLOW),
        ),
        verbose_name='用例执行流类型'
    )
    ui_json_file = models.FileField(upload_to='ui_json_file', verbose_name='用例执行流文件')
    # to_flow_id: inner flow id
    inner_flow = models.ManyToManyField('self', related_name='job_flow', symmetrical=False, blank=True)
    order = models.IntegerField(verbose_name='用例执行流顺序')
    description = models.TextField(blank=True, verbose_name='用例执行流描述')

    objects = models.Manager()
    custom_objects = JobFlowManager()

    class Meta:
        unique_together = (('job', 'name'), ('job', 'order'))
        verbose_name_plural = "用例执行流"

    def save(self, **kwargs):
        if self.flow_type == 'InnerFlow':
            # innerflow对应关联innerjob
            if self.job.job_type != 'InnerJob':
                raise ValidationError('inner_flow should related inner_job')

            # inner_flow: inner_job = 1:1
            job_relatic_flows = list(self.job.job_flow.all().values_list('id', flat=True))
            if job_relatic_flows and job_relatic_flows != [self.id]:
                raise ValidationError('inner_job only allowed one inner_flow')

        super(JobFlow, self).save()
        self.job.complexity = self.job.set_complexity()
        update_time_fields = kwargs.get('update_time_fields', None)
        if update_time_fields is not None and update_time_fields is False:
            # 导入用例不更新 job的update_time 字段
            self.job.save(update_fields=['complexity'])
        else:
            self.job.updated_time = timezone.now()
            self.job.save()


class JobResourceFile(models.Model):
    name = models.CharField(max_length=50, verbose_name='用例资源文件名称')
    type = models.CharField(max_length=50, verbose_name='用例资源文件类型')
    file = models.FileField(upload_to='job_resource_file', verbose_name='用例资源文件')
    job_flow = models.ForeignKey(JobFlow, on_delete=models.CASCADE, related_name='job_res_file',
                                 verbose_name='用例执行流', null=True)
    update_time = models.DateTimeField(auto_now=True, verbose_name='用例资源文件最后更新时间')

    def save(self, **kwargs):
        if self.name == 'ui.json':
            return reef_400_response(
                description='资源文件名称不符合规范，请从新命名',
                message=f"upload file: {self.name} file name can't is ui.json")
        super(JobResourceFile, self).save()

    class Meta:
        unique_together = (('job_flow', 'name'),)
        verbose_name_plural = "用例资源文件"


class Unit(models.Model):
    unit_name = models.CharField(max_length=50, unique=True, verbose_name='unit名称')
    unit_content = JSONField(max_length=800, verbose_name='unit的内容')
    type = models.CharField(max_length=50, verbose_name='unit所属类型')
    # 注意这个字段虽然值是12345但是不是直接代表适配12345型柜，其含义如下
    # 1 :通用unit 2：adb用unit 3：旋转机械臂用unit 4：龙门架机械臂用unit 5：摄像头用unit
    # 其与机柜的映射关系暂时如下
    # "Tcab_1": [1, 2], "Tcab_2": [1, 2],"Tcab_3": [1, 2, 3],"Tcab_4": [1, 2, 4], "Tcab_5": [1, 4, 5],
    unit_group = models.SmallIntegerField(default=1, verbose_name='unit所属类型')

    class Meta:
        verbose_name_plural = "用例执行单元"


class Unit_EN(models.Model):
    unit_name = models.CharField(max_length=100, unique=True, verbose_name='unit名称')
    unit_content = JSONField(max_length=800, verbose_name='unit的内容')
    type = models.CharField(max_length=50, verbose_name='unit所属类型')
    # 注意这个字段虽然值是12345但是不是直接代表适配12345型柜，其含义如下
    # 1 :通用unit 2：adb用unit 3：旋转机械臂用unit 4：龙门架机械臂用unit 5：摄像头用unit
    # 其与机柜的映射关系暂时如下
    # "Tcab_1": [1, 2], "Tcab_2": [1, 2],"Tcab_3": [1, 2, 3],"Tcab_4": [1, 2, 4], "Tcab_5": [1, 4, 5],
    unit_group = models.SmallIntegerField(default=1, verbose_name='unit所属类型')

    class Meta:
        verbose_name_plural = "用例执行单元"


class TestGather(AbsDescribe):
    name = models.CharField(max_length=150, unique=True, verbose_name='测试集名称')
    job_count = models.IntegerField(default=0, verbose_name='job数量')
    duration_time = models.BigIntegerField(default=0, verbose_name='预计耗时')
    cabinet_version = JSONField(null=True, blank=True, verbose_name='用例所属机柜类型')
    job = models.ManyToManyField(
        Job,
        related_name='testgather',
        verbose_name='关联job'
    )


class TestProject(AbsDescribe):
    name = models.CharField(max_length=150, unique=True, verbose_name='项目名称')
    test_gather = models.ManyToManyField(
        TestGather,
        through='TestGatherShip',
        related_name='testproject',
        verbose_name='关联测试集'
    )

    @property
    def test_gather_count(self):
        return len(self.test_gather.all())

    class Meta:
        verbose_name_plural = '测试项目'


class TestGatherShip(models.Model):
    gather = models.ForeignKey(
        TestGather,
        on_delete=models.CASCADE,
        related_name='testgathership'
    )
    project = models.ForeignKey(
        TestProject,
        on_delete=models.CASCADE,
        related_name='testgathership'
    )

    class Meta:
        verbose_name_plural = '测试集项目关联'
        unique_together = ['gather', 'project']
