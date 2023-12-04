from django.urls import path

from apiv1.module.system.consumers import LogDeleteConsumer
from apiv1.module.tboard.consumers import TBoardDeleteConsumer, TBoardDeleteFailConsumer

websocket_urlpatterns = [
    # tboard
    path('ws/tboard/tboard_delete/', TBoardDeleteConsumer),
    path('ws/tboard/tboard_deleted_fail/', TBoardDeleteFailConsumer),
    path('ws/system/log_delete/', LogDeleteConsumer)
]
