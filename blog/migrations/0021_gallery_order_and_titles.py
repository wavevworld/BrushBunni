import re

from django.db import migrations

# Two things about the gallery.
#
# 1. Every one of the 71 pieces was called "Untitled #1" … "Untitled #12".
#    That was not the artists' naming — the work came from the six ARTIST
#    SPOTLIGHT posts on note.com, which publish the pieces without captions or
#    titles, so the importer numbered them. A made-up number is worse than no
#    title: it looks like data and carries none, and it is not the artist's
#    word. The titles are cleared, and the gallery card simply shows the work
#    and the credit until somebody enters a real one.
#
# 2. The folders sorted alphabetically, which put Christopher first purely
#    because of the letter C. They now run newest first, by the date each
#    artist's spotlight was published:
#
#      2025-11-06  MICHI
#      2025-09-18  TAKA YUKI
#      2025-08-21  RICHARD VINCENT SHIELDS
#      2025-08-07  KAY TANG
#      2025-05-22  Gabe Ramos
#      2025-04-24  Christopher T. Falkenberg
#
#    `order` carries this: rank * 100 + the piece's position in its article, so
#    artists stay grouped and each artist's pieces keep the sequence they were
#    published in. Gallery.Meta.ordering already sorts on `order`.

# Newest spotlight first.
ARTIST_ORDER = [
    'Michi',
    'Taka Yuki',
    'Richard Vincent Shields',
    'Kay Tang',
    'Gabe Ramos',
    'Christopher T. Falkenberg',
]

PLACEHOLDER = re.compile(r'^Untitled\s*#\d+$', re.I)
POSITION = re.compile(r'-(\d+)\.[a-z]+$', re.I)


def apply_order(apps, schema_editor):
    Gallery = apps.get_model('blog', 'Gallery')
    rank = {name: i for i, name in enumerate(ARTIST_ORDER)}

    for art in Gallery.objects.all():
        update = {}

        if PLACEHOLDER.match((art.title or '').strip()):
            update['title'] = ''

        # Anyone not in the list sorts after the six, keeping a stable place
        # rather than jumping to the front.
        position = POSITION.search(art.image.name or '')
        update['order'] = (rank.get(art.artist_name, len(ARTIST_ORDER)) * 100
                           + (int(position.group(1)) if position else 0))

        Gallery.objects.filter(pk=art.pk).update(**update)


def restore(apps, schema_editor):
    """Put the numbered placeholders back, per artist, in image order."""
    Gallery = apps.get_model('blog', 'Gallery')
    seen = {}
    for art in Gallery.objects.order_by('order', 'pk'):
        if art.title:
            continue
        seen[art.artist_name] = seen.get(art.artist_name, 0) + 1
        Gallery.objects.filter(pk=art.pk).update(
            title=f'Untitled #{seen[art.artist_name]}', order=0)


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0020_event_descriptions'),
    ]

    operations = [
        migrations.RunPython(apply_order, restore),
    ]
