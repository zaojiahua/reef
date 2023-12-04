import json
import os
from collections import OrderedDict
from json import JSONDecodeError
from typing import List

from django.core.management import BaseCommand, CommandParser
from django.db import transaction, IntegrityError

from apiv1.management.commands import export_job_unit
from apiv1.module.job.models import Unit


class Command(BaseCommand):

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("-f", "--file",
                            help="指定的文件输入路径",
                            default=export_job_unit.DEFAULT_PATH)
        parser.add_argument("--force",
                            help="强制导入Job Unit。 注意: 使用此选项将会覆盖冲突的Job Unit!",
                            action="store_true",
                            default=False)

    def handle(self, *args, **options):
        path = export_job_unit.DEFAULT_PATH if "file" not in options \
            else options.get("file")
        force = options.get("force")

        if not os.path.exists(path):
            print(f"File {path} not exist!")
            return
        with open(path, "r") as f:
            data = f.read()
            try:
                data = json.loads(data)
            except JSONDecodeError as e:
                print("档案解析失败!")
                return
            print(f"Loading data...\n {data}")
            serializer = export_job_unit.UnitSerializer(data=data, many=True)

        if not serializer.is_valid():
            print("Data deserialize error!")
            print(serializer.errors)
            return

        try:
            if force:
                self._import_job_force(serializer.validated_data)
            else:
                self._import_job(serializer.validated_data)

        except IntegrityError as e:
            print("导入资料错误，有可能是因为资料冲突造成，考虑使用 --force")

    @staticmethod
    def _import_job(data: List[OrderedDict]):
        with transaction.atomic():
            for unit in data:
                Unit.objects.create(
                    **unit
                )

    @staticmethod
    def _import_job_force(data: List[OrderedDict]):
        with transaction.atomic():
            for unit in data:
                Unit.objects.update_or_create(
                    defaults=unit,
                    unit_name=unit.get("unit_name")
                )
