"""Smoke tests for the public site.

Deliberately shallow: they assert that every public URL renders at all. That is
the check nothing else was making — a template typo or a view referencing a
deleted model would previously only show up by loading the page by hand.
"""

from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from .models import Event, BBNote, ContactMessage, Gallery, Member, PageContent


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


class MemberSlugTests(TestCase):
    def test_slug_is_derived_from_the_name(self):
        self.assertEqual(Member.objects.create(name='Kay Tang').slug, 'kay-tang')

    def test_duplicate_names_get_distinct_slugs(self):
        """Two people can share a name; the URL cannot."""
        a = Member.objects.create(name='Alex')
        b = Member.objects.create(name='Alex')
        self.assertEqual(a.slug, 'alex')
        self.assertEqual(b.slug, 'alex-2')

    def test_non_latin_name_still_gets_a_usable_slug(self):
        """slugify() returns '' for Japanese, which would break the URL."""
        member = Member.objects.create(name='東條あずさ')
        self.assertTrue(member.slug)
        self.assertEqual(member.slug, 'member')

    def test_slug_survives_a_rename(self):
        """Renaming must not break links that already point at the profile."""
        member = Member.objects.create(name='Original Name')
        member.name = 'New Name'
        member.save()
        self.assertEqual(member.slug, 'original-name')


class GalleryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.artist = Member.objects.create(name='Kay Tang', role='artist')
        cls.event = Event.objects.create(code='GAL-1', title='Gallery event',
                                         date=date.today() - timedelta(days=5))
        cls.piece = Gallery.objects.create(
            title='Red Oni', artist=cls.artist, event=cls.event,
            image='gallery/test.jpg')
        cls.guest = Gallery.objects.create(
            title='Guest piece', artist_name='Visiting Artist',
            image='gallery/guest.jpg')

    def test_gallery_page_lists_visible_artwork(self):
        response = self.client.get(reverse('gallery'))
        self.assertContains(response, 'Red Oni')
        self.assertContains(response, 'Guest piece')

    def test_hidden_artwork_is_not_listed(self):
        self.piece.is_visible = False
        self.piece.save()
        self.assertNotContains(self.client.get(reverse('gallery')), 'Red Oni')

    def test_filter_by_artist(self):
        response = self.client.get(reverse('gallery'), {'artist': self.artist.slug})
        self.assertContains(response, 'Red Oni')
        self.assertNotContains(response, 'Guest piece')

    def test_filter_by_event(self):
        response = self.client.get(reverse('gallery'), {'event': self.event.slug})
        self.assertContains(response, 'Red Oni')
        self.assertNotContains(response, 'Guest piece')

    def test_credit_falls_back_to_free_text_for_a_guest(self):
        self.assertEqual(self.guest.credit, 'Visiting Artist')
        self.assertEqual(self.piece.credit, 'Kay Tang')

    def test_deleting_a_member_keeps_their_artwork(self):
        """SET_NULL, not CASCADE — removing a profile must not destroy the art."""
        self.artist.delete()
        self.piece.refresh_from_db()
        self.assertIsNone(self.piece.artist)
        self.assertEqual(self.piece.credit, 'Unknown artist')
        self.assertEqual(self.client.get(reverse('gallery')).status_code, 200)

    def test_deleting_an_event_keeps_the_artwork(self):
        self.event.delete()
        self.piece.refresh_from_db()
        self.assertIsNone(self.piece.event)


class MemberDetailTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.member = Member.objects.create(name='Kay Tang', role='artist',
                                           bio='Paints oni masks.')
        Gallery.objects.create(title='Red Oni', artist=cls.member,
                               image='gallery/test.jpg')

    def test_profile_shows_the_member_and_their_work(self):
        response = self.client.get(self.member.get_absolute_url())
        self.assertContains(response, 'Kay Tang')
        self.assertContains(response, 'Paints oni masks.')
        self.assertContains(response, 'Red Oni')

    def test_hidden_member_profile_is_404(self):
        self.member.is_visible = False
        self.member.save()
        self.assertEqual(self.client.get(self.member.get_absolute_url()).status_code, 404)

    def test_members_list_links_to_the_profile(self):
        response = self.client.get(reverse('members'))
        self.assertContains(response, self.member.get_absolute_url())

    def test_members_list_counts_only_visible_artwork(self):
        Gallery.objects.create(title='Hidden', artist=self.member,
                               image='gallery/h.jpg', is_visible=False)
        response = self.client.get(reverse('members'))
        person = response.context['members'][0]
        self.assertEqual(person.artwork_count, 1)
