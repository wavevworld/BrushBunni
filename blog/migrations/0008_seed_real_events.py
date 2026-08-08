from django.db import migrations


# Real, sourced events pulled from note.com/brushbunni (see note_url on each).
# Deliberately NOT touching the 8 existing Event rows: their dates/venues/
# descriptions are all blank or look like placeholder data, and none of them
# line up with any date found in the note.com archive, so guessing which
# is which would risk publishing wrong facts under the wrong event.
SEED = [
    {
        'code': 'KYOTO-0925',
        'title': 'Kyoto Gathering: Fear & Beauty with Kay Tang',
        'event_type': 'community',
        'date': '2025-09-27',
        'location': 'Kyoto',
        'short_description': (
            'A casual Kyoto meetup with a talk on creative fear, and treats '
            'from Kitaharashouten.'
        ),
        'description': (
            'Guest speaker Kay Tang (@kaytaart) led a discussion titled '
            '"Fear & Beauty" about the emotional side of making art — the '
            'fear of failing, of being judged, of not being good enough.\n\n'
            'Kitaharashouten provided dagashi (old-style Japanese candy and '
            'snacks) to share. Some people opened their sketchbooks, others '
            'simply talked and made new friends.'
        ),
        'note_url': 'https://note.com/brushbunni/n/n6a3a3beb3c85',
    },
    {
        'code': 'KYOTO-WACHAJACK-1225',
        'title': 'A Creative Day in Kyoto with WACHAJACK',
        'event_type': 'workshop',
        'date': '2025-12-13',
        'location': 'Demachi Gadget, Demachiyanagi, Kyoto',
        'short_description': (
            'A talk and drawing workshop with concept artist Azusa Tojo, '
            'hosted with WACHAJACK Kyoto.'
        ),
        'description': (
            'Concept artist, visual development artist and Blender teacher '
            'Azusa Tojo shared her journey in the concept art industry — '
            'working abroad, the challenges along the way, and advice and '
            'resources for people starting out.\n\n'
            'Afterwards everyone moved downstairs at Demachi Gadget (a '
            'machiya-style maker space run by BASSDRUM) for Kyoto treats and '
            'tea while Azusa demonstrated techniques in Heavy Paint. Many '
            'attendees were not concept artists, which brought perspectives '
            'from other creative fields into the conversation.\n\n'
            'WACHAJACK plans more events like this through the year, with a '
            'variety of speakers and themes.'
        ),
        'note_url': 'https://note.com/brushbunni/n/n9320b47a1e2b',
    },
    {
        'code': 'ETO-NIGHT-1',
        'title': 'Eto Night vol.1',
        'event_type': 'exhibition',
        'date': '2025-10-04',
        'start_time': '17:00',
        'end_time': '22:00',
        'location': 'Shibuya LUSH, Shibuya, Tokyo',
        'short_description': (
            'A live art night in Shibuya — live sculpting, an art & merch '
            'sale, and a music set by SEICHAN.'
        ),
        'description': (
            'An evening of art and music in Shibuya: an exhibition and '
            'merchandise sale alongside live sculpting, where artists built '
            'a sculpture from scratch in front of the audience.\n\n'
            'Music came from Taiwanese-Japanese singer-songwriter SEICHAN, '
            "followed by a DJ set from SEICHAN's Merry Crew, with food from "
            "Tokyo Mabo (東京麻婆).\n\n"
            'Participating artists: Yuuki Morita, Hajime Tanno, Hiroaki '
            'Nakanishi, Daiki Miyama, Saekiniko and Tatsuyuki Shimada, with '
            'merchandise from Kazuma Murata.'
        ),
        'note_url': 'https://note.com/brushbunni/n/nc8c25dfbf0a6',
    },
]


def seed(apps, schema_editor):
    Event = apps.get_model('blog', 'Event')
    from django.utils.text import slugify

    for row in SEED:
        row = dict(row)
        code = row.pop('code')
        if Event.objects.filter(code=code).exists():
            continue
        Event.objects.create(
            code=code,
            slug=slugify(code),
            is_active=True,
            **row,
        )


def unseed(apps, schema_editor):
    Event = apps.get_model('blog', 'Event')
    Event.objects.filter(code__in=[r['code'] for r in SEED]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0007_seed_page_content'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
