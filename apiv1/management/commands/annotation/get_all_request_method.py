import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reef.settings")
import django

django.setup()
from apiv1.management.commands.annotation.get_all_view_name import get_all_url_dict
import importlib, yaml, platform

# 当前路径
current_path = os.path.abspath(os.path.dirname(__file__))
# 项目所在路径
project_path = os.getcwd()
def get_all_request_method():
    module_view_dict = {}
    file_path = os.path.join(project_path, 'apiv1','module')
    module_lists = os.listdir(file_path)
    for module in module_lists:
        if os.path.isdir(os.path.join(file_path, module)) and module != '__pycache__':
            module_path =  'apiv1.module.' + module
            module = os.path.join(os.sep, 'apiv1','module',module)
            module_view_dict[module] = {}
            # 获取模块下的所有View_name和ViewClass
            view_name_dict = get_all_url_dict(module_path + '.urls')
            for view_name in view_name_dict:
                if 'api-root' == view_name:
                    continue

                view_class = view_name_dict[view_name]['view_class']
                the_class = from_class(view_class)
                # 截取非通用接口
                if 'ViewSet' not in view_class:
                    methods = dir(the_class)
                    for method in methods:
                        if 'post' == method or 'get' == method or 'put' == method or 'patch' == method or 'delete' == method:
                            module_view_dict[module][method + ':' + view_name] = 0
                else:
                    for def_view_class in dir(the_class):
                        if '_list' in view_name:
                            if 'create' == def_view_class:
                                module_view_dict[module]['post:' + view_name] = 0
                            elif 'bulk_creat' == def_view_class:
                                module_view_dict[module]['post:' + view_name] = 0
                            if 'list' == def_view_class:
                                module_view_dict[module]['get:' + view_name] = 0
                            if 'bulk_delete' == def_view_class:
                                module_view_dict[module]['delete:' + view_name] = 0
                        elif '_detail' in view_name:
                            if 'retrieve' == def_view_class:
                                module_view_dict[module]['get:' + view_name] = 0
                            if 'update' == def_view_class:
                                module_view_dict[module]['put:' + view_name] = 0
                            if 'partial_update' == def_view_class:
                                module_view_dict[module]['patch:' + view_name] = 0
                            if 'destroy' == def_view_class:
                                module_view_dict[module]['delete:' + view_name] = 0
                        else:
                            if 'bulk_delete' in def_view_class:
                                module_view_dict[module]['delete:' + view_name] = 0

    leader_module_dict = {}
    with open(os.path.join(current_path, 'persons_for_unittest_list.yaml'), 'rb') as f:
        temp = yaml.load(f, Loader=yaml.FullLoader)
    for leader, paths in temp.items():
        leader_module_dict[leader] = {}
        for modules in paths:
            for module_path in paths[modules]:
                if platform.system() == 'Linux':
                    module_path = module_path.replace("\\", "/")
                leader_module_dict[leader][module_path] = {}
                if module_path in module_view_dict.keys():
                    leader_module_dict[leader][module_path] = module_view_dict[module_path]
    return leader_module_dict


# apiv1.module.system.viewset.DynamicSystemViewSet
# 自定义导入模块 eg: from apiv1.module.system.viewset import DynamicSystemViewSet
def from_class(cclass):
    vieww = cclass.split('.')[-1]
    ffrom = cclass.replace('.' + vieww, '')
    o = importlib.import_module(ffrom)
    the_class = getattr(o, vieww)
    return the_class
