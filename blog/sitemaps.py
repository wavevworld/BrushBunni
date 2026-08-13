from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Event, Member


class StaticViewSitemap(Sitemap):
    """The hand-written pages. 'shop' is left out on purpose — it is hidden
    from the navigation in base.html, so it should not be advertised either."""

    changefreq = "monthly"

    def items(self):
        return ['home', 'community', 'gallery', 'be_online', 'events',
                'project_bunni', 'members', 'contact']

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return 1.0 if item == 'home' else 0.6


class EventSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Event.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class MemberSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return Member.objects.filter(is_visible=True)


sitemaps = {
    'static': StaticViewSitemap,
    'events': EventSitemap,
    'members': MemberSitemap,
}
