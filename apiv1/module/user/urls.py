from django.urls import path, include

from apiv1.core import routers
from apiv1.module.user.viewset import DynamicReefUserViewSet, DynamicGroupViewSet, DynamicTokenViewSet
from apiv1.module.user.view import UserLoginView, LoginView, GetUserPermissionsView

router = routers.ReefDefaultRouter()

router.register(r'reefuser', DynamicReefUserViewSet, basename='reefuser')
router.register(r'group', DynamicGroupViewSet, basename='group')
router.register(r'token', DynamicTokenViewSet, basename='token')

urlpatterns = [
    path('cedar/', include(router.urls)),

    path('cedar/user_login/',
         UserLoginView.as_view(),
         name='user_login'
         ),

    path('login/', LoginView.as_view(), name='login'),
    path('permissions/', GetUserPermissionsView.as_view()),
]
