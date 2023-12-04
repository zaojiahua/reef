from django.urls import path, include

from apiv1.core import routers
from apiv1.module.tboard.view import GetTboardRunningDetailView, GetTboardStatisticsView, CreateTBoardView, \
    EndTBoardView, GetTboardProgressView, GetTboardSuccessRatioView, InsertTBoard, RemoveTBoard, DeleteTBoard, \
    JobPriorTboardView, RepeatExecuteTBoardView, TBoardRepeatExecuteCheckView, ReleaseBusyDeviceView, OpenInsertTBoard, \
    OpenCoolPadInsertTBoard
from apiv1.module.tboard.views.get_data_view import GetDataViewView, DataViewLabelFilterView, \
    DataViewFilterView
from apiv1.module.tboard.views.get_data_view_calendar import GetDataViewCalendarView
from apiv1.module.tboard.views.get_data_view_summery import GetDataViewSummeryView
from apiv1.module.tboard.views.get_perf_data_view import GetPerfTboardDetailData, GetPerfDataJobData, \
    GetPerfDataPhoneModelData, GetPerfDataChart, GetPerfDataBarChart, GetSingleDevicePerfTableData, \
    GetPerfDataTimeBarChart, GetXlsData, PerfDataPreviewView
from apiv1.module.tboard.viewset import DynamicTBoardViewSet, TBoardStatisticsResultViewSet

router = routers.ReefDefaultRouter()
router.register(r'tboard', DynamicTBoardViewSet)
router.register(r'tboard_statistics_result', TBoardStatisticsResultViewSet)

urlpatterns = [
    path('cedar/', include(router.urls)),
    path('statistics/get_tboard_running_detail/',
         GetTboardRunningDetailView.as_view(),
         name='get_tboard_running_detail'
         ),

    path('statistics/get_tboard_statistics/',
         GetTboardStatisticsView.as_view(),
         name='get_tboard_statistics'
         ),
    path('coral/create_tboard/',
         CreateTBoardView.as_view(),
         name='create_tboard'
         ),

    path('coral/end_tboard/<int:pk>/',  # 任务正常执行完成，coral调用此接口
         EndTBoardView.as_view(),
         name='end_tboard'
         ),

    path('statistics/get_tboard_progress/',
         GetTboardProgressView.as_view(),
         name='get_tboard_progress'
         ),

    path('statistics/get_tboard_success_ratio/',
         GetTboardSuccessRatioView.as_view(),
         name='get_tboard_success_ratio'
         ),

    # cedar insert_tboard proxy
    path(
        'coral/insert_tboard/',
        InsertTBoard.as_view(),
        name='insert_tboard'
    ),

    # coral remove_tboard proxy
    path(
        'coral/remove_tboard/',
        RemoveTBoard.as_view(),
        name='remove_tboard'
    ),

    # tboard delete 会进入celery异步删除
    path(
        'cedar/delete_tboard/',
        DeleteTBoard.as_view(),
        name='delete_tboard'
    ),

    path(
        'cedar/get_data_view/',
        GetDataViewView.as_view(),
        name='get_data_view'
    ),

    path(
        'cedar/get_data_view_summery/',
        GetDataViewSummeryView.as_view(),
        name='get_data_view_summery'
    ),

    path(
        'cedar/get_data_view_calendar/',
        GetDataViewCalendarView.as_view(),
        name='get_data_view_calendar'
    ),

    path(
        'cedar/get_tboard_perf_dtail_data/',
        GetPerfTboardDetailData.as_view(),
        name='get_tboard_perf_dtail_data'
    ),

    path(
        'cedar/get_perf_data_job_data/',
        GetPerfDataJobData.as_view(),
        name='get_per_data_job_data'
    ),

    path(
        'cedar/get_perf_data_phone_model_data/',
        GetPerfDataPhoneModelData.as_view(),
        name='get_perf_data_phone_model_data'
    ),

    path(
        'cedar/get_perf_data_chart/',
        GetPerfDataChart.as_view(),
        name='get_perf_data_line_chart'
    ),

    path(
        'cedar/get_perf_data_bar_chart/',
        GetPerfDataBarChart.as_view(),
        name='get_perf_data_bar_chart'
    ),
    path(
        'cedar/get_perf_data_bar_chart_by_time_order/',
        GetPerfDataTimeBarChart.as_view(),
        name='get_perf_data_bar_chart_by_time_order'
    ),
    path(
        'cedar/get_xls_data/',
        GetXlsData.as_view(),
        name='get_xls_data'  # 获取性能测试结果的excel文件下载
    ),

    path(
        'cedar/get_single_device_table_data/',
        GetSingleDevicePerfTableData.as_view(),
        name='get_single_device_table_data'
    ),

    path(
        'cedar/get_job_prior_tboard/',
        JobPriorTboardView.as_view(),
        name='get_job_prior_tboard'
    ),

    # 废弃了，只能在来一次单任务tboard
    path(
        'cedar/repeat_execute_tboard/',
        RepeatExecuteTBoardView.as_view(),
        name='repeat_execute_tboard'
    ),

    path(
        'cedar/tboard_repeat_execute_check/',
        TBoardRepeatExecuteCheckView.as_view(),
        name='tboard_repeat_execute_check'
    ),

    path(
        'coral/release_busy_device/',
        ReleaseBusyDeviceView.as_view(),
        name='release_busy_device'
    ),

    path('cedar/data_view_label_filter/',
         DataViewLabelFilterView.as_view(),
         name='data_view_label_filter'
         ),

    path('cedar/data_view_job_filter/',
         DataViewFilterView.as_view(),
         name='data_view_job_filter'
         ),

    path('open/insert_tboard/',
         OpenInsertTBoard.as_view(),
         name='insert_tboard'
         ),

    path('open/coolpad/insert_tboard/',
         OpenCoolPadInsertTBoard.as_view(),
         name='coolpad_insert_tboard'
         ),

    path('cedar/perf_data_preview/',
         PerfDataPreviewView.as_view(),
         name='perf_data_preview'
        )
]
