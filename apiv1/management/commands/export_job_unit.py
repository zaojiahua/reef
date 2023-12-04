import json
import os

from django.core.management import BaseCommand, CommandParser
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from apiv1.core.utils import yn_prompt
from apiv1.module.job.models import Unit

DEFAULT_PATH = "job.units"


class UnitSerializer(ModelSerializer):
    unit_name = serializers.CharField(max_length=50, allow_blank=True)
    type = serializers.CharField(max_length=50, allow_blank=True)

    class Meta:
        model = Unit
        fields = ("unit_name", "unit_content", "type")


class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser):
        parser.add_argument("-f", "--file",
                            help="指定的文件输出路径",
                            default=DEFAULT_PATH)
        parser.add_argument("-n", "--noinput",
                            help="强制所有选项按默认模式进行，不会再提示询问任何事情，"
                                 "若您使用脚本执行，建议启用该选项",
                            action="store_true",
                            default=False)
        parser.add_argument("-o", "--stdoutput",
                            help="输出到标准输出流而非档案",
                            action="store_true",
                            default=False)

    def handle(self, *args, **options):
        path = DEFAULT_PATH if "file" not in options else options.get("file")
        noinput = options.get("noinput")
        stdoutput = options.get("stdoutput")

        if os.path.exists(path) and not noinput:
            yn = yn_prompt(f"档案 {path} 已存在，是否覆盖?")
            if not yn:
                return

        units = Unit.objects.all().order_by("id")
        serialized_data = UnitSerializer(instance=units, many=True).data

        if stdoutput:
            print(json.dumps(serialized_data))
        else:
            with open(path, "w") as f:
                f.write(json.dumps(serialized_data))
