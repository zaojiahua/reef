from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from apiv1.module.device.models import Manufacturer, PhoneModel, RomVersion
from apiv1.module.rds.models import Rds
from apiv1.module.user.models import ReefUser
from apiv1.module.tboard.models import TBoard, TBoardJob
from reef.settings import ENABLE_TCCOUNTER


class TestJob(APITestCase):

    def setUp(self):
        self.default_data = TestTool.load_default_data()
        self.default_id = self.default_data['job'].id

    @tccounter("job_list", "get", ENABLE_TCCOUNTER)
    def test_get_jobs_all_info(self):
        response = self.client.get(reverse('job_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("job_list", "get", ENABLE_TCCOUNTER)
    def test_get_job_wanted_info(self):
        response = self.client.get(
            f"{reverse('job_list')}?fields=id,job_label,job_name,job_type,description,job_deleted")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_recently_used_time(self):
        """
        Date: 2019/02/18
        Author: Raymond
        Test job's auto generated field 'recently_used_time'
        this field should return rds.start_time which rds.tboard.job is this job
        and rds.tboard.author not 'AITester'
        """
        aitester = ReefUser.objects.create(username='AITester')
        tboard = TBoard.objects.create(
            author=self.default_data['user'],  # Not AITester
            board_stamp='2018-01-01 00:00:00+0800'
        )
        TBoardJob(tboard=tboard, job=self.default_data['job'], order=0)
        tboard.device.add(self.default_data['device'])

        ai_tboard = TBoard.objects.create(
            author=aitester,
            board_stamp='2018-01-01 00:00:01+0800'
        )

        TBoardJob(tboard=ai_tboard, job=self.default_data['job'], order=0)
        ai_tboard.device.add(self.default_data['device'])

        Rds.objects.all().delete()  # 确认没有其他Rds
        # tboard created by AITester
        Rds.objects.create(
            job=self.default_data['job'],
            device=self.default_data['device'],
            tboard=ai_tboard,
            start_time='2018-01-01 00:00:00+0800'
        )
        # tboard created by normal user
        Rds.objects.create(
            job=self.default_data['job'],
            device=self.default_data['device'],
            tboard=tboard,
            start_time='2018-01-02 00:00:00+0800'
        )
        # tboard created by normal user
        Rds.objects.create(
            job=self.default_data['job'],
            device=self.default_data['device'],
            tboard=tboard,
            start_time='2018-01-03 00:00:00+0800'
        )
        # tboard created by AITester
        Rds.objects.create(
            job=self.default_data['job'],
            device=self.default_data['device'],
            tboard=ai_tboard,
            start_time='2018-01-04 00:00:00+0800'
        )

        self.assertEqual(
            self.default_data['job'].recently_used_time,
            '2018-01-03 00:00:00'
        )

    def test_earliest_used_time(self):
        """
        Date: 2019/02/18
        Author: Raymond
        Test job's auto generated field 'earliest_used_time'
        this field should return rds.start_time which rds.tboard.job is this job
        and rds.tboard.author not 'AITester'
        """
        aitester = ReefUser.objects.create(username='AITester')
        tboard = TBoard.objects.create(
            author=self.default_data['user'],  # Not AITester
            board_stamp='2018-01-01 00:00:00+0800'
        )

        TBoardJob(tboard=tboard, job=self.default_data['job'], order=0).save()
        tboard.device.add(self.default_data['device'])

        ai_tboard = TBoard.objects.create(
            author=aitester,
            board_stamp='2018-01-01 00:00:01+0800'
        )

        TBoardJob(tboard=ai_tboard, job=self.default_data['job'], order=0).save()
        ai_tboard.device.add(self.default_data['device'])

        Rds.objects.all().delete()  # 确认没有其他Rds
        # tboard created by AITester
        Rds.objects.create(
            job=self.default_data['job'],
            device=self.default_data['device'],
            tboard=ai_tboard,
            start_time='2018-01-01 00:00:00+0800'
        )
        # tboard created by normal user
        Rds.objects.create(
            job=self.default_data['job'],
            device=self.default_data['device'],
            tboard=tboard,
            start_time='2018-01-02 00:00:00+0800'
        )
        # tboard created by normal user
        Rds.objects.create(
            job=self.default_data['job'],
            device=self.default_data['device'],
            tboard=tboard,
            start_time='2018-01-03 00:00:00+0800'
        )
        # tboard created by AITester
        Rds.objects.create(
            job=self.default_data['job'],
            device=self.default_data['device'],
            tboard=ai_tboard,
            start_time='2018-01-04 00:00:00+0800'
        )

        self.assertEqual(
            self.default_data['job'].earliest_used_time,
            '2018-01-02 00:00:00'
        )

    def test_manufacturer_uniq_on_create(self):
        """
        Date: 2019/06/11
        Author: Raymond
        Job 中的 rom_version和 phone_model 所属的 manufacturer 应该是唯一的
        """
        m1 = Manufacturer.objects.create(manufacturer_name="1")
        m2 = Manufacturer.objects.create(manufacturer_name="2")

        phone_model = PhoneModel.objects.create(manufacturer=m1, phone_model_name="p1")
        rom_version = RomVersion.objects.create(manufacturer=m2, version="r2")

        response = self.client.post(reverse("job_list"), data={
            "job_label": "job123",
            "job_name": "job123",
            "job_type": "UnKnow",
            "rom_version": [rom_version.id],
            "phone_models": [phone_model.id]
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_manufacturer_uniq_on_update(self):
        """
        Date: 2019/06/11
        Author: Raymond
        Job 中的 rom_version和 phone_model 所属的 manufacturer 应该是唯一的
        """
        m1 = Manufacturer.objects.create(manufacturer_name="1")
        m2 = Manufacturer.objects.create(manufacturer_name="2")

        phone_model = PhoneModel.objects.create(manufacturer=m1, phone_model_name="p1")
        rom_version1 = RomVersion.objects.create(manufacturer=m1, version="r1")
        rom_version2 = RomVersion.objects.create(manufacturer=m2, version="r2")

        with open('apiv1/module/job/tests/file/0JBblockDict4front.json', 'rb') as ui_json_file:
            response = self.client.post(reverse("job_list"), data={
                "job_label": "job123",
                "job_name": "job123",
                "job_type": "UnKnow",
                "rom_version": [rom_version1.id],
                "phone_models": [phone_model.id],
                "ui_json_file": ui_json_file
            })

        job_id = response.data.get("id", None)
        self.assertIsNotNone(job_id)

        response = self.client.patch(reverse("job_detail", args=(job_id,)), data={
            "rom_version": [rom_version2.id],
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, reverse("job_detail", args=(job_id,)))

    @tccounter("job_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_by_id(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test get a instance by id
        """
        response = self.client.get(reverse('job_detail', args=[self.default_id]))
        self.assertEqual(response.data['id'], self.default_id)

    @tccounter("job_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_which_id_not_exist(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test get a instance which do not exist
        """
        response = self.client.get(reverse('job_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tccounter("job_list", "post", ENABLE_TCCOUNTER)
    def test_post_and_job_label_is_not_unique(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test create job with job_label
        """
        with open('apiv1/module/job/tests/file/0JBblockDict4front.json', 'rb') as ui_json_file:
            response = self.client.post(reverse("job_list"), data={
                "job_label": self.default_data['job'].job_label,
                "job_name": "name_test",
                "job_type": "UnKnow",
                "ui_json_file": ui_json_file
            })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("job_list", "post", ENABLE_TCCOUNTER)
    def test_bulk_create(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test bulk create
        """
        with open('apiv1/module/job/tests/file/0JBblockDict4front.json', 'rb') as ui_json_file:
            custom_tags = [{
                "job_label": "test1",
                "job_name": "name_test1",
                "job_type": "UnKnow",
                "ui_json_file": ui_json_file
            },
                {
                    "job_label": "test5",
                    "job_name": "name_test2",
                    "job_type": "UnKnow",
                    "ui_json_file": ui_json_file
                }
            ]
            response = self.client.post(reverse('job_list'), data=custom_tags)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter("job_detail", "put", ENABLE_TCCOUNTER)
    def test_put_200ok(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test put method 200 OK
        """
        with open('apiv1/module/job/tests/file/0JBblockDict4front.json', 'rb') as ui_json_file:
            response = self.client.put(reverse('job_detail', args=[self.default_id]), data={
                'job_label': self.default_data['job'].job_label,
                'job_name': self.default_data['job'].job_name,
                'job_type': 'Uniq',
                'ui_json_file': ui_json_file
            })
            self.assertEqual(response.data['job_type'], 'Uniq')

    @tccounter("job_detail", "put", ENABLE_TCCOUNTER)
    def test_put_job_type_not_in_choice(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test update job_type not in choice
        """
        with open('apiv1/module/job/tests/file/0JBblockDict4front.json', 'rb') as ui_json_file:
            response = self.client.put(reverse('job_detail', args=[self.default_id]), data={
                'job_label': self.default_data['job'].job_label,
                'job_name': self.default_data['job'].job_name,
                'job_type': 'job_type_not_in_choice',
                'ui_json_file': ui_json_file
            })
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("job_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_200ok(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test patch method 200 OK
        """
        response = self.client.patch(reverse('job_detail', args=[self.default_id]), data={
            'job_name': 'name_test'
        })
        self.assertEqual(response.data['job_name'], 'name_test')

    @tccounter("job_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_author(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test patch author can be None
        """
        response = self.client.patch(reverse('job_detail', args=[self.default_id]), data={
            'author': None
        })
        self.assertEqual(response.data['author'], None)

    @tccounter("job_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_job(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test delete job
        """
        # job 不允许删除
        response = self.client.delete(reverse('job_detail', args=[self.default_id]))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    @tccounter("job_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_instance_do_not_exist(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test delete instance which is not exists
        """
        response = self.client.delete(reverse('job_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
