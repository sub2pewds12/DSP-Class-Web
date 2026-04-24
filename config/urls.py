from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.http import HttpResponse
from apps.teams.api import api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('favicon.ico', lambda r: HttpResponse(status=204)),
    path('api/', api.urls),
    path('', include('apps.teams.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
