from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.http import HttpResponse
from apps.teams.api import api

from django_prometheus import exports
from django.contrib.auth.decorators import user_passes_test

def can_manage_system(user):
    return user.is_authenticated and getattr(user, 'can_manage_system', False)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('favicon.ico', lambda r: HttpResponse(status=204)),
    path('api/', api.urls),
    path('', include('apps.teams.urls')),
    path('internal/telemetry/metrics/', user_passes_test(can_manage_system)(exports.ExportToDjangoView), name='prometheus-metrics'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
