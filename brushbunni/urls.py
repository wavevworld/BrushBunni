# Project URL configuration.

from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve

from blog.sitemaps import sitemaps
from blog.views import favicon, robots_txt

app_name = "blog"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('favicon.ico', favicon),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),
    path('', include('blog.urls')),
]

# Static files are served by WhiteNoise. Media (user uploads) must be served
# explicitly so images keep working when DEBUG is off. Fine for this site's
# scale; move to nginx/CDN if traffic grows.
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

# Under DEBUG the staticfiles app serves /static/ from the app directories
# automatically, so no extra urlpattern is needed here.