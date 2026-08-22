# views.py — page views for the public site

import json

from django import forms
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Count, Q
from django.templatetags.static import static
from django.utils import timezone

from .models import Event, BBNote, ContactMessage, Gallery, Member, PageContent


class ContactForm(forms.ModelForm):
    # Honeypot: real users never see or fill this; bots tend to fill every field.
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Your name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'you@example.com'}),
            'subject': forms.TextInput(attrs={'placeholder': "What's this about?"}),
            'message': forms.Textarea(attrs={'placeholder': 'Your message...', 'rows': 6}),
        }

    def is_spam(self):
        return bool(self.data.get('website'))


def page_context(current_page, bg_image, title, description, **extra):
    """Shared per-page context.

    `title`/`description` feed <title>, og:title and twitter:title from a single
    place (see base.html), so social preview cards can never drift from the page.

    Editable text for this page (if the owner filled it in via the admin) is
    attached as `content`; a page-specific meta description there wins over the
    hard-coded fallback passed in here.
    """
    content = PageContent.objects.filter(page=current_page).first()

    context = {
        'current_page': current_page,
        'bg_image': bg_image,
        'page_title': title,
        'page_description': (content.meta_description if content and
                             content.meta_description else description),
        'content': content,
        # Sidebar email link. Empty until the address is configured, and
        # base.html omits the icon entirely rather than linking nowhere.
        'contact_email': settings.CONTACT_EMAIL,
        # Menu entries for pages that have nothing on them yet. Community and
        # Members each held a single welcome sentence, so the menu promised
        # content that was not there. These are computed rather than hardcoded
        # so the links come back on their own the moment there is something to
        # show — nobody has to remember to restore them.
        **_menu_visibility(),
    }
    context.update(extra)
    return context


def _menu_visibility():
    """Which thin pages are worth linking to right now.

    Members stays in the menu at the owner's request even while it is empty —
    profiles are coming — so the page carries an honest empty state instead.
    Community is still hidden until it has more than a welcome sentence.
    """
    community = PageContent.objects.filter(page='community').first()
    return {
        'show_members': True,
        'show_community': bool(community and community.body.strip()),
    }


DISCORD_INVITE = 'https://discord.com/invite/YWnYE4EHk5'


def home(request):
    """The landing page: who, where, and how to join, above the fold.

    It previously carried a heading and one generic sentence, so a first-time
    visitor learned neither the country nor what actually happens here.
    """
    today = timezone.localdate()
    past_events = Event.objects.filter(is_active=True, date__lt=today)
    latest_event = past_events.order_by('-date').first()

    artworks = Gallery.objects.filter(is_visible=True)

    # The counted row that used to sit here — events held, artists, works —
    # was removed at the owner's request: it read as a metrics dashboard on a
    # page whose whole message is "no pressure, just bring your sketchbook",
    # and the numbers are small enough to undersell the community. The cards
    # further down show the work itself, which does the job better.
    return render(request, 'blog/home.html', page_context(
        'home', 'blog/bg_about.jpg',
        "Brush Bunni — art community in Japan",
        "Brush Bunni is an art community in Japan for illustrators and "
        "creators — meet-ups and workshops in Tokyo and Kyoto, and a gallery "
        "of work by our members.",
        latest_event=latest_event,
        artwork_count=artworks.count(),
        # Every card needs a picture or the row reads as two empty boxes beside
        # a full one. The gallery borrows a featured piece as its cover.
        gallery_cover=artworks.order_by('-is_featured', 'order').first(),
        discord_invite=DISCORD_INVITE,
    ))


def community(request):
    return render(request, 'blog/community.html', page_context(
        'community', 'blog/bg_community.jpg',
        "Community — Brush Bunni",
        "Meet the Brush Bunni community: illustrators, painters and creators "
        "sharing work, feedback and events.",
    ))


def be_online(request):
    """BB Notes — links out to the community's note.com articles."""
    notes = BBNote.objects.filter(is_visible=True).order_by(
        '-is_pinned', 'order', '-published_date', '-created_at'
    )
    return render(request, 'blog/be_online.html', page_context(
        'be_online', 'blog/bg_online.jpg',
        "BB Notes — Brush Bunni",
        "Articles and notes from the Brush Bunni community, published on note.com.",
        notes=notes,
    ))


def events(request):
    """Events page with an upcoming/past split."""
    base = Event.objects.filter(is_active=True).prefetch_related('photos')

    # Split on the date itself. The old code filtered on a stored `status`
    # column that only updated when an event was re-saved, so finished events
    # kept showing under "Upcoming" indefinitely.
    today = timezone.localdate()
    past_events = base.filter(date__lt=today).order_by('order', '-date')
    upcoming_events = base.filter(date__gte=today).order_by('date', 'order')

    return render(request, 'blog/events.html', page_context(
        'events', 'blog/bg_events.jpg',
        "Events — Brush Bunni",
        "Upcoming and past Brush Bunni events: BB FESTA, Thunder Gatherers, "
        "workshops and exhibitions.",
        past_events=past_events,
        upcoming_events=upcoming_events,
        # When nothing is scheduled, the page said only "Nothing scheduled
        # yet" — which reads as a community that stopped meeting. Showing when
        # we last met, and where the next date gets announced, says the
        # opposite with the same honesty.
        last_event=past_events.order_by('-date').first(),
        discord_invite=DISCORD_INVITE,
    ))


