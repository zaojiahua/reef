from django.utils import timezone

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool
from apiv1.module.rds.models import Rds
from apiv1.module.tboard.models import TBoard
from apiv1.module.user.models import ReefUser
from apiv1.core.test import tccounter
from reef.settings import ENABLE_TCCOUNTER

class TestTBoard(APITestCase):
    def setUp(self):
        self.default_data = TestTool.load_default_data()

    def add_extra_date(self):
        self.rds_for_test = Rds.objects.create(job=self.default_data['job'],
                                               device=self.default_data['device'],
                                               tboard=self.default_data['tboard'],
                                               start_time=timezone.now(),
                                               end_time=timezone.now(),
                                               job_assessment_value='0'
                                               )
        self.tboard_for_test = TBoard.objects.create(author=self.default_data['user'],
                                                     repeat_time=1,
                                                     board_name='board_name1',
                                                     finished_flag=False,
                                                     board_stamp=timezone.now(),
                                                     end_time=timezone.now()
                                                     )

    @tccounter("tboard_list", "get", ENABLE_TCCOUNTER)
    def test_get_tboards_all_info(self):
        response = self.client.get(reverse('tboard_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("tboard_list", "get", ENABLE_TCCOUNTER)
    def test_get_tboard_wanted_info(self):
        response = self.client.get(
            f"{reverse('tboard_list')}?fields=id,repeat_time,board_name,finished_flag,board_stamp,end_time")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("tboard_list", "post", ENABLE_TCCOUNTER)
    def test_post_tboard_200ok(self):
        """
        Date: 2019/11/18
        Author: wengmeijia
        Describe: POST /cedar/tboard/
        """
        response = self.client.post(
            reverse('tboard_list'),
            data={
                  "board_stamp": "2018-11-11 22:22:23",
	              "author": 1,
	              "device": [self.default_data['device'].id],
	              "job": [self.default_data['job'].id]
                 }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter("tboard_list", "post", ENABLE_TCCOUNTER)
    def test_post_tboard_field_required(self):
        """
        Date: 2019/11/18
        Author: wengmeijia
        Describe: POST /cedar/tboard/
        """
        response = self.client.post(
            reverse('tboard_list'),
            data={
                    "board_stamp": "2018-11-11 22:22:23",
                    "device": [self.default_data['device'].id],
                    "job": [self.default_data['job'].id]
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("tboard_detail", "put", ENABLE_TCCOUNTER)
    def test_put_tboard_200ok(self):
        """
        Date: 2019/11/18
        Author: wengmeijia
        Describe: PUT /cedar/tboard/
        """
        response = self.client.put(
            reverse('tboard_detail', args=(self.default_data['tboard'].id,)),
            data={
                "board_stamp":timezone.now(),
                "author":ReefUser.objects.filter()[0].id,
                "device": [self.default_data['device'].id],
                "job": [self.default_data['job'].id]
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("tboard_detail", "put", ENABLE_TCCOUNTER)
    def test_put_tboard_400(self):
        """
        Date: 2019/11/18
        Author: wengmeijia
        Describe: PUT /cedar/tboard/
        """
        response = self.client.put(
            reverse('tboard_detail', args=(self.default_data['tboard'].id,)),
            data={
                "board_stamp": timezone.now(),
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("tboard_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_tboard_200ok(self):
        """
        Date: 2019/11/18
        Author: wengmeijia
        Describe: PATCH /cedar/tboard/
        """
        response = self.client.patch(
            reverse('tboard_detail', args=(self.default_data['tboard'].id,)),
            data={
                "device":[self.default_data['device'].id]
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("tboard_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_tboard_update_device_id(self):
        """
        Date: 2019/11/18
        Author: wengmeijia
        Describe: PATCH /cedar/tboard/
        """
        response = self.client.patch(
            reverse('tboard_detail', args=(self.default_data['tboard'].id,)),
            data={
                "device":[self.default_data['device'].id]
            }
        )
        self.assertEqual(response.data.get('device')[0], self.default_data['device'].id)

    @tccounter("tboard_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_tboard_200ok(self):
        """
        Date: 2019/11/18
        Author: wengmeijia
        Describe: DELETE /cedar/tboard/
        """
        response = self.client.delete(
            reverse('tboard_detail', args=(self.default_data['tboard'].id,)),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @tccounter("tboard_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_tboard_not_found(self):
        """
        Date: 2019/11/18
        Author: wengmeijia
        Describe: DELETE /cedar/tboard/
        """
        response = self.client.delete(
            reverse('tboard_detail', args=(10,)),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tccounter("tboard_detail", "get", ENABLE_TCCOUNTER)
    def test_get_tboard_200ok(self):
        """
        Date: 2019/11/18
        Author: wengmeijia
        Describe: GET /cedar/tboard/
        """
        response = self.client.get(
            reverse('tboard_detail', args=(self.default_data['tboard'].id,)),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("tboard_detail", "get", ENABLE_TCCOUNTER)
    def test_get_tboard_get_board_name(self):
        """
        Date: 2019/11/18
        Author: wengmeijia
        Describe: GET /cedar/tboard/
        """
        response = self.client.get(
            reverse('tboard_detail', args=(self.default_data['tboard'].id,)),
        )
        self.assertEqual(response.data['board_name'], "tboard0")

    def test_tboard_success_ratio(self):
        """
        Date: 2019/06/03
        Author: Guozijun
        default_data['rds'] --> tboard_id = default_data['tboard'].id --> job_assessment_value = "null"
        rds_for_test       ---> tboard_id = default_data['tboard'].id --> job_assessment_value = "0"
        """
        self.add_extra_date()
        self.assertEqual(TBoard.objects.get(id=self.default_data['tboard'].id).success_ratio, 1.0)

    def test_job_assessment_value_null_to_0(self):
        """
        Date: 2019/06/03
        Author: Guozijun
        """
        self.add_extra_date()
        rds = self.default_data['rds']
        rds.job_assessment_value = '0'
        self.rds_for_test.end_time = timezone.now()
        rds.save()
        self.assertEqual(TBoard.objects.get(id=self.default_data['tboard'].id).success_ratio, 1.0)

    def test_job_assessment_value_0_to_1(self):
        """
        Date: 2019/06/03
        Author: Guozijun
        """
        self.add_extra_date()
        self.rds_for_test.job_assessment_value = '1'
        self.rds_for_test.end_time = timezone.now()
        self.rds_for_test.save()
        self.assertEqual(TBoard.objects.get(id=self.default_data['tboard'].id).success_ratio, 0.5)

    def test_partial_update_job_assessment_value_null_to_1(self):
        """
        Date: 2019/06/03
        Author: Guozijun
        """
        self.add_extra_date()
        self.client.patch(
            reverse('rds_detail', kwargs={'pk': self.default_data['rds'].id}),
            data={
                'job_assessment_value': '1'
            }
        )
        self.assertEqual(TBoard.objects.get(id=self.default_data['tboard'].id).success_ratio, 1.0)

    def test_change_tboard_relation_for_rds(self):
        """
        Date: 2019/06/03
        Author: Guozijun
        """
        self.add_extra_date()
        self.rds_for_test.tboard_id = self.tboard_for_test.id
        self.rds_for_test.save()
        self.assertEqual(TBoard.objects.get(id=self.default_data['tboard'].id).success_ratio, 0.0)
        self.assertEqual(TBoard.objects.get(id=self.tboard_for_test.id).success_ratio, 1.0)

    def test_update_rds_job_assessment_value_and_change_tboard_relation_for_rds(self):
        """
        Date: 2019/06/24
        Author: Guozijun

        Initial : default_data['tboard'] ---   default_data['rds'] -->job_assessment_value = None
                                               rds_for_test  --> job_assessment_value = '0'       (1/2 = 0.5)
                  tboard_for_test       ---    no relationship with rds                           (None)

        Test :  default_data['rds'].job_assessment_value  :  None --> '1'
                rds_for_test.tboard_id   :    default_data['tboard'].id ---> tboard_for_test.id

        Final :  default_data['tboard'] ---   default_data['rds'] -->job_assessment_value = '1'   (0/1 = 0.0)
                 tboard_for_test        ---    rds_for_test  --> job_assessment_value = '0'       (1/1 = 1.0)
        """
        self.add_extra_date()
        self.default_data['rds'].job_assessment_value = '1'
        self.default_data['rds'].end_time = timezone.now()
        self.default_data['rds'].save()
        self.assertEqual(TBoard.objects.get(id=self.default_data['tboard'].id).success_ratio, 0.5)
        self.assertEqual(TBoard.objects.get(id=self.tboard_for_test.id).success_ratio, None)
        self.rds_for_test.tboard_id = self.tboard_for_test.id
        self.rds_for_test.save()
        self.assertEqual(TBoard.objects.get(id=self.default_data['tboard'].id).success_ratio, 0.0)
        self.assertEqual(TBoard.objects.get(id=self.tboard_for_test.id).success_ratio, 1.0)

    def test_update_rds_job_assessment_value_0_to_1(self):
        """
        Date: 2019/06/27
        Author: Guozijun
        """
        self.add_extra_date()
        self.assertEqual(TBoard.objects.get(id=self.default_data['tboard'].id).success_ratio, 1.0)
        Rds.objects.filter(id=self.rds_for_test.id).update(job_assessment_value='1')
        self.assertEqual(TBoard.objects.get(id=self.default_data['tboard'].id).success_ratio, 0.0)

    def test_create_rds_and_job_assessment_value_1(self):
        """
        Date: 2019/10/15
        Author: Guozijun
        default_data['rds'] --> tboard_id = default_data['tboard'].id --> job_assessment_value = "null"
        rds_for_test       ---> tboard_id = default_data['tboard'].id --> job_assessment_value = "0"
        """
        self.add_extra_date()
        self.assertEqual(TBoard.objects.get(id=self.default_data['tboard'].id).success_ratio, 1.0)
        # create rds and job_assessment_value = '1'
        Rds.objects.create(job=self.default_data['job'],
                           device=self.default_data['device'],
                           tboard=self.default_data['tboard'],
                           end_time=timezone.now(),
                           job_assessment_value='1'
                           )
        self.assertEqual(TBoard.objects.get(id=self.default_data['tboard'].id).success_ratio, 0.5)

    def test_delete_rds_and_job_assessment_value_null(self):
        """
        Date: 2019/10/15
        Author: Guozijun
        default_data['rds'] --> tboard_id = default_data['tboard'].id --> job_assessment_value = "null"
        rds_for_test       ---> tboard_id = default_data['tboard'].id --> job_assessment_value = "0"
        """
        self.add_extra_date()
        self.assertEqual(TBoard.objects.get(id=self.default_data['tboard'].id).success_ratio, 1.0)
        # delete rds and job assessment value null
        self.default_data['rds'].delete()
        self.assertEqual(TBoard.objects.get(id=self.default_data['tboard'].id).success_ratio, 1.0)
