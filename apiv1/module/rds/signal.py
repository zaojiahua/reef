from django.apps import apps
from django.db import connection
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver


def _rds_update_field(instance):
    rds_cls = apps.get_model("apiv1", "Rds")

    # rds field "created_by_ai_tester"
    if instance.tboard is None or instance.tboard.author is None:
        instance.created_by_ai_tester = False
    else:
        instance.created_by_ai_tester = (instance.tboard.author.username == 'AITester')

    # rds field "created_by_sys_job"
    if instance.job is None:
        instance.created_by_sys_job = False
    instance.created_by_sys_job = (instance.job.job_type == 'Sysjob')

    with connection.cursor() as sql:
        sql.execute(
            f"UPDATE apiv1_rds SET created_by_ai_tester = '{instance.created_by_ai_tester}',"
            f"created_by_sys_job = '{instance.created_by_sys_job}' WHERE id = {instance.id}"
        )

    return


def _update_tboard_success_ratio(instance, flag=''):
    rds_cls = apps.get_model("apiv1", "Rds")
    tboard_cls = apps.get_model("apiv1", "TBoard")

    success = rds_cls.objects.filter(tboard=instance.tboard_id, end_time__isnull=False).filter(job_assessment_value='0').count()
    total = rds_cls.objects.filter(tboard=instance.tboard_id, end_time__isnull=False).count()
    # create/after_modify total+1   if job_assessment_value=0 suc+1
    if flag == 'created' or flag == 'after_modify' or flag == 'changed_end_time_value' or flag == 'changed_job_assessment_and_end_time_value':
        if instance.end_time != None:
            total += 1
            if instance.job_assessment_value == '0':
                success += 1

    # deleted/before_modify total+1  if job_assessment_value=0 suc-1
    if flag == 'deleted' or flag == 'before_modify':
        if instance.end_time != None:
            total -= 1
            if instance.job_assessment_value == '0':
                success -= 1

    if flag == 'changed_job_assessment_value':
        old_rds = rds_cls.objects.get(id=instance.id)
        if old_rds.end_time != None:
            if old_rds.job_assessment_value == '0':
                if instance.job_assessment_value == '1':  # 0 --> !0   tboard : success - 1
                    success -= 1

            else:
                if instance.job_assessment_value == '0':  # !0  --> 0   tboard : success + 1
                    success += 1

    success_ratio = round(success / total, 3) if total != 0 else 0
    with connection.cursor() as sql:
        sql.execute(f"UPDATE apiv1_tboard SET success_ratio = '{success_ratio}' WHERE id = {instance.tboard_id}")


@receiver(post_save, sender="apiv1.Rds", dispatch_uid='rds_post_save')
def rds_post_save_handler(sender, instance=None, **kwargs):
    _rds_update_field(instance)


@receiver(pre_save, sender="apiv1.Rds", dispatch_uid='rds_pre_save')
def rds_pre_save_handler(sender, instance=None, **kwargs):
    rds_cls = apps.get_model("apiv1", "Rds")

    # rds创建
    if instance.id is None:
        _update_tboard_success_ratio(instance, flag='created')

    # rds与tboard的关联关系改变 eg：rds -->tboard1  change to  rds -->tboard2
    # before_modify：计算的是tboard1关联rds的成功率（改变之前）
    # after_modify： 计算的是tboard2关联rds的成功率（改变之后）
    elif instance.tboard_id != rds_cls.objects.get(id=instance.id).tboard_id:
        _update_tboard_success_ratio(rds_cls.objects.get(id=instance.id), flag='before_modify')
        _update_tboard_success_ratio(instance, flag='after_modify')

    # rds job_assessment_value 字段值发生改变
    elif instance.job_assessment_value != rds_cls.objects.get(id=instance.id).job_assessment_value:
        if instance.end_time != rds_cls.objects.get(id=instance.id).end_time:
            _update_tboard_success_ratio(instance, flag='changed_job_assessment_and_end_time_value')
        else:
            _update_tboard_success_ratio(instance, flag='changed_job_assessment_value')

    elif instance.end_time != rds_cls.objects.get(id=instance.id).end_time:
        _update_tboard_success_ratio(instance, flag='changed_end_time_value')


    # 其它情况不进行操作
    else:
        _update_tboard_success_ratio(instance)


@receiver(pre_delete, sender="apiv1.Rds", dispatch_uid='rds_delete')
def rds_deleted_handler(sender, instance=None, **kwargs):
    # rds删除
    _update_tboard_success_ratio(instance, flag='deleted')

