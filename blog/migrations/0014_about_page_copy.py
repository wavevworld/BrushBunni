from django.db import migrations

# The About page said "Welcome to Brush Bunni - where creativity meets
# community!" and nothing else -- its body was empty. That sentence could have
# belonged to any community anywhere: it named no country, no city, no craft,
# and gave a first-time visitor no reason to join.
#
# The replacement is not new copy. It is Brush Bunni's own wording, taken from
# their note.com articles so the page sounds like them rather than like a
# website:
#   "Why Creative Communities Like BrushBunni Matter"  (10 Apr 2025)
#     - "built on two simple but powerful ideas: kindness and support"
#     - "We aren't about competition or chasing perfection. We're about showing
#        up, sharing what you love, and cheering each other on."
#   "Foreign Communication - The Possibilities with an International Community"
#   (15 May 2025)
#     - "Our main language is English, but Japanese and Spanish are also
#        commonly used."
#     - "There's zero pressure, just bring yourself, curiosity, and maybe your
#        sketchbook!"
#   note.com profile: "International Art Community based in Japan!"
#
# These are Page texts, so Matilda can still rewrite every word in the admin
# without a deploy. This migration only replaces the placeholder.

INTRO = (
    "An international art community based in Japan. We hold meet-ups and "
    "exhibitions in Tokyo and Kyoto, and the rest of the time we're on Discord."
)

BODY = (
    "Brush Bunni is built on two simple ideas: kindness and support. We aren't "
    "about competition or chasing perfection — we're about showing up, "
    "sharing what you love, and cheering each other on.\n\n"
    "Whatever your level or background, there's room for you here. Our main "
    "language is English, but Japanese and Spanish are spoken every day. "
    "There's zero pressure — just bring yourself, curiosity, and maybe "
    "your sketchbook."
)

OLD_INTRO = "Welcome to Brush Bunni — where creativity meets community!"


def write_about_copy(apps, schema_editor):
    PageContent = apps.get_model('blog', 'PageContent')
    # Only touch the row if it still holds the placeholder -- if the owner has
    # already written their own text, leave it alone.
    for page in PageContent.objects.filter(page='home'):
        if page.intro.strip() in ('', OLD_INTRO, OLD_INTRO.replace('—', '-')):
            page.intro = INTRO
        if not page.body.strip():
            page.body = BODY
        page.save(update_fields=['intro', 'body'])


def restore_placeholder(apps, schema_editor):
    PageContent = apps.get_model('blog', 'PageContent')
    for page in PageContent.objects.filter(page='home', intro=INTRO):
        page.intro = OLD_INTRO
        if page.body == BODY:
            page.body = ''
        page.save(update_fields=['intro', 'body'])


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0013_event_city'),
    ]

    operations = [
        migrations.RunPython(write_about_copy, restore_placeholder),
    ]
