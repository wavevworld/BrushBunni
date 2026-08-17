from django.db import migrations

# WACHAJ2 was stored with the date 2027-03-03. Nothing supports that date --
# it is a placeholder like the rest of the untouched rows -- but because it
# sits in the future it was the one row the site treated as a real upcoming
# event, so brushbunni.com was advertising a gathering that nobody has
# scheduled. That is worse than showing nothing.
#
# Hiding rather than deleting: the row owns 8 photographs of an event that did
# happen, and they should come back the moment someone supplies the real date.
# Flip is_active back to True in the admin once it is known.

SLUG = 'wachaj2'


def hide(apps, schema_editor):
    Event = apps.get_model('blog', 'Event')
    Event.objects.filter(slug=SLUG).update(is_active=False)


def unhide(apps, schema_editor):
    Event = apps.get_model('blog', 'Event')
    Event.objects.filter(slug=SLUG).update(is_active=True)


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0015_correct_festa_dates'),
    ]

    operations = [
        migrations.RunPython(hide, unhide),
    ]
