# -*- coding: utf-8 -*-
import os, yaml, re, operator, platform
from apiv1.management.commands.annotation import write_in_xls

"""   
本程序通过计算python源码中"注释的行数",检查源码是否合格
1.本程序可对"#"开头的注释,以及 成对的"三双引号"源码进行计数
2.本程序使用了正则匹配
3.注释占源码比例 = 源码内注释行数/源码代码行数+注释行数
"""
def annotation_rate(book_name_xls, sheet_name_xls, value_title):
    # 当前路径
    current_path = os.path.abspath(os.path.dirname(__file__))
    # 项目所在路径
    project_path = os.getcwd()
    with open(os.path.join(current_path, 'persons_list.yaml'), 'rb') as f:
        temp = yaml.load(f, Loader=yaml.FullLoader)
    annotation_rate_path = os.path.join(current_path, 'persons.txt')
    if os.path.exists(annotation_rate_path):
        os.remove(annotation_rate_path)

    annotation_title = []
    for key, paths in temp.items():
        file_dict = {}
        file_list = []
        file_list.append(key)
        #同一人名下module的总注释率
        total_exp_rate = 0
        #同一人名下的module文件总数
        file_total = 0
        #平均注释率
        agv = 0
        total_dict = {}
        for path in paths['modules']:
            if platform.system() == 'Linux' :
                path = path.replace("\\", "/")
            root_path = project_path + path
            for root, dirs, files in os.walk(root_path):
                for afile in files:
                    if re.match(r".*py$", afile):
                        fileDir = os.path.join(root, afile)
                        commentLines = 0
                        whiteLines = 0
                        normal = 0
                        comment = False
                        lines = open(fileDir, 'r', encoding='utf-8')
                        for line in  lines:
                            line = line.strip()
                            # 空行
                            if (line == ''):
                                whiteLines = whiteLines + 1
                            # 注释 """  """
                            elif re.findall(r"(.*\"\"\".*)(.*\"\"\".*)", line):
                                commentLines = commentLines + 1
                            # 注释 """ 开头
                            elif (re.match(r".*\"\"\".*", line) and  False == comment):
                                commentLines = commentLines + 1
                                comment = True
                            # 注释 中间 和 """ 结尾
                            elif (True == comment):
                                commentLines = commentLines + 1
                                if re.match(r".*\"\"\".*", line):
                                    comment = False
                            # 注释 #
                            elif re.search(r"\s*#+.*", line):
                                commentLines = commentLines + 1
                            # 代码
                            else:
                                normal = normal + 1

                        if normal==0 and commentLines == 0:
                            continue
                        ann = float('%.2f' % (100 * (commentLines / (normal+commentLines))))
                        total = normal + commentLines

                        file_AP = fileDir.replace(project_path, '')
                        file_dict[file_AP] = ann
                        total_dict[file_AP] = total
                        total_exp_rate += ann
                        file_total += 1

        if file_total != 0:
            agv = '%.2f%%' % (total_exp_rate / file_total)
        sort_files = sorted(file_dict.items(), key=operator.itemgetter(1))
        for sort_file in sort_files:
            #创建list，将要添加到表格里的数据存入list
            list_ff = []
            list_ff.extend((key, agv, sort_file[0], total_dict[sort_file[0]], '%.2f%%' % sort_file[1]))
            #集合list
            annotation_title.append(list_ff)

    #创建表格
    write_in_xls.write_excel_xls(book_name_xls, sheet_name_xls, value_title)
    #将数据存入表格
    write_in_xls.write_excel_xls_append(book_name_xls, annotation_title, sheet_name_xls)