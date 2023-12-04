from django.urls import path, include
from rest_framework.documentation import include_docs_urls
from rest_framework.schemas import get_schema_view

from reef.settings import SHOW_SWAGGER
from apiv1.document import swagger_schema_view
from apiv1.module.device.urls import urlpatterns as device_url
from apiv1.module.job.urls import urlpatterns as job_url
from apiv1.module.rds.urls import urlpatterns as rds_url
from apiv1.module.system.urls import urlpatterns as system_url
from apiv1.module.tboard.urls import urlpatterns as tboard_url
from apiv1.module.user.urls import urlpatterns as user_url
from apiv1.module.search.urls import urlpatterns as search_url
from apiv1.module.abnormity.urls import urlpatterns as abnormity_url
from apiv1.module.resource.urls import urlpatterns as resource_url


schema_view = get_schema_view()

urlpatterns = [
    # basic
    path('docs/', include_docs_urls(title='My API title')),
    path('schema/', schema_view),
    # path('redoc/', swagger_schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

] + job_url + tboard_url + device_url + system_url + rds_url + user_url + search_url + abnormity_url + resource_url

if SHOW_SWAGGER:
    urlpatterns += [path('swagger/', swagger_schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui')]
