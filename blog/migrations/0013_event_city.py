# Splits the city out of the venue string so search engines can read where an
# event happened. Previously "Shibuya LUSH, Shibuya, Tokyo" was one opaque
# field, which schema.org cannot break down into an address.

from django.db import migrations, models

# Only cities that appear verbatim in the existing venue strings. This reads a
# value that is already there rather than inferring one — an event whose venue
# names no city is left blank for the owner to fill, not guessed at.
KNOWN_CITIES = ['Kyoto', 'Tokyo', 'Osaka']


def split_city_from_venue(apps, schema_editor):
    Event = apps.get_model('blog', 'Event')
    for event in Event.objects.exclude(location=''):
        parts = [p.strip() for p in event.location.split(',')]
        for city in KNOWN_CITIES:
            if parts and parts[-1] == city:
                event.city = city
                # Leave the venue as the part before the city.
                remainder = ', '.join(parts[:-1]).strip()
                event.location = remainder or city
                event.save(update_fields=['city', 'location'])
                break


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0012_plain_language_labels'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='city',
            field=models.CharField(blank=True, help_text='Kyoto, Tokyo, and so on. Kept separate from the venue so search engines can read where the event was held.', max_length=100),
        ),
        migrations.AlterField(
            model_name='event',
            name='is_online',
            field=models.BooleanField(default=False, help_text='Tick for events with no physical venue.', verbose_name='Online event'),
        ),
        migrations.AlterField(
            model_name='event',
            name='location',
            field=models.CharField(blank=True, help_text='The place itself, e.g. "Demachi Gadget, Demachiyanagi".', max_length=200, verbose_name='Venue'),
        ),
        # Irreversible on purpose: the reverse would have to guess how to glue
        # the city back on, and the original string is not worth reconstructing.
        migrations.RunPython(split_city_from_venue, migrations.RunPython.noop),
    ]
