# Drops six models that were never wired to anything: no view, no URL, no
# template, no admin registration, and zero rows in every environment checked.
# Post/EventImage were only reachable from two one-off import commands, deleted
# in the same change. Gallery keeps its table — it gets a real implementation
# next — but loses the FK to the Category model going away here.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0008_seed_real_events'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='category',
        ),
        migrations.RemoveField(
            model_name='gallery',
            name='category',
        ),
        migrations.RemoveField(
            model_name='eventimage',
            name='event',
        ),
        migrations.DeleteModel(
            name='NewsletterSubscriber',
        ),
        migrations.RemoveField(
            model_name='post',
            name='author',
        ),
        migrations.DeleteModel(
            name='SiteConfiguration',
        ),
        migrations.DeleteModel(
            name='Product',
        ),
        migrations.DeleteModel(
            name='Category',
        ),
        migrations.DeleteModel(
            name='EventImage',
        ),
        migrations.DeleteModel(
            name='Post',
        ),
    ]
