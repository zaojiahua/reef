from django.utils import timezone
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from apiv1.module.job.models import Job
from apiv1.module.rds.models import Rds
from apiv1.module.user.models import ReefUser
from apiv1.module.tboard.models import TBoard
from reef.settings import ENABLE_TCCOUNTER


def get_reef_list(param_list):
    params = '{%,%}'.join(param_list)
    return f'ReefList[{params}]'


class TestRds(APITestCase):

    def setUp(self):
        self.default_data = TestTool.load_default_data()

    def add_extra_data(self):
        self.ai_tester = ReefUser.objects.create(username='AITester',
                                                 password='123456',
                                                 date_joined=timezone.now())

        self.tboard_for_test_AItest = TBoard.objects.create(author=self.ai_tester,
                                                            repeat_time=1,
                                                            board_name='board_name1',
                                                            finished_flag=False,
                                                            board_stamp=timezone.now(),
                                                            end_time=timezone.now()
                                                            )
        self.job_for_test_with_job_type = Job.objects.create(
                                                            job_label='job1',
                                                            job_name='job1',
                                                            description='description',
                                                            author=self.default_data['user'],
                                                            job_type='Sysjob'
                                                            )

    @tccounter('rds_list', 'get', ENABLE_TCCOUNTER)
    def test_get_rdss_all_info(self):
        """
        Date: 2019/11/5
        Author: Goufuqiang
        Describe: /cedar/rds/
        """
        response = self.client.get(reverse('rds_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('rds_list', 'get', ENABLE_TCCOUNTER)
    def test_get_rds_wanted_info(self):
        """
        Date: 2019/11/5
        Author: Goufuqiang
        Describe: user add parameter
        """
        response = self.client.get(f"{reverse('rds_list')}?fields=id,start_time,end_time,job_assessment_value")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('rds_list', 'get', ENABLE_TCCOUNTER)
    def test_tboard_id_filter(self):
        """
        Date: 2018/12/19
        Author: Raymond
        Rds list api support tboard_id filter with key:
        'tboard__id'
        For example:
        GET path/to/api/?tboard__id=2451

        Note:tboard__id has two underscore '_'
        """
        response = self.client.get(
            reverse('rds_list') + f'?tboard__id={self.default_data["tboard"].id}'
        )
        self.assertIn('rdss', response.data)
        self.assertGreater(len(response.data['rdss']), 0)

    @tccounter('rds_list', 'get', ENABLE_TCCOUNTER)
    def test_phone_model_name_filter(self):
        """
        Date 2018/12/12
        Author: Raymond
        Rds list api support phone_model_name list filter with key:
        'device__phone_model__phone_model_name__in'
        For example:
        GET path/to/api/?device__phone_model__phone_model_name__in=ReefList[dior{%,%}xiaomi]
        """
        params = get_reef_list(
            (self.default_data['phone_model'].phone_model_name,
             'bla',
             'blabla')
        )
        response = self.client.get(
            reverse('rds_list') + f'?device__phone_model__phone_model_name__in={params}'
        )
        self.assertIn('rdss', response.data)
        self.assertGreater(len(response.data['rdss']), 0)

    @tccounter('rds_list', 'get', ENABLE_TCCOUNTER)
    def test_android_version_filter(self):
        """
        Date 2018/12/12
        Author: Raymond
        Rds list api support androi_version list filter with key:
        'device__android_version__version__in'
        For example:
        GET path/to/api/?device__android_version__version__in=ReefList[4.1.0{%,%}4.1.1]
        """
        params = get_reef_list(
            (self.default_data['android_version'].version,
             'bla',
             'blabla')
        )
        response = self.client.get(
            reverse('rds_list') + f'?device__android_version__version__in={params}'
        )
        self.assertIn('rdss', response.data)
        self.assertGreater(len(response.data['rdss']), 0)

    @tccounter('rds_list', 'get', ENABLE_TCCOUNTER)
    def test_cpu_name_filter(self):
        """
        Date 2018/12/12
        Author: Raymond
        Rds list api support cpu_name list filter with key:
        'device__phone_model__cpu_name__in'
        For example:
        GET path/to/api/?device__phone_model__cpu_name__in=ReefList[XiaoLong 600{%,%}Tegra x1]
        """
        params = get_reef_list(
            (self.default_data['phone_model'].cpu_name,
             'bla',
             'blabla')
        )
        response = self.client.get(
            reverse('rds_list') + f'?device__phone_model__cpu_name__in={params}'
        )
        self.assertIn('rdss', response.data)
        self.assertGreater(len(response.data['rdss']), 0)

    @tccounter('rds_list', 'get', ENABLE_TCCOUNTER)
    def test_custom_tag_filter(self):
        """
        Date 2018/12/12
        Author: Raymond
        Rds list api support custom_tag list filter with key:
        'job__custom_tag__custom_tag_name__in'
        For example:
        GET path/to/api/?job__custom_tag__custom_tag_name__in=ReefList[power{%,%}temperature]
        """
        params = get_reef_list(
            (self.default_data['custom_tag'].custom_tag_name,
             'bla',
             'blabla')
        )
        response = self.client.get(
            reverse('rds_list') + f'?job__custom_tag__custom_tag_name__in={params}'
        )
        self.assertIn('rdss', response.data)
        self.assertGreater(len(response.data['rdss']), 0)

    @tccounter('rds_list', 'get', ENABLE_TCCOUNTER)
    def test_return_job_id(self):
        """
        Date: 2018/12/19
        Author: Raymond
        Get .../rds/ should return job id in format:
        {
            "rdss": [
                {
                    other fields...

                    "job": {
                        "id": 1
                    }
                }
            ]
        }
        """
        response = self.client.get(
            reverse('rds_list'), data={'fields':'job.id'}
        )
        self.assertIsInstance(response.data['rdss'][0].get('job', None)['id'], int)

    @tccounter('rds_detail', 'get', ENABLE_TCCOUNTER)
    def test_rds_get_id_200ok(self):
        """
        Date: 2019/11/20
        Author: Goufuqiang
        Describe: GET /cedar/rds/{id}/
        """
        response = self.client.get(
            reverse('rds_detail', args=(self.default_data['rds'].id,))
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('rds_detail', 'get', ENABLE_TCCOUNTER)
    def test_rds_get_id_response_data_type(self):
        """
        Date: 2019/11/20
        Author: Goufuqiang
        Describe: check response data type
        """
        response = self.client.get(
            reverse('rds_detail', args=(1,))
        )
        self.assertIsInstance(response.data, dict)

    @tccounter('rds_list', 'post', ENABLE_TCCOUNTER)
    def test_rds_dict_binary(self):
        """
        Date: 2018/01/28
        Author: Raymond
        Field rds_dict stored in database with encoded binary string, not primative string
        and when we retrieve it, we should get a encoded dict, not primative string
        """
        response = self.client.post(
            reverse('rds_list'),
            data={
                'device': self.default_data['device'].id,
                'job': self.default_data['job'].id,
                'tboard': self.default_data['tboard'].id,
                'rds_dict': "{\"1\":1, \"2\":2, \"3\":{\"a\":\"a\", \"b\":\"b\"}}"
            }
        )
        rds = Rds.objects.get(pk=response.data['id'])
        self.assertIsInstance(rds.rds_dict, dict)

    def test_rds_create_with_tboard(self):
        """
        Date: 2019/04/16
        Author: Guozijun
        Rds create with tboard  by user
                    created_by_ai_tester: Null --> False (author is not AItester)
                    created_by_sys_job: Null ---> False  (job.job_type Null )
        """
        self.assertEqual(Rds.objects.filter(id=self.default_data['rds'].id).first().created_by_ai_tester, 'False')
        self.assertEqual(Rds.objects.filter(id=self.default_data['rds'].id).first().created_by_sys_job, 'False')

    @tccounter('rds_list', 'post', ENABLE_TCCOUNTER)
    def test_rds_create_with_tboard_by_AItester(self):
        """
        Date: 2019/04/16
        Author: Guozijun
        Rds create with tboard  by  AItester  job'job_type is Sysjob
                    created_by_ai_tester: Null --> True (author is AItester)
                    created_by_sys_job: Null ---> True  (job.job_type is Sysjob )
        """
        self.add_extra_data()
        rds_test = Rds.objects.create(
                                    device=self.default_data['device'],
                                    job=self.job_for_test_with_job_type,
                                    tboard=self.tboard_for_test_AItest
                                )
        self.assertEqual(Rds.objects.filter(id=rds_test.id).first().created_by_ai_tester, 'True')
        self.assertEqual(Rds.objects.filter(id=rds_test.id).first().created_by_sys_job, 'True')

    @tccounter('rds_detail', 'patch', ENABLE_TCCOUNTER)
    def test_rds_patch_tboard_User_to_AItester(self):
        """
        Date: 2019/04/16
        Author: Guozijun
        patch  tboard  by user to AItester to rds
                    created_by_ai_tester: Null --> False --> True (author is AItester)
                    created_by_sys_job: Null ---> False --> False  (job.job_type Null )
        """
        self.add_extra_data()
        self.client.patch(
            reverse('rds_detail', kwargs={'pk': self.default_data['rds'].id}),
            data={
                'tboard': self.tboard_for_test_AItest.id
            }
        )
        self.assertEqual(Rds.objects.filter(id=self.default_data['rds'].id).first().created_by_ai_tester, 'True')
        self.assertEqual(Rds.objects.filter(id=self.default_data['rds'].id).first().created_by_sys_job, 'False')

    @tccounter('rds_detail', 'patch', ENABLE_TCCOUNTER)
    def test_rds_patch_200ok(self):
        """
        Date: 2019/04/16
        Author: Guozijun
        Describe: PATCH /cedar/rds/{id}
        """
        response = self.client.patch(
            reverse('rds_detail', args=(self.default_data['rds'].id,)),
            data={
                'end_time': '2019-07-18 17:33:21+08'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('rds_detail', 'put', ENABLE_TCCOUNTER)
    def test_rds_put_200ok(self):
        """
        Date: 2019/04/16
        Author: Guozijun
        Describe: PUT /cedar/rds/{id}
        """
        self.add_extra_data()
        response = self.client.put(
            reverse('rds_detail', args=(self.default_data['rds'].id,)),
            data={
                'device': self.default_data['device'].id,
                'job': self.job_for_test_with_job_type.id,
                'tboard': self.tboard_for_test_AItest.id,
                'rds_dict': b'{}'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('rds_detail', 'put', ENABLE_TCCOUNTER)
    def test_rds_put_response_data(self):
        """
        Date: 2019/04/16
        Author: Guozijun
        Describe: get response data
        """
        self.add_extra_data()
        response = self.client.put(
            reverse('rds_detail', args=(self.default_data['rds'].id,)),
            data={
                'device': self.default_data['device'].id,
                'job': self.job_for_test_with_job_type.id,
                'tboard': self.tboard_for_test_AItest.id,
                'rds_dict': b'{}'
            }
        )
        self.assertEqual(response.data.get('device', None), self.default_data['device'].id)

    @tccounter('rds_detail', 'delete', ENABLE_TCCOUNTER)
    def test_rds_delete_200ok(self):
        """
        Date: 2019/04/16
        Author: Guozijun
        Describe: DELETE /cedar/rds/{id}
        """
        response = self.client.delete(
            reverse('rds_detail', args=(self.default_data['rds'].id,))
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @tccounter('rds_detail', 'delete', ENABLE_TCCOUNTER)
    def test_rds_delete_no_existent(self):
        """
        Date: 2019/04/16
        Author: Guozijun
        Describe: Delete no existent rds
        """
        response = self.client.delete(
            reverse('rds_detail', args=(100,))
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tccounter('rds_bulk_delete_rds', 'delete', ENABLE_TCCOUNTER)
    def test_bulk_delete_rds_200ok(self):
        """
        Date: 2019/11/20
        Author: Goufuqiang
        Describe: /cedar/rds/bulk_delete_rds/
        """
        response = self.client.delete(
            reverse('rds_bulk_delete_rds') + f'?rds_id_list={self.default_data["rds"].id}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('rds_bulk_delete_rds', 'delete', ENABLE_TCCOUNTER)
    def test_bulk_delete_rds_rds_id_list_is_empty(self):
        """
        Date: 2019/11/20
        Author: Goufuqiang
        Describe: rds_id_list parameter is empty
        """
        response = self.client.delete(
            reverse('rds_bulk_delete_rds') + f'?rds_id_list=""'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)