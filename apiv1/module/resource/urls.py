from django.urls import path, include

from apiv1.core import routers
from apiv1.module.resource.view import BindAccountSourceView, UnbindAccountSourceView, GetOrderAppNameView, \
    BlockUnbindSimCardView, ResourceExportView, ResourceImportView, TGuardViewSet
from apiv1.module.resource.viewset import SIMCardViewSet, AccountViewSet, APPGatherViewSet

router = routers.ReefDefaultRouter()
router.register(r'simcard', SIMCardViewSet)
router.register(r'account', AccountViewSet)
router.register(r'appgather', APPGatherViewSet)
router.register(r'tguard', TGuardViewSet)


urlpatterns = [

    path('cedar/', include(router.urls)),

    path(
        'cedar/bind_account_source/',
        BindAccountSourceView.as_view(),
        name='bind_account_source'
         ),

    path(
        'cedar/unbind_account_source/',
        UnbindAccountSourceView.as_view(),
        name='unbind_account_source'
    ),

    path(
        'cedar/get_order_app_name',
        GetOrderAppNameView.as_view(),
        name='get_order_app_name'
    ),

    path(
        'cedar/block_unbind_resource',
        BlockUnbindSimCardView.as_view(),
        name='block_unbind_resource'
    ),

    path(
        'cedar/resource_export/',
        ResourceExportView.as_view(),
        name='resource_export_view'
    ),

    path(
        'cedar/resource_import/',
        ResourceImportView.as_view(),
        name='resource_import'
    )

    ]