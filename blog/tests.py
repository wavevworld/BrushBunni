"""Smoke tests for the public site.

Deliberately shallow: they assert that every public URL renders at all. That is
the check nothing else was making — a template typo or a view referencing a
deleted model would previously only show up by loading the page by hand.
"""

from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from .models import Event, BBNote, ContactMessage, Member, PageContent


class PublicPagesTests(TestCase):
    """Every route in blog/urls.py answers 200."""

    @classmethod
    def setUpTestData(cls):
        cls.past_event = Event.objects.create(
            code='TEST-PAST', title='Test past event',
            date=date.today() - timedelta(days=30),
            description='A past event used by the tests.',
        )
        cls.upcoming_event = Event.objects.create(
            code='TEST-SOON', title='Test upcoming event',
            date=date.today() + timedelta(days=30),
        )
        Member.objects.create(name='Test Artist', role='artist')
        BBNote.objects.create(title='Test note', url='https://note.com/brushbunni')

    def test_static_pages_render(self):
        for name in ['home', 'about', 'community', 'be_online', 'events',
                     'shop', 'project_bunni', 'members', 'contact']:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_event_detail_renders(self):
        url = reverse('event_detail', kwargs={'slug': self.past_event.slug})
        self.assertContains(self.client.get(url), 'Test past event')

    def test_inactive_event_detail_is_404(self):
        self.past_event.is_active = False
        self.past_event.save()
        url = reverse('event_detail', kwargs={'slug': self.past_event.slug})
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_events_page_splits_on_date(self):
        response = self.client.get(reverse('events'))
        self.assertIn(self.past_event, response.context['past_events'])
        self.assertIn(self.upcoming_event, response.context['upcoming_events'])

    def test_robots_txt_points_at_this_hosts_sitemap(self):
        response = self.client.get('/robots.txt')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sitemap: http://testserver/sitemap.xml')

    def test_sitemap_renders(self):
        self.assertEqual(self.client.get('/sitemap.xml').status_code, 200)


class PageContentTests(TestCase):
    """Editable page text overrides the hard-coded fallbacks."""

    def test_admin_text_replaces_the_default_heading(self):
        # Migration 0007 already seeds one row per page, so update rather than
        # create — `page` is unique.
        PageContent.objects.update_or_create(
            page='community',
            defaults={'heading': 'Our people',
                      'meta_description': 'A custom description.'},
        )
        response = self.client.get(reverse('community'))
        self.assertContains(response, 'Our people')
        self.assertContains(response, 'A custom description.')

    def test_page_renders_without_a_row(self):
        """A missing row must fall back to the default, never render blank."""
        PageContent.objects.filter(page='community').delete()
        self.assertContains(self.client.get(reverse('community')), 'Community')


class ContactFormTests(TestCase):
    def test_valid_message_is_stored(self):
        response = self.client.post(reverse('contact'), {
            'name': 'Ada', 'email': 'ada@example.com',
            'subject': 'Hello', 'message': 'Nice site.',
        })
        self.assertRedirects(response, reverse('contact'))
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_honeypot_submission_is_dropped_but_looks_successful(self):
        """Bots must not learn they were caught, so the response is identical."""
        response = self.client.post(reverse('contact'), {
            'name': 'Bot', 'email': 'bot@example.com',
            'subject': 'Spam', 'message': 'Buy things.',
            'website': 'http://spam.example.com',
        })
        self.assertRedirects(response, reverse('contact'))
        self.assertEqual(ContactMessage.objects.count(), 0)


class EventModelTests(TestCase):
    def test_status_follows_the_date_without_a_resave(self):
        """The bug this replaced: status was stored and went stale."""
        event = Event.objects.create(code='X-1', title='X',
                                     date=date.today() + timedelta(days=1))
        self.assertTrue(event.is_upcoming)
        self.assertEqual(event.status, 'upcoming')

        event.date = date.today() - timedelta(days=1)
        self.assertFalse(event.is_upcoming)
        self.assertEqual(event.status, 'past')

    def test_slug_is_derived_from_the_code(self):
        self.assertEqual(
            Event.objects.create(code='BBFESTA-9', title='Nine',
                                 date=date.today()).slug,
            'bbfesta-9',
        )

    def test_display_name_numbers_series_events(self):
        festa = Event.objects.create(code='BBFESTA-7', title='Seventh',
                                     event_type='bb_festa', date=date.today())
        self.assertEqual(festa.display_name, 'BB FESTA #7')

        workshop = Event.objects.create(code='WS-1', title='A workshop',
                                        event_type='workshop', date=date.today())
        self.assertEqual(workshop.display_name, 'A workshop')
