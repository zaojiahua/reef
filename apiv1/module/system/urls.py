from django.urls import path, include

from apiv1.core import routers
from apiv1.module.system.view import CabinetRegistView, GetReefSpaceUsageView, CreateWoodenBoxView, RemoveWoodenBoxView, \
    GetCabinetTypeInfoView, GetReefVersionView, UpdateCabinetMLocationView, DeleteLogView
from apiv1.module.system.viewset import DynamicSystemViewSet, \
    DynamicCabinetViewSet, DynamicWoodenBoxViewSet

router = routers.ReefDefaultRouter()
router.register(r'system', DynamicSystemViewSet, basename='system')
router.register(r'cabinet', DynamicCabinetViewSet, basename='cabinet')
router.register(r'woodenbox', DynamicWoodenBoxViewSet, basename='woodenbox')


urlpatterns = [
    path('cedar/', include(router.urls)),

    path(
        'coral/cabinet_regist/<int:pk>/',
        CabinetRegistView.as_view(),
        name='cabinet_regist'
    ),

    path('cedar/get_reef_space_usage/',
         GetReefSpaceUsageView.as_view(),
         name='get_reef_space_usage'
         ),

    path('cedar/create_wooden_box/',
         CreateWoodenBoxView.as_view(),
         name='create_wooden_box'
         ),

    path('cedar/remove_wooden_box/<int:pk>',
         RemoveWoodenBoxView.as_view(),
         name='remove_wooden_box'
         ),

    path('cedar/get_cabinet_type_info/',
        GetCabinetTypeInfoView.as_view(),
         name='get_cabinet_type_info'
         ),

    path(
        'cedar/get_reef_version/',
        GetReefVersionView.as_view(),
        name='get_reef_version'
    ),

    path(
        'cedar/update_cabinet_mlocation/',
        UpdateCabinetMLocationView.as_view(),
        name='update_cabinet_mlocation'
    ),

    path(
        'cedar/delete_log/',
        DeleteLogView.as_view(),
        name='delete_log'
    )
]
