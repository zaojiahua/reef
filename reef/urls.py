import os

import django
from django.conf.urls.static import static
from django.urls import path, include, re_path
from django.contrib import admin

from apiv1.core.view.server_test import ServerTestView
from reef import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reef.settings')
django.setup()

urlpatterns = [
    path('api/v1/', include('apiv1.urls')),
    path('admin/', admin.site.urls),
    re_path(r'^server/test/(?P<ip>([0-9]{1,3}\.){3}[0-9]{1,3})/', ServerTestView.as_view())
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
