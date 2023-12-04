from dingtalkchatbot.chatbot import DingtalkChatbot
from django.apps import apps
from django.db import models

from apiv1.module.device.models import Device
from apiv1.module.job.models import Job
from apiv1.module.system.models import Cabinet
from apiv1.module.user.models import ReefUser
from reef.settings import DINGDINGWEBHOOK


def send_dingding(message, at_mobiles=None):
    if at_mobiles is None:
        at_mobiles = []
    webhook = DINGDINGWEBHOOK
    robort = DingtalkChatbot(webhook)
    robort.send_text(msg=f"上报Bug \n{message}", at_mobiles=at_mobiles)


class Bug(models.Model):
    reporter = models.ForeignKey(ReefUser, on_delete=models.SET_NULL, related_name="bug_reporter", null=True,
                                 verbose_name="上报人")
    cabinet = models.ForeignKey(Cabinet, on_delete=models.SET_NULL, null=True, related_name="bug", verbose_name="机柜编号",
                                blank=True)
    device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, related_name="bug", verbose_name="使用设备",
                               blank=True,
                               help_text="idle&busy设备显示备注名，offline设备显示devicelabel")
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, related_name="bug", verbose_name="使用用例",
                            blank=True)
    description = models.TextField(verbose_name="bug 描述",
                                   help_text="请用文字描述发生的问题,如异常请写出错误码和对应错误的unit,如果是页面异常请描述对应页面异常位置")
    happened_time = models.DateTimeField(verbose_name="发生时间")
    status = models.CharField(max_length=50, choices=(("未处理", "未处理"), ("已解决", "已解决")), default="未处理")
    level = models.CharField(max_length=50, choices=(("1级", "1级"), ("2级", "2级"), ("3级", "3级"), ("4级", "4级")),
                             default="4级")

    class Meta:
        verbose_name = "Bug上报"
        verbose_name_plural = verbose_name

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self._send_message()
        return super().save(force_insert=False, force_update=False, using=None,
                            update_fields=None)

    def _send_message(self):
        Cabinet = apps.get_model("apiv1", "Cabinet")
        try:
            cabinet = Cabinet.objects.get(id=138)
            system_id = cabinet.ip_address.split(".")[-2]
        except Cabinet.DoesNotExist:
            system_id = "未知"
        if self.status != "已解决":
            message = f"------------{system_id}系统------------\n" \
                      f"等级:[{self.level}]\n" \
                      f"设备: [{self.device}]\n" \
                      f"用例:  [{self.job}]\n" \
                      f"报告人: [{self.reporter}]\n" \
                      f"详情: [{self.description}]\n"
            from concurrent.futures import ThreadPoolExecutor
            ThreadPoolExecutor().submit(send_dingding, message)
