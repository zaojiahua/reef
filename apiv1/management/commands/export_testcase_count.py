import os
from collections import namedtuple
from concurrent.futures import ProcessPoolExecutor
from importlib import import_module
from typing import List
from unittest import TestSuite

from django.core.management import BaseCommand, CommandParser
from django.db import DatabaseError
from django.test.runner import DiscoverRunner

from reef import settings

TCInfo = namedtuple("TCInfo", ("module", "klass", "method"))  # TestCase Information
DEFAULT_PATH = "testcase_count.txt"
settings.ENABLE_TCCOUNTER = True


class Command(BaseCommand):
    """
    export_testcase_count命令需配合装饰器apiv1.core.test.tccounter使用
    统计tccounter标注的单元测试，输出统计结果（每只API的单元测试用例数量）
    """
    def add_arguments(self, parser: CommandParser):
        parser.add_argument("-f", "--file",
                            help="指定的文件输出路径",
                            default=DEFAULT_PATH)
        parser.add_argument("-n", "--noinput",
                            help="强制所有选项按默认模式进行，不会再提示询问任何事情，"
                                 "若您使用脚本执行，建议启用该选项",
                            action="store_true",
                            default=False)
        parser.add_argument("-m", "--multiprocess",
                            help="以多进程模式执行",
                            default="")

    def handle(self, *args, **options):
        # 输入选项处理
        path: str = options.get("file")
        noinput: bool = options.get("noinput")
        multiprocess: int = int(options.get("multiprocess")) if options.get("multiprocess") else 0

        # 若档案存在则确认是否覆盖
        if not noinput and os.path.exists(path):
            while True:
                yn = input(f"档案 {os.path.abspath(path)} 已存在, 覆盖它吗? [Y/n]").lower()
                if yn == "n":
                    return
                elif yn in ("y", ""):
                    break
                else:
                    continue

        tcis = self._get_all_testcase()  # TestCase Informations

        # 计算单元测试用例数量
        if multiprocess > 1:  # 多进程模式
            with ProcessPoolExecutor(multiprocess) as pool:
                data = []
                for i in range(multiprocess):
                    data.append(tcis[i::multiprocess])
                gen = pool.map(self._count_testcase_in_process, data)
        else:  # 单进程模式
            gen = [self._count_testcase(tcis)]

        # 合并来自各进程的执行结果
        hadshown, list_ = set(), []
        for viewnames in gen:  # type: dict
            for k, v in viewnames.items():  # type: str, int
                if k not in hadshown:
                    list_.append([k, v])
                    hadshown.add(k)
                    continue

                for l in list_:
                    if l[0] == k:
                        l[1] += v
                        break

        # 将viewname按照字母排序
        list_.sort(key=lambda t: t[0])

        # 将统计出来的单元测试数量写入档案
        with open(path, "w+") as file:
            for tc, count in list_:  # type: str, int
                file.write(f"{tc},{count}\n")

    @staticmethod
    def _get_all_testcase() -> List[TCInfo]:
        runner = DiscoverRunner()
        suite: TestSuite = runner.build_suite()

        # noinspection PyProtectedMember,PyUnresolvedReferences
        tcis: List[TCInfo] = [TCInfo(tc.__module__, tc.__class__.__name__, tc._testMethodName) for tc in suite]
        return tcis

    @staticmethod
    def _count_testcase(tcis: List[TCInfo]) -> dict:
        dic = {}
        for tci in tcis:  # type: TCInfo
            """
            将输入的TCI转换成function并呼叫
            """
            try:
                func = getattr(getattr(import_module(tci.module), tci.klass), tci.method)
                viewname, method = func()
                key = f"{viewname},{method}"
                if key not in dic:
                    dic[key] = 0
                dic[key] += 1
            except (AttributeError, DatabaseError, TypeError, ImportError) as e:
                print(f"=====================\n"
                      f"执行下列用例时时发生错误, "
                      f"是否忘记在测试用例上添加装饰器@tccounter(VIEWNAME, HTTP_METHOD, COUNT_TESTCASE)?:\n"
                      f"{tci.module}.{tci.klass}.{tci.method}\n"
                      f"Error: {e}\n")
                continue
        return dic

    @staticmethod
    def _count_testcase_in_process(tcis: List[TCInfo]) -> dict:
        import django
        django.setup()
        return Command._count_testcase(tcis)
