import copy
import ftplib
import os
import zipfile

from django.db.models import ManyToManyRel, ManyToOneRel, OneToOneRel, OneToOneField
from django.db.models.fields.related import RelatedField

from apiv1.core.constants import JOB_TYPE_INNER_JOB
from apiv1.core.response import reef_400_response
from reef.settings import JOB_RES_FILE_EXPORT_PATH


class Checkout:

    class CheckoutZipFile:

        def __init__(self, job_list):
            self.job_list = job_list
            self.correct_list = []
            self.error_list = []

        def get_job_zip_file_path(self):
            # job 列表不做去重处理。job选取多次此信息，返给前端,用于执行多次此job.
            for job in self.job_list:
                zip_path_list = [job]
                inner_job_label_list = list(set([
                    inner_flow.job
                    for job_flow in job.job_flow.all()
                    for inner_flow in job_flow.inner_flow.all()
                ]))
                zip_path_list.extend(inner_job_label_list)
                error_exists = self.is_exist(zip_path_list)
                if not error_exists:
                    # job and inner_job zip file not have error
                    self.correct_list.append(job)

        def is_exist(self, zip_path_list):
            error_exists = False
            for job in zip_path_list:
                if not os.path.exists(os.path.join(JOB_RES_FILE_EXPORT_PATH, f'{job.job_label}.zip')):
                    self.error_list.append(job)
                    error_exists = True
                else:
                    # zip is empty
                    try:
                        with zipfile.ZipFile(
                                os.path.join(JOB_RES_FILE_EXPORT_PATH, f'{job.job_label}.zip'), 'r'
                         ) as z:
                            if not z.namelist():
                                self.error_list.append(job)
                                error_exists = True
                    except Exception as e:
                        self.error_list.append(job)
            return error_exists

        def error_job_set(self):
            # job error execute set
            # 避免页面同一job显示多次
            self.error_list = list(set(self.error_list))

    def checkout_zip_file(self, job_list):
        checkout_zip_file = self.CheckoutZipFile(job_list=job_list)
        checkout_zip_file.get_job_zip_file_path()
        checkout_zip_file.error_job_set()
        return checkout_zip_file.correct_list, checkout_zip_file.error_list


def explain_abnormity_policy(abnormity_policy: object):
    """
    policy format
    {
        type: ..... (通用)
        value: .....
    }

    """
    rule = abnormity_policy.policy_rule
    type = rule.get('type', None)
    result = None
    if type == 'power_leave':
        result = rule.get('value', None)

    return result


class CleanObjRelated:

    def __init__(self, obj, clean_fields_list):
        self.obj = obj
        self.clean_fields_list = clean_fields_list
        self.fail_list = []

    def clean_obj_field(self):
        field_obj_dict = {
            (
             field_obj.attname.split('_')[0]
             if field_obj.attname.endswith('_id') else field_obj.attname
            ): field_obj
            for field_obj in self.obj._meta.fields
        }
        for field in self.clean_fields_list:
            if field in field_obj_dict.keys():
                # clean obj OneToOneField
                if isinstance(field_obj_dict[field], OneToOneField):
                    obj_specific_field = getattr(self.obj, field, None)
                    if obj_specific_field:
                        obj_specific_field.delete()
                setattr(self.obj, field, None)
                self.obj.save()

    def handle_related_field(self):
        # obj related
        related_objects = self.obj._meta.related_objects
        for item in related_objects:
            if not hasattr(item, 'field'):
                self.fail_list.append(f'related_{item.name}')
                continue
            if isinstance(item, ManyToManyRel) and item.related_name in self.clean_fields_list:
                related_obj = getattr(self.obj, f'{item.name}', None)
                if related_obj:
                    related_queryset = related_obj.model.objects.filter(**{item.field.attname: self.obj})
                    related_obj.remove(*related_queryset)
            elif isinstance(item, ManyToOneRel) and item.related_name in self.clean_fields_list:
                # 判断外键null属性,是否允许为None
                if item.field.null:
                    filter_data: dict = {item.field.attname: None}
                    item.related_model.objects.filter(**{item.field.attname: self.obj}).update(**filter_data)
            elif isinstance(item, OneToOneRel) and item.related_name in self.clean_fields_list:
                if item.field.null:
                    filter_data: dict = {item.field.attname: None}
                    item.related_model.objects.filter(**{item.field.attname: self.obj}).update(**filter_data)
            else:
                pass

    def clean(self):
        self.clean_obj_field()
        self.handle_related_field()
        return self.fail_list


class Prototype:

    def __init__(self):
        self.object = {}

    def register(self, key, obj):
        self.object[key] = obj

    def unregister(self, key):
        del self.object[key]

    def clone(self, key, **kwargs):
        obj = self.object.get(key, None)
        if not obj:
            raise reef_400_response(message=f'incorrect object identifier:{key}')
        obj_copy = copy.deepcopy(obj)
        obj_copy.__dict__.update(**kwargs)
        return obj_copy


class ReefFTP:

    def __init__(self, ip, user, passwd, port=21):
        self.ftp_ip = ip
        self.ftp_user = user
        self.ftp_passwd = passwd
        self.ftp_port = port
        self.ftp = None

    def __call__(self, *args, **kwargs):
        ftp = ftplib.FTP()
        # 连接ftp
        ftp.connect(self.ftp_ip, self.ftp_port)
        # ftp登录
        ftp.login(self.ftp_user, self.ftp_passwd)
        self.ftp = ftp
        return self

    def quit(self):
        self.ftp.quit()

    def ftp_path_exist(self, ftp_path):
        try:
            self.ftp.cwd(ftp_path)
        except Exception as e:
            raise ftplib.error_perm(e)

    def download_file(self, ftp_file_name, local_file_name):
        try:
            file_handle = open(local_file_name, "wb").write  # 以写模式在本地打开文件
            self.ftp.retrbinary("RETR " + ftp_file_name, file_handle)
        except Exception as e:
            raise f"ftp file download fail: {e}"

    def download_dir_files(self, ftp_path, local_path):
        # check path
        self.ftp_path_exist(ftp_path)
        # 进入指定目录 是否以/结尾不影响进入指定目录
        self.ftp.cwd(ftp_path)
        # 区分文件和文件夹
        dirs = []
        self.ftp.dir(".", dirs.append)
        for i in dirs:
            try:
                if '<DIR>' in i:
                    # 目录跳过
                    continue
                else:
                    ftp_file_name = i.split(' ')[-1]
                    if not local_path.endswith('/'):
                        local_file_name = os.path.join(local_path, ftp_file_name)
                    else:
                        local_file_name = local_path + ftp_file_name
                    self.download_file(ftp_file_name, local_file_name)
            except Exception as e:
                raise f"ftp file download fail: {e}"

        # 退出当前目录
        self.ftp.cwd("..")
        self.quit()