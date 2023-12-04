from django.urls import path, include

from apiv1.core import routers
from apiv1.module.rds.view import RdsCreateOrUpdateView, UploadRdsLogView, UploadRdsScreenShotView, GetRdsRapidView, \
    GetRdsGroupByPhoneModelNameView, GetRdsGroupByDeviceLabelView, GetRdsView, FilterRdsValidityView, \
    GetRdsStatisticsData, GetSimilarityMatrix, GetJobFeatureMatrix, SortRdsScreenShotView, FilterInvalidRdsView, \
    RdsScreenShotFileMultiUploadView, UploadCoolPadPowerLastView
from apiv1.module.rds.viewset import DynamicRdsViewSet, DynamicRdsLogViewSet, DynamicRdsScreenShotViewSet

router = routers.ReefDefaultRouter()
router.register(r'rds', DynamicRdsViewSet)
router.register(r'rds_log', DynamicRdsLogViewSet, basename='rds_log')
router.register(r'rds_screenshot', DynamicRdsScreenShotViewSet, basename='rds_screenshot')

urlpatterns = [
    path('cedar/', include(router.urls)),

    path('cedar/filter_rds_validity/',
         FilterRdsValidityView.as_view(),
         name='filter_rds_validity',
         ),

    path('coral/search_rds/',
         GetRdsView.as_view(),
         name='search_rds'
         ),

    path('coral/rds_create_or_update/',
         RdsCreateOrUpdateView.as_view(),
         name='rds_create_or_update'
         ),
    path('coral/upload_rds_log_file/',
         UploadRdsLogView.as_view(),
         name='upload_rds_log_file'
         ),

    path('coral/upload_rds_screen_shot/',
         UploadRdsScreenShotView.as_view(),
         name='upload_rds_screen_shot'
         ),

    path('cedar/get_rds_rapid/',
         GetRdsRapidView.as_view(),
         name='get_rds_rapid'
         ),

    path('cedar/get_rds_group_by_phone_model_name/',
         GetRdsGroupByPhoneModelNameView.as_view(),
         name='get_rds_group_by_phone_model_name'
         ),

    path('cedar/get_rds_group_by_device_label/',
         GetRdsGroupByDeviceLabelView.as_view(),
         name='get_rds_group_by_device_label'
         ),

    path('cedar/get_rds_statistics_data/',
         GetRdsStatisticsData.as_view(),
         name='get_rds_statistics_data'
         ),

    path('coral/get_similarity_matrix/',
         GetSimilarityMatrix.as_view(),
         name='get_similarity_matrix'
         ),

    path('coral/get_job_feature_matrix/',
         GetJobFeatureMatrix.as_view(),
         name='get_job_feature_matrix'
         ),

    path('cedar/get_sort_rds_screenshot/',
         SortRdsScreenShotView.as_view(),
         name='get_sort_rds_screenshot'
        ),

    path(
        'cedar/filter_invalid_rds/',
        FilterInvalidRdsView.as_view(),
        name='filter_invalid_rds'
    ),

    path(
        'cedar/rds_screen_shot_file_multi_upload/',
        RdsScreenShotFileMultiUploadView.as_view(),
        name='rds_screen_shot_file_multi_upload'
    ),

    path(
        'coral/upload_cool_pad_power_last_view/',
        UploadCoolPadPowerLastView.as_view(),
        name='upload_cool_pad_power_last_view'
    )
]
