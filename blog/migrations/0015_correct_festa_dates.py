from datetime import date, time

from django.db import migrations

# The two BB FESTA rows carried placeholder dates. Both are corrected here to
# dates that are sourced, not guessed -- every other event row is left alone
# because no evidence for it exists yet.
#
# BB FESTA #1 -- Friday 19 April 2024, 19:00, Harajuku, Tokyo
#   - BB_Matilda, Discord #bb-日本語チャット, 1 Mar 2024:
#     「初イベントは4月19日（金）に東京の原宿で開催します！」
#   - Google Doc shared in the server, titled "BrushBunni Festa! #1 (Concept
#     art, 3DCG & Illustrations) April 19th", body: 「4月19日(金)19:00～原宿です」
#   - note.com, "BRUSHBUNNI FESTA! Event Information & Recap!" (12 Jun 2025):
#     "Our very first BRUSHBUNNI FESTA! was held in April last year in
#     Harajuku." -> April 2024
#   - note.com, "BRUSHBUNNI FESTA! #1" (13 Mar 2025): "Last April, we hosted
#     our first-ever BRUSHBUNNI FESTA! event in Harajuku."
#   19 April 2024 fell on a Friday, which matches the 金 in both Japanese
#   sources. Stored was 2026-01-08 -- about 21 months out, and it placed #1
#   after #2.
#
# BB FESTA #4 -- Saturday 5 July 2025, 17:00-19:00, Instituto Cervantes Tokyo
#   - note.com, same recap article: "Date: Saturday, July 5th, 17:00–19:00
#     Venue: Instituto Cervantes Tokyo"
#   - note.com, "BRUSHBUNNI FESTA! #4 is THIS SATURDAY in TOKYO" (3 Jul 2025)
#   - note.com recap (10 Jul 2025):「7月5日に、第4回BRUSHBUNNI FESTA!を開催しました！」
#   Stored was 2024-01-01 with 13:00-17:00 -- the date 18 months out and the
#   times wrong too.

CORRECTIONS = {
    'bbfesta-1': {
        'date': date(2024, 4, 19),
        'start_time': time(19, 0),
        'end_time': None,
        'location': 'Harajuku',
        'city': 'Tokyo',
    },
    'bbfesta-4': {
        'date': date(2025, 7, 5),
        'start_time': time(17, 0),
        'end_time': time(19, 0),
        'location': 'Instituto Cervantes Tokyo',
        'city': 'Tokyo',
    },
}

# What was there before, so the migration reverses cleanly.
PREVIOUS = {
    'bbfesta-1': {
        'date': date(2026, 1, 8),
        'start_time': None,
        'end_time': None,
        'location': '',
        'city': '',
    },
    'bbfesta-4': {
        'date': date(2024, 1, 1),
        'start_time': time(13, 0),
        'end_time': time(17, 0),
        'location': '',
        'city': '',
    },
}


def apply_values(apps, values):
    Event = apps.get_model('blog', 'Event')
    for slug, fields in values.items():
        # Not get() -- a missing row on another database should not blow up the
        # migration, it just means there is nothing to correct there.
        Event.objects.filter(slug=slug).update(**fields)


def correct_dates(apps, schema_editor):
    apply_values(apps, CORRECTIONS)


def restore_dates(apps, schema_editor):
    apply_values(apps, PREVIOUS)


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0014_about_page_copy'),
    ]

    operations = [
        migrations.RunPython(correct_dates, restore_dates),
    ]
