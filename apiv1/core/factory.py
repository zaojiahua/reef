from apiv1.core.company.coolpad import CoolPadObj
from apiv1.core.utils import ReefLogger


def init_open_module_factory(module_name):
    if module_name == 'coolpad':
        obj = CoolPadObj()
    else:
        # 考虑到外部模块的初始化，会嵌套在TMach系统API中。外部模块的执行都在不影响TMach系统API本身功能下执行，达到解耦的效果
        # 统一对错误进行日志记录而不是response
        logger = ReefLogger('backend')
        logger.error(
            f'Init open module fail, module_name unavailable: \n'
            f'module_name: {module_name} \n'
                     )
        return None
    return obj


def check_func_execute(obj, func_or_attribute, *args, **kwargs):
    if not hasattr(obj, func_or_attribute):
        logger = ReefLogger('backend')
        logger.error(
            f"obj: {obj} Not {func_or_attribute} attribute, That doesn't walk\n"
        )
        return None
    func_or_attribute = getattr(obj, func_or_attribute)
    if not callable(func_or_attribute):
        return func_or_attribute
    else:
        return func_or_attribute(*args, **kwargs)



