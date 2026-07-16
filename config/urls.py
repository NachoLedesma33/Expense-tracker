from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('transactions/', include('transactions.urls')),
    path('analytics/', include('analytics.urls')),
    path('users/', include('users.urls')),
]

if settings.DEBUG:
    urlpatterns += [path('__reload__/', include('django_browser_reload.urls'))]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