def shop(request):
    return render(request, 'blog/shop.html', page_context(
        'shop', 'blog/bg_shop.jpg',
        "Shop — Brush Bunni",
        "Brush Bunni merch and goods.",
    ))


def project_bunni(request):
    return render(request, 'blog/project_bunni.html', page_context(
        'project_bunni', 'blog/bg_shop.jpg',
        "Project Bunni — Brush Bunni",
        "Project Bunni — a Brush Bunni community project.",
        project_image='blog/images/PJBUNNI.jpg',
    ))


def members(request):
    # annotate so a card can say how many pieces a member has without a query
    # per card in the template.
    people = Member.objects.filter(is_visible=True).annotate(
        artwork_count=Count('artworks', filter=Q(artworks__is_visible=True))
    )
    return render(request, 'blog/members.html', page_context(
        'members', 'blog/bg_members.jpg',
        "Members — Brush Bunni",
        "Meet the members of the Brush Bunni art community.",
        members=people,
    ))


def member_detail(request, slug):
    """One member's profile, with the artwork credited to them."""
    member = get_object_or_404(Member, slug=slug, is_visible=True)
    artworks = member.artworks.filter(is_visible=True).select_related('event')

    return render(request, 'blog/member_detail.html', page_context(
        'members', 'blog/bg_members.jpg',
        f"{member.name} — Brush Bunni",
        member.bio[:160] or f"{member.name} — {member.get_role_display()} "
                            f"in the Brush Bunni art community.",
        member=member,
        artworks=artworks,
        og_image=member.avatar.url if member.avatar else None,
        og_type='profile',
    ))


def gallery(request):
    """Community artwork, optionally filtered to one artist or one event.

    The filters are read from the querystring rather than being separate URLs
    so a filtered view stays shareable and needs no extra routes.
    """
    artworks = (Gallery.objects.filter(is_visible=True)
                .select_related('artist', 'event'))

    artist_slug = request.GET.get('artist', '')
    event_slug = request.GET.get('event', '')
    # Guest artists have no Member row and so no slug; they are opened by name.
    credit_name = request.GET.get('credit', '')

    all_visible = list(artworks)

    if artist_slug:
        artworks = artworks.filter(artist__slug=artist_slug)
    if credit_name:
        artworks = artworks.filter(artist__isnull=True, artist_name=credit_name)
    if event_slug:
        artworks = artworks.filter(event__slug=event_slug)

    # Only offer a filter for artists/events that actually have visible work,
    # so the pill row can never lead to an empty grid.
    artists = Member.objects.filter(
        is_visible=True, artworks__is_visible=True).distinct()
    events = Event.objects.filter(
        is_active=True, artworks__is_visible=True).distinct()

    # With nothing selected the page shows one folder per artist; opening a
    # folder shows that artist's work. A single wall of every piece made it
    # impossible to see whose work was whose.
    browsing_folders = not (artist_slug or credit_name or event_slug)
    folders = build_artist_folders(all_visible) if browsing_folders else []
    open_folder = folder_title(artworks) if not browsing_folders else ""

    return render(request, 'blog/gallery.html', page_context(
        'gallery', 'blog/bg_community.jpg',
        "Gallery — Brush Bunni",
        "Artwork from the Brush Bunni community — paintings, illustrations "
        "and pieces shown at our events.",
        browsing_folders=browsing_folders,
        folders=folders,
        open_folder=open_folder,
        groups=group_by_artist(artworks),
        artwork_count=len(artworks),
        artists=artists,
        events=events,
        active_artist=artist_slug,
        active_event=event_slug,
    ))


def build_artist_folders(artworks):
    """One entry per artist: a cover image, a count and a way in.

    Folders follow the order of the artwork itself — newest artist first — not
    the alphabet. Sorting on the name put Christopher at the front for no
    reason other than the letter C, while the most recently featured artist
    was buried at the bottom. `rank` records where each artist first appears
    in the (already ordered) queryset.
    """
    folders = {}
    for position, art in enumerate(artworks):
        folder = folders.setdefault(art.credit, {
            'name': art.credit, 'artist': None, 'cover': art, 'count': 0,
            'rank': position,
        })
        folder['count'] += 1
        if art.artist and not folder['artist']:
            folder['artist'] = art.artist
        # Prefer a featured piece as the cover when there is one.
        if art.is_featured and not folder['cover'].is_featured:
            folder['cover'] = art
    return sorted(folders.values(), key=lambda f: f['rank'])


def folder_title(artworks):
    """What to call the open folder, for the heading and the back link."""
    first = artworks[0] if artworks else None
    return first.credit if first else ""


