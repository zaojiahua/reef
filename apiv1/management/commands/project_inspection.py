from apiv1.management.commands.annotation.annotation_rate import annotation_rate
from apiv1.management.commands.annotation.unit_test_count import write_file
from django.core.management.base import BaseCommand, CommandParser

DEFAULT_PATH = "项目质量报告.xls"

class Command(BaseCommand):

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("-f", "--file",
                            help="指定的文件输出路径",
                            default=DEFAULT_PATH)

    def handle(self, **options):
        book_name_xls: str = options.get("file")
        #表名称
        annotation_sheet_name_xls = '检测代码注释率'
        #指定字段
        annotation_title = [["负责人", "平均注释率", "文件名称", "总行数","各文件注释率"], ]
        annotation_rate(book_name_xls, annotation_sheet_name_xls, annotation_title)
        # 表名称
        test_sheet_name_xls = '检测单元测试率'
        # 指定字段
        test_title = [["负责人", "模块", "REQUEST_METHOD", "unit test count", "数量"]]
        write_file(book_name_xls, test_sheet_name_xls, test_title)