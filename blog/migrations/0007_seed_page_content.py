from django.db import migrations


# The text each page shows today, so the admin opens with something to edit
# rather than four blank forms.
SEED = [
    {
        'page': 'home',
        'heading': 'About Us',
        'intro': 'Welcome to Brush Bunni — where creativity meets community!',
    },
    {
        'page': 'community',
        'heading': 'Community',
        'intro': 'Welcome to the Brush Bunni community page!',
    },
    {
        'page': 'members',
        'heading': 'Members',
        'intro': 'Meet our community members!',
    },
    {
        'page': 'project_bunni',
        'heading': 'Project Bunni',
        'intro': '',
    },
]


def seed(apps, schema_editor):
    PageContent = apps.get_model('blog', 'PageContent')
    for row in SEED:
        PageContent.objects.get_or_create(page=row['page'], defaults=row)


def unseed(apps, schema_editor):
    PageContent = apps.get_model('blog', 'PageContent')
    PageContent.objects.filter(page__in=[r['page'] for r in SEED]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0006_pagecontent_alter_member_options_and_more'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
