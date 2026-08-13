# views.py — page views for the public site

from django import forms
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.templatetags.static import static
from django.utils import timezone

from .models import Event, BBNote, ContactMessage, Member, PageContent


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
    }
    context.update(extra)
    return context


def home(request):
    return render(request, 'blog/home.html', page_context(
        'home', 'blog/bg_about.jpg',
        "About Us — Brush Bunni",
        "Brush Bunni is an art community where creativity meets community — "
        "events, workshops and a place for illustrators and creators to meet.",
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
    return render(request, 'blog/members.html', page_context(
        'members', 'blog/bg_members.jpg',
        "Members — Brush Bunni",
        "Meet the members of the Brush Bunni art community.",
        members=Member.objects.filter(is_visible=True),
    ))


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
    ))
