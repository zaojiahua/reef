from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from apiv1.module.device.models import PhoneModel, AndroidVersion
from apiv1.module.job.models import Job
from reef.settings import ENABLE_TCCOUNTER


class TestUnionJob(APITestCase):
    def setUp(self):
        self.url = reverse('union_job')
        self.default_data = TestTool.load_default_data()

    @tccounter("union_job", "get", ENABLE_TCCOUNTER)
    def test200ok(self):
        """
        Date: 2018/12/25
        Author: Raymond
        Base test case
        """
        response = self.client.get(
            self.url
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("union_job", "get", ENABLE_TCCOUNTER)
    def test_phone_model_name_param(self):
        """
        Date: 2018/12/25
        Author: Raymond
        UnionJob support query param phone_model_name(a reef list) to filter job
        phone_model_name means Job.phone_models.phone_model_name
        key is phone_model_name__in
        """
        phone_model_name = self.default_data['phone_model'].phone_model_name
        response = self.client.get(
            self.url + f'?phone_model_name__in=ReefList[{phone_model_name}{{%,%}}model2]'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertGreater(len(response.data['jobs']), 0)

    @tccounter("union_job", "get", ENABLE_TCCOUNTER)
    def test_phone_model_name_param_format(self):
        """
        Date: 2018/12/26
        Author: Raymond
        phone_model_name param accept only ReefList format list, if format is wrong
        return 400 Bad request
        """
        phone_model_name = self.default_data['phone_model'].phone_model_name
        response = self.client.get(
            self.url + f'?phone_model_name__in={phone_model_name},name2'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("union_job", "get", ENABLE_TCCOUNTER)
    def test_android_version_param(self):
        """
        Date: 2018/12/25
        Author: Raymond
        UnionJob support query param android_version(a reef list) to filter job
        android_version means Job.android_version.version
        key is android_version__version__in
        """
        android_version = self.default_data['android_version'].version
        response = self.client.get(
            self.url + f'?android_version__version__in=ReefList[{android_version}{{%,%}}version2]'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertGreater(len(response.data['jobs']), 0)

    @tccounter("union_job", "get", ENABLE_TCCOUNTER)
    def test_android_version_param_format(self):
        """
        Date: 2018/12/26
        Author: Raymond
        android_version param accept only ReefList format list, if format is wrong
        return 400 Bad request
        """
        android_version = self.default_data['android_version'].version
        response = self.client.get(
            self.url + f'?android_version__version__in={android_version},version2'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("union_job", "get", ENABLE_TCCOUNTER)
    def test_union_job(self):
        """
        Date: 2018/12/27
        Author: Raymond
        This api support union filter between android_version.version
        and phone_model.phone_model_name
        In this case
        phone_model_name filter should return job 1,2,3,4
        android_version filter should return job 3,4,5,6
        and in the end.
        API should return there union set 1,2,3,4,5,6
        """
        # create 9 jobs with job_label 1~9
        jobs = [Job.objects.create(
            job_label=f'{i}',
            job_name=f'{i}',
            description='',
            author=self.default_data['user']
        ) for i in range(1, 10)]

        # create phone_models 1~2
        phone_models = [PhoneModel.objects.create(
            phone_model_name=f'phone_model_name__{i}',
            manufacturer=self.default_data['manufacturer'],
            cpu_name='Intel Core i7 8650 U'
        ) for i in range(1, 3)]

        # create android_versions 1~2
        android_versions = [AndroidVersion.objects.create(
            version=f'version__{i}',
        ) for i in range(1, 3)]

        # add phone_model 1 to job 1~2
        [jobs[i].phone_models.add(phone_models[0])
         for i in range(0, 2)]

        # add phone_model 2 to job 3~4
        [jobs[i].phone_models.add(phone_models[1])
         for i in range(2, 4)]

        # add android_version 1 to job 3~4
        [jobs[i].android_version.add(android_versions[0])
         for i in range(2, 4)]

        # add android_version 2 to job 5~6
        [jobs[i].android_version.add(android_versions[1])
         for i in range(4, 6)]

        response = self.client.get(
            self.url + '?phone_model_name__in='
                       'ReefList[phone_model_name__1{%,%}phone_model_name__2]'
                       '&android_version__version__in=ReefList[version__1{%,%}version__2]'
        )

        job_labels = [job['job_name'] for job in response.data['jobs']]
        self.assertEqual(job_labels, ['1', '2', '3', '4', '5', '6'])
