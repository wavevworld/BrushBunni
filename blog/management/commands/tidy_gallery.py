"""Clean up artwork imported from note.com.

    ./.venv/Scripts/python.exe manage.py tidy_gallery --dry-run
    ./.venv/Scripts/python.exe manage.py tidy_gallery

Two things the import could not get right on its own:

  * Credits come from the article titles, which shout — "KAY TANG" and "MICHI"
    sit beside "Gabe Ramos" and "Christopher T. Falkenberg". Only names that
    are entirely uppercase are touched; anything already mixed-case is left
    exactly as the artist wrote it.
  * Every piece landed with order=0, so the ordering field does nothing and the
    grid falls back to upload time. Pieces are numbered in tens per artist,
    leaving room to slot something in between without renumbering.

Re-runnable: a second run reports nothing to do.
"""

import re

from django.core.management.base import BaseCommand

from blog.models import Gallery

# Words that should stay capitalised as-is when un-shouting a name.
KEEP_UPPER = {'BB', 'DJ', 'II', 'III', 'JP', 'UK', 'US'}


def detitle(name):
    """KAY TANG -> Kay Tang, leaving already-cased names untouched."""
    stripped = name.strip()
    if not stripped or stripped != stripped.upper():
        return stripped  # already has lowercase somewhere: the artist's choice

    words = []
    for word in stripped.split():
        if word in KEEP_UPPER:
            words.append(word)
        elif re.fullmatch(r'[A-Z]\.', word):     # initials like "T."
            words.append(word)
        else:
            words.append(word.capitalize())
    return ' '.join(words)


def console_safe(text, stream):
    enc = getattr(stream, 'encoding', None) or 'utf-8'
    return text.encode(enc, errors='replace').decode(enc, errors='replace')


class Command(BaseCommand):
    help = "Normalise gallery credits and give artwork a real display order"

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        dry = options['dry_run']
        renamed = renumbered = 0

        # --- credits ---
        for art in Gallery.objects.exclude(artist_name=''):
            tidy = detitle(art.artist_name)
            if tidy != art.artist_name:
                self.stdout.write(console_safe(
                    f'  credit  {art.artist_name!r} -> {tidy!r}', self.stdout))
                if not dry:
                    art.artist_name = tidy
                    art.save(update_fields=['artist_name'])
                renamed += 1

        # --- ordering, numbered per artist so each folder reads sensibly ---
        by_artist = {}
        for art in Gallery.objects.order_by('artist_name', 'pk'):
            by_artist.setdefault(art.credit, []).append(art)

        for credit, pieces in by_artist.items():
            for position, art in enumerate(pieces, start=1):
                wanted = position * 10
                if art.order != wanted:
                    if not dry:
                        art.order = wanted
                        art.save(update_fields=['order'])
                    renumbered += 1

        verb = 'would be' if dry else ''
        self.stdout.write(self.style.SUCCESS(
            f'\nDone: {renamed} credit(s) {verb} tidied, '
            f'{renumbered} artwork(s) {verb} renumbered'))
