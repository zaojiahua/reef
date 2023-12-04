from django.urls import path, include

from apiv1.core import routers
from apiv1.module.job.viewset import DynamicJobViewSet, DynamicCustomTagViewSet, DynamicJobTestAreaViewSet, \
    DynamicJobResourceFileViewSet, DynamicJobFlowViewSet, TestGatherViewSet, TestProjectViewSet, \
    DynamicUnitENLibViewSet, DynamicUnitLibViewSet
from apiv1.module.job.view import UnionJobView, JobResourceFileMultiUploadView, JobExportView, JobImportView, \
    JobChangeOwnerView, JobFlowOrderUpdateView, JobFlowCopyView, JobDeletedView, JobCopyView, JobBindResourceView, \
    UpdateTestGatherViewSet, MergeTestGatherView, JobLabelOrderView, SearchJobView, DeleteTagView, JobExecuteImportView, \
    OperateTestGather, GetTestGatherViewSet

router = routers.ReefDefaultRouter()

router.register(r'job', DynamicJobViewSet)
router.register(r'custom_tag', DynamicCustomTagViewSet)
router.register(r'job_test_area', DynamicJobTestAreaViewSet)
router.register(r'unit', DynamicUnitLibViewSet)
router.register(r'unit_en', DynamicUnitENLibViewSet)
router.register(r'job_res_file', DynamicJobResourceFileViewSet)
router.register(r'job_flow', DynamicJobFlowViewSet)
router.register(r'test_gather', TestGatherViewSet)
router.register(r'update_test_gather', UpdateTestGatherViewSet)
router.register(r'test_project', TestProjectViewSet)

urlpatterns = [
    path('cedar/', include(router.urls)),

    # 根据筛选条件（phone_model_name/android_version__version）筛选出job并集集合
    path('cedar/union_job/',
         UnionJobView.as_view(),
         name='union_job'
         ),

    path('cedar/job_upload_multi_res_file/',
         JobResourceFileMultiUploadView.as_view(),
         name='job_upload_multi_res_file'
         ),

    path('cedar/job_export/',
         JobExportView.as_view(),
         name='job_export'
         ),

    path('cedar/job_import/',
         JobImportView.as_view(),
         name='job_import'
         ),

    path('cedar/execute_job_import/',
        JobExecuteImportView.as_view(),
        name='execute_job_import'
        ),

    path('cedar/job_change_owner/',
         JobChangeOwnerView.as_view(),
         name='job_change_owner'
         ),

    path('cedar/job_flow_order_update/',
         JobFlowOrderUpdateView.as_view(),
         name='job_flow_order_update'
         ),

    path('cedar/job_flow_copy/',
         JobFlowCopyView.as_view(),
         name='job_flow_copy'
         ),

    path('cedar/job_deleted/',
         JobDeletedView.as_view(),
         name='job_deleted'
         ),

    path('cedar/job_copy/',
         JobCopyView.as_view(),
         name='job_copy'
         ),

    path('cedar/job_bind_resource/',
         JobBindResourceView.as_view(),
         name='job_bind_resource'
        ),

    path('cedar/merge_test_gather/',
        MergeTestGatherView.as_view(),
         name='merge_test_gather'
         ),

    path('cedar/job_label_order/',
         JobLabelOrderView.as_view(),
         name='job_label_order'
         ),

    path('cedar/search_job/',
         SearchJobView.as_view(),
         name='search_job'),

    path(
        'cedar/delete_tag/',
        DeleteTagView.as_view(),
        name='delete_tag'
    ),

    path(
        'cedar/operate_test_gather/',
        OperateTestGather.as_view(),
        name='operate_test_gather'
    ),

    path(
        'cedar/get_test_gather/',
        GetTestGatherViewSet.as_view(),
        name='get_test_gather'
    )

]
