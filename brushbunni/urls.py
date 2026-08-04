# blog/urls.py - Ensure event detail URL is properly configured

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

app_name = "blog"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('blog.urls')),
]

# Static files are served by WhiteNoise. Media (user uploads) must be served
# explicitly so images keep working when DEBUG is off. Fine for this site's
# scale; move to nginx/CDN if traffic grows.
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else '',
    )