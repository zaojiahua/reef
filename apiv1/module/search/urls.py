from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from apiv1.module.search.view import RdsLogSearchView

urlpatterns = [
    path(
        'search/rds_log_search/',
        csrf_exempt(RdsLogSearchView.as_view()),
        name='rds_log_search'
    ),
]