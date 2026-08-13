# Gives Member a URL slug and turns Gallery into a real model.
#
# The slug is added in three steps rather than one. Adding a unique column to a
# table that already has rows hands every one of them the same empty string,
# which trips the constraint the moment there is more than one member. Local
# has none; production may. So: add it nullable and unconstrained, fill it in,
# then apply the constraint.

import django.db.models.deletion
from django.db import migrations, models
from django.utils.text import slugify


def populate_member_slugs(apps, schema_editor):
    Member = apps.get_model('blog', 'Member')
    seen = set()
    for member in Member.objects.all().order_by('pk'):
        # Mirrors Member._unique_slug(); duplicated because migrations must not
        # call model methods that may change shape in a later release.
        base = slugify(member.name) or "member"
        slug, n = base, 2
        while slug in seen:
            slug = f"{base}-{n}"
            n += 1
        seen.add(slug)
        member.slug = slug
        member.save(update_fields=['slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0010_clear_placeholder_event_data'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='gallery',
            options={'ordering': ['-is_featured', 'order', '-created_at'],
                     'verbose_name': 'Artwork', 'verbose_name_plural': 'Gallery'},
        ),
        migrations.AddField(
            model_name='gallery',
            name='artist_name',
            field=models.CharField(blank=True, max_length=120, help_text='Credit for an artist who is not on the Members page. Ignored when an artist is chosen above.'),
        ),
        migrations.AddField(
            model_name='gallery',
            name='event',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='artworks', to='blog.event', help_text='Optional: the event this was shown at'),
        ),
        migrations.AddField(
            model_name='gallery',
            name='is_visible',
            field=models.BooleanField(default=True, help_text='Show on the website'),
        ),
        migrations.AddField(
            model_name='gallery',
            name='order',
            field=models.PositiveIntegerField(default=0, help_text='Lower numbers appear first'),
        ),
        migrations.AlterField(
            model_name='gallery',
            name='artist',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='artworks', to='blog.member'),
        ),
        migrations.AlterField(
            model_name='gallery',
            name='is_featured',
            field=models.BooleanField(default=False, help_text='Show first'),
        ),

        # --- Member.slug, in three safe steps ---
        migrations.AddField(
            model_name='member',
            name='slug',
            field=models.SlugField(max_length=120, blank=True, null=True),
        ),
        migrations.RunPython(populate_member_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='member',
            name='slug',
            field=models.SlugField(max_length=120, unique=True, blank=True,
                                   help_text='Auto-filled from the name; used in the profile page URL'),
        ),
    ]
