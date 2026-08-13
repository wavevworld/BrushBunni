# Clears data that a one-off seeder wrote and nobody ever replaced.
#
# Two provable placeholders, and only those:
#
#   * 7 EventPhoto captions reading "Photo from BBFESTA-N". They restate the
#     event the photo already belongs to, so the site rendered a caption under
#     each thumbnail that told the reader nothing.
#   * BBFESTA-1's start_time of 00:00, which the event page rendered as
#     "TIME 12:00 AM".
#
# The other seven events also carry odd-looking times (10:44, 11:17, 11:50 and
# friends — most likely whatever the clock said when the seeder ran). They are
# deliberately left alone: a junk 10:44 and a real 10:44 are indistinguishable
# from here, and nothing in the repo records the real ones.

from datetime import time

from django.db import migrations


def clear_placeholders(apps, schema_editor):
    EventPhoto = apps.get_model('blog', 'EventPhoto')
    Event = apps.get_model('blog', 'Event')

    EventPhoto.objects.filter(caption__startswith='Photo from ').update(caption='')
    Event.objects.filter(code='BBFESTA-1', start_time=time(0, 0)).update(start_time=None)


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0009_remove_dead_models'),
    ]

    operations = [
        # Irreversible on purpose: the values being cleared carry no
        # information, so there is nothing meaningful to restore.
        migrations.RunPython(clear_placeholders, migrations.RunPython.noop),
    ]