def group_by_artist(artworks):
    """Collect the artwork under one heading per artist.

    A flat wall of images makes it impossible to see whose work is whose, which
    is the wrong emphasis for a community gallery — the artists are the point.
    Sorting is by name so the page order does not shuffle when a piece is
    added, and pieces keep their own order within an artist.
    """
    buckets = {}
    for art in artworks:
        key = art.credit
        bucket = buckets.setdefault(key, {'name': key, 'artist': None, 'items': []})
        bucket['items'].append(art)
        # A Member link, if any one of the pieces has one.
        if art.artist and not bucket['artist']:
            bucket['artist'] = art.artist

    return sorted(buckets.values(), key=lambda b: b['name'].lower())


def contact(request):
    context = page_context(
        'contact', 'blog/bg_contact.jpg',
        "Contact Us — Brush Bunni",
        "Get in touch with Brush Bunni — questions, collaborations and event enquiries.",
    )

    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Drop bot submissions silently (honeypot filled) but pretend success.
            if not form.is_spam():
                form.save()
            messages.success(request, "Thanks! Your message has been sent — we'll get back to you soon.")
            return redirect('contact')
    else:
        form = ContactForm()

    context['form'] = form
    return render(request, 'blog/contact.html', context)


def favicon(request):
    """Browsers request /favicon.ico regardless of the <link> tags in <head>.

    The static path is resolved per request, not at import time: with the
    hashed-filename storage that lookup needs the manifest, which only exists
    after collectstatic has run.
    """
    return redirect(static('blog/favicon-32.png'), permanent=True)


def robots_txt(request):
    """Served from a view so the sitemap URL always matches the live host."""
    sitemap_url = request.build_absolute_uri('/sitemap.xml')
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "",
        f"Sitemap: {sitemap_url}",
        "",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def event_detail(request, slug):
    """Single event detail page."""
    event = get_object_or_404(Event, slug=slug, is_active=True)

    event_photos = event.photos.all().order_by('order', '-is_featured', '-uploaded_at')

    related_events = Event.objects.filter(
        is_active=True, event_type=event.event_type
    ).exclude(pk=event.pk).order_by('order', '-date')[:3]

    if not related_events:
        related_events = Event.objects.filter(
            is_active=True
        ).exclude(pk=event.pk).order_by('-date')[:3]

    # The first photo doubles as the hero backdrop and the social preview.
    hero_photo = event_photos.first()
    og_image = hero_photo.image.url if hero_photo and hero_photo.image else None

    return render(request, 'blog/event_detail.html', page_context(
        'events', 'blog/bg_events.jpg',
        f"{event.title} — Brush Bunni",
        event.short_description or event.description[:160] or
        f"{event.title} — a Brush Bunni event.",
        event=event,
        event_photos=event_photos,
        hero_photo=hero_photo,
        related_events=related_events,
        og_image=og_image,
        og_type='article',
        event_schema=build_event_schema(request, event, hero_photo),
    ))


def build_event_schema(request, event, hero_photo):
    """schema.org/Event as JSON-LD.

    The audit's point was that these events do not exist for search: the facts
    lived in screenshots. The page already shows the date and venue as text —
    this states them in a form a search engine can actually parse.

    Returned as a JSON string; json.dumps escapes the characters that could
    otherwise close the surrounding <script> tag early.
    """
    data = {
        '@context': 'https://schema.org',
        '@type': 'Event',
        'name': event.display_name,
        'startDate': _iso_start(event),
        'eventStatus': 'https://schema.org/EventScheduled',
        'eventAttendanceMode': (
            'https://schema.org/OnlineEventAttendanceMode' if event.is_online
            else 'https://schema.org/OfflineEventAttendanceMode'),
        'url': request.build_absolute_uri(event.get_absolute_url()),
        'organizer': {
            '@type': 'Organization',
            'name': 'Brush Bunni',
            'url': request.build_absolute_uri('/'),
        },
    }

    description = event.short_description or event.description
    if description:
        data['description'] = description[:300]

    if hero_photo and hero_photo.image:
        data['image'] = [request.build_absolute_uri(hero_photo.image.url)]

    # Only claim a place when there is one; an Event with an empty location is
    # worse than an Event with none.
    if event.is_online:
        data['location'] = {'@type': 'VirtualLocation',
                            'url': request.build_absolute_uri(event.get_absolute_url())}
    elif event.location or event.city:
        place = {'@type': 'Place', 'name': event.location or event.city}
        if event.city:
            place['address'] = {'@type': 'PostalAddress',
                                'addressLocality': event.city,
                                'addressCountry': 'JP'}
        data['location'] = place

    if event.registration_url:
        data['offers'] = {
            '@type': 'Offer',
            'url': event.registration_url,
            'availability': 'https://schema.org/InStock',
        }

    return json.dumps(data, ensure_ascii=False)


def _iso_start(event):
    """Date, with the time appended only when we actually know it."""
    if event.start_time:
        return f"{event.date.isoformat()}T{event.start_time.isoformat()}"
    return event.date.isoformat()
