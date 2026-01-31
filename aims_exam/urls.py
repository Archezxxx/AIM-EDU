"""
URL configuration for aims_exam project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
]

# URL patterns with language prefix
urlpatterns += i18n_patterns(
    path('', include('accounts.urls', namespace='accounts')),
    path('schools/', include('schools.urls', namespace='schools')),
    path('exams/', include('exams.urls', namespace='exams')),
    path('zipgrade/', include('zipgrade.urls', namespace='zipgrade')),
    path('analytics/', include('analytics.urls', namespace='analytics')),
    prefix_default_language=False,
)

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
