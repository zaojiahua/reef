from django.urls import path, include

from apiv1.core import routers
from apiv1.module.abnormity.view import GetAbnormityCountView, AbnormityListView, \
    PowerAbnormityChartView, PowerAbnormityDataView, CreateExceptionView

router = routers.ReefDefaultRouter()
# router.register(r'abnormity', AbnormityViewset)


urlpatterns = [

    path('cedar/', include(router.urls)),

    path('cedar/get_abnormity_count/',
         GetAbnormityCountView.as_view(),
         name='get_abnormity_count'
         ),

    path('cedar/get_abnormity_list/',
         AbnormityListView.as_view(),
         name='get_abnormity_list'
         ),

    path('cedar/power_abnormity_chart/',
        PowerAbnormityChartView.as_view(),
        name='power_abnormity_chart'
        ),

    path('cedar/power_abnormity_data/',
         PowerAbnormityDataView.as_view(),
         name='power_abnormity_data'
         ),

    path('cedar/create_exception_data/',
        CreateExceptionView.as_view(),
         name='create_exception_data'
        )
    ]