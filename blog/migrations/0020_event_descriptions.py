from django.db import migrations

# Six events reached the site with no description at all — a title, a date and
# a row of photographs, and nothing telling a reader what the evening was.
# Everything below is taken from Brush Bunni's own note.com posts and from the
# event documents shared in their Discord. Nothing here is invented; where a
# fact was not in a source it simply is not stated.
#
# BB FESTA #1 — the event's own Google Doc, shared in the server:
#   "BrushBunni Festa! #1 (Concept art, 3DCG & Illustrations)", portfolio
#   review by art director 澤井藤彦 (Fujihiko Sawai), talk sessions by two
#   professional artists, plus a gallery. note.com adds that 33 artists from
#   different countries exhibited and that WACHAJACK helped make it possible.
#
# BB FESTA #2 / #3 — "BRUSHBUNNI FESTA! Event Information & Recap!"
#   (12 Jun 2025): #2 was "all about character design", "Held once again in
#   Harajuku, this summer event…"; #3 "was a collaboration with the French
#   comic bookstore Maison Petit Renard".
#
# BB FESTA #4 — the announcement (5 Jun 2025) and recap (10 Jul 2025):
#   "Special guests from VOXEL SCHOOL in Madrid and Fujihiko Sawai, CEO of
#   Japan's concept art studio WACHAJACK", a digital gallery of community
#   artwork, refreshments and networking, and "Thanks to the incredibly
#   generous support of Instituto Cervantes Tokyo".
#
# THUNDER GATHERERS — Kay Tang in #bb-announcements (6 Dec 2024): "a casual
#   meetup for artists in the game, film and animation industries in Tokyo".
#   Note this row's DATE is still unverified — only the description is being
#   filled in here.
#
# note_url is also set for #1 and #4, which have an article but were never
# linked to it. That link is what lets import_event_photos pull their pictures.

DESCRIPTIONS = {
    'bbfesta-1': {
        'short_description': (
            'Our first FESTA — concept art, 3DCG and illustration, '
            'in a Harajuku gallery.'
        ),
        'description': (
            "The very first BRUSHBUNNI FESTA. Fujihiko Sawai, art director at "
            "WACHAJACK, gave portfolio reviews, two professional artists gave "
            "talks, and we showed work by 33 artists from all over the "
            "world.\n\n"
            "WACHAJACK helped make it happen."
        ),
        'note_url': 'https://note.com/brushbunni/n/nf8a8134ce7f2',
    },
    'bbfesta-2': {
        'short_description': 'Character design, back in Harajuku.',
        'description': (
            "Our second FESTA, in a Harajuku gallery again. This one was all "
            "about character design."
        ),
    },
    'bbfesta-3': {
        'short_description': 'A FESTA about comics, with Maison Petit Renard.',
        'description': (
            "Our third FESTA was a collaboration with Maison Petit Renard, "
            "the French comic bookstore — so this one was about comics."
        ),
    },
    'bbfesta-4': {
        'short_description': (
            'Spanish Connection — concept art across two countries, '
            'at Instituto Cervantes Tokyo.'
        ),
        'description': (
            "Guests from VOXEL SCHOOL in Madrid joined Fujihiko Sawai, CEO of "
            "the concept art studio WACHAJACK, for an evening about "
            "international exchange and concept art.\n\n"
            "We showed a digital gallery of the community's work, then stayed "
            "to talk over drinks. Instituto Cervantes Tokyo gave us the venue."
        ),
        'note_url': 'https://note.com/brushbunni/n/n55e51dfd4ed2',
        'location': 'Instituto Cervantes Tokyo',
        'city': 'Tokyo',
    },
    'thung1': {
        'short_description': (
            'A casual meetup for artists in games, film and animation.'
        ),
        'description': (
            "THUNDER GATHERERS is Kay Tang's meetup series for artists "
            "working in the game, film and animation industries in Tokyo — a "
            "relaxed evening to meet people doing the same kind of work."
        ),
    },
}


def write(apps, schema_editor):
    Event = apps.get_model('blog', 'Event')
    for slug, fields in DESCRIPTIONS.items():
        # Only fill what is genuinely empty, so anything the owner has since
        # typed into the admin survives a re-run.
        for event in Event.objects.filter(slug=slug):
            update = {k: v for k, v in fields.items()
                      if not (getattr(event, k, '') or '').strip()}
            if update:
                Event.objects.filter(pk=event.pk).update(**update)


def clear(apps, schema_editor):
    Event = apps.get_model('blog', 'Event')
    for slug, fields in DESCRIPTIONS.items():
        for event in Event.objects.filter(slug=slug):
            revert = {k: '' for k, v in fields.items()
                      if (getattr(event, k, '') or '') == v}
            if revert:
                Event.objects.filter(pk=event.pk).update(**revert)


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0019_about_voice_and_wachaj'),
    ]

    operations = [
        migrations.RunPython(write, clear),
    ]
