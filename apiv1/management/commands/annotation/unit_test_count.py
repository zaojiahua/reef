import os
from apiv1.management.commands.annotation import write_in_xls
import xlrd
from xlutils.copy import copy as xl_copy
from apiv1.management.commands.annotation.get_all_request_method import get_all_request_method

def write_file(book_name_xls, sheet_name_xls, value_title):
    # 当前路径
    current_path = os.path.abspath(os.path.dirname(__file__))
    # unit_test_count.txt保存的是unit test的全部API
    fileDir = os.path.join(current_path, "unit_test_count.txt")
    os.system('python manage.py export_testcase_count -n -m=4 -f='+fileDir)
    test_title = []
    with open(fileDir, 'r', encoding='utf-8') as f:
        views_name = get_all_request_method()
        file_list = f.read().replace('\n',';').split(';')
        # 计算test中每只API测试的数量
        test_number_dict = {}
        for view_information in file_list:
            if len(view_information) == 0:
                continue
            view_information_list = view_information.split(',')
            test_count = view_information_list[-1]
            view_name_http = view_information_list[1]+':'+view_information_list[0]
            test_number_dict[view_name_http] = test_count
            for key in views_name:
                for module in views_name[key]:
                    if view_name_http in views_name[key][module].keys():
                        views_name[key][module][view_name_http]=int(test_count)

        """
        将数据存入表格中，要求格式为 
        value1 = [["张三", "男", "19", "杭州", "研发工程师"],
                  ["李四", "男", "22", "北京", "医生"],
                  ["王五", "女", "33", "珠海", "出租车司机"], ]
        """
        for leader in views_name:
            for module1 in views_name[leader]:
                # 对unit test count进行排序
                aa = dict(sorted(views_name[leader][module1].items(), key=lambda x: x[1]))
                views_name[leader][module1] = aa
                for dd in views_name[leader][module1]:
                    # 创建list，将要添加到表格里的数据存入list
                    list_ff = []
                    cc = dd.split(':')
                    list_ff.extend((leader, module1, cc[0], cc[1], views_name[leader][module1][dd]))
                    # 集合list
                    value_title.append(list_ff)
                    test_title.append(list_ff)

        if not os.path.exists(book_name_xls):
            # 创建表格
            write_in_xls.write_excel_xls(book_name_xls, sheet_name_xls, value_title)
            # 将数据存入表格
            write_in_xls.write_excel_xls_append(book_name_xls, test_title, sheet_name_xls)

        else:
            rb = xlrd.open_workbook(book_name_xls, formatting_info=True)
            # make a copy of it
            wb = xl_copy(rb)
            # add sheet to workbook with existing sheets
            wb.add_sheet(sheet_name_xls)
            wb.save(book_name_xls)
            # 将数据存入表格
            write_in_xls.write_excel_xls_append(book_name_xls, value_title, sheet_name_xls)
