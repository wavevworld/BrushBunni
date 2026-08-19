from datetime import date, time

from django.db import migrations

# Two things, both about saying less and meaning more.
#
# 1. The About text, shortened and put back into Matilda's own voice. The
#    previous version was already built from her note.com writing but had grown
#    to three paragraphs. Her register is short sentences, "we", the odd
#    exclamation mark, no polish:
#      "We aren't about competition or chasing perfection. We're about showing
#       up, sharing what you love, and cheering each other on."
#      "There's zero pressure, just bring yourself, curiosity, and maybe your
#       sketchbook!"
#    The one new fact comes from #bb-rules on Discord: "We do not allow in this
#    server AI generated art". For an art community that is worth saying out
#    loud on the About page.
#
# 2. WACHAJ was a code, not a name. The card on the front page read
#    "Wachaj - 7 June 2026" over a poster for something else entirely, which
#    told a visitor nothing and was not even true.
#    The row's single photo turned out to be the event's real poster:
#      「描く前に考える コンセプトアーティストのアイデア発想術」
#      9月6日(土) 14:00-19:00 出町ガジェット京都
#      FUJIHIKO SAWAI / JULIEN GAUTHIER
#    Confirmed by note.com, "A Rare Creative Opportunity in Kyoto" (15 Aug
#    2025): "Saturday, September 6th  Time: 14:00 - 19:00 (Doors open 13:30)",
#    "Demachi Gadget Kyoto", Fujihiko Sawai "Art Director & CEO, WACHAJACK"
#    and Julien Gauthier "International Art Director & Concept Artist".
#    6 September fell on a Saturday in 2025, matching the (土) on the poster.
#    Stored was 2026-06-07 — a placeholder, and in the future, which is why it
#    was being advertised as the most recent thing that happened.

INTRO = (
    "We're an international art community based in Japan. We meet up in Tokyo "
    "and Kyoto, and the rest of the time we're on Discord."
)

BODY = (
    "Brush Bunni is built on two simple things: kindness and support. We "
    "aren't about competition or chasing perfection — we're about showing up, "
    "sharing what you love, and cheering each other on.\n\n"
    "Whatever your level, there's room for you here. We talk in English, "
    "Japanese and Spanish. No AI art, and no pressure — just bring yourself, "
    "your curiosity, and maybe your sketchbook!"
)

WACHAJ = {
    'title': 'Thinking Before You Draw',
    'date': date(2025, 9, 6),
    'start_time': time(14, 0),
    'end_time': time(19, 0),
    'location': 'Demachi Gadget',
    'city': 'Kyoto',
    'event_type': 'workshop',
    'short_description': (
        'An afternoon in Kyoto with concept artists Fujihiko Sawai and '
        'Julien Gauthier, on how to build an idea before you start drawing.'
    ),
    'description': (
        "Our first event in Kyoto, held with WACHAJACK — the concept art "
        "studio Fujihiko Sawai runs, with offices in Japan and Madrid.\n\n"
        "Fujihiko Sawai and Julien Gauthier talked about how concept artists "
        "come up with strong ideas before the sketching starts. Then everyone "
        "drew, got feedback on the spot, and stayed to talk to each other."
    ),
    'note_url': 'https://note.com/brushbunni/n/n49f467da338b',
}

PREVIOUS_WACHAJ = {
    'title': 'WACHAJ',
    'date': date(2026, 6, 7),
    'start_time': time(10, 0),
    'end_time': time(15, 0),
    'location': '',
    'city': '',
    'event_type': 'bb_festa',
    'short_description': '',
    'description': '',
    'note_url': '',
}

OLD_INTRO = (
    "An international art community based in Japan. We hold meet-ups and "
    "exhibitions in Tokyo and Kyoto, and the rest of the time we're on Discord."
)

OLD_BODY = (
    "Brush Bunni is built on two simple ideas: kindness and support. We aren't "
    "about competition or chasing perfection — we're about showing up, "
    "sharing what you love, and cheering each other on.\n\n"
    "Whatever your level or background, there's room for you here. Our main "
    "language is English, but Japanese and Spanish are spoken every day. "
    "There's zero pressure — just bring yourself, curiosity, and maybe "
    "your sketchbook."
)


def apply(apps, schema_editor, intro, body, old_intro, old_body, wachaj):
    PageContent = apps.get_model('blog', 'PageContent')
    Event = apps.get_model('blog', 'Event')

    # Leave the page alone if somebody has since written their own text.
    for page in PageContent.objects.filter(page='home'):
        if page.intro.strip() in ('', old_intro):
            page.intro = intro
        if page.body.strip() in ('', old_body):
            page.body = body
        page.save(update_fields=['intro', 'body'])

    Event.objects.filter(slug='wachaj').update(**wachaj)


def forwards(apps, schema_editor):
    apply(apps, schema_editor, INTRO, BODY, OLD_INTRO, OLD_BODY, WACHAJ)


def backwards(apps, schema_editor):
    apply(apps, schema_editor, OLD_INTRO, OLD_BODY, INTRO, BODY, PREVIOUS_WACHAJ)


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0018_plain_language_labels_3'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
