"""Fill empty events with the photos from their own note.com write-up.

    ./.venv/Scripts/python.exe manage.py import_event_photos --dry-run
    ./.venv/Scripts/python.exe manage.py import_event_photos

Each event already stores the article it came from in `note_url`, so there is
no guessing about which photos belong to which event — an event only ever gets
pictures from its own post.

Only events with no photos are touched, so this never competes with pictures
the client uploaded by hand. Pass --refill to include events that already have
some.

Re-runnable: the saved filename encodes the article and position, so a second
run recognises what it already imported.
"""

import json
import re
import urllib.request
from urllib.error import URLError, HTTPError

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from blog.models import Event, EventPhoto

NOTE_API = "https://note.com/api/v3/notes/{key}"
UA = {"User-Agent": "BrushBunni-site/1.0 (+https://brushbunni.com)"}


def fetch(url, as_json=True):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
    return json.loads(raw.decode("utf-8")) if as_json else raw


def console_safe(text, stream):
    enc = getattr(stream, "encoding", None) or "utf-8"
    return text.encode(enc, errors="replace").decode(enc, errors="replace")


class Command(BaseCommand):
    help = "Import event photos from each event's linked note.com article"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--refill", action="store_true",
                            help="Also import for events that already have photos")
        parser.add_argument("--max-per-event", type=int, default=8)

    def handle(self, *args, **options):
        dry = options["dry_run"]
        events = Event.objects.filter(is_active=True).exclude(note_url="")
        if not options["refill"]:
            events = [e for e in events if not e.photos.exists()]

        if not events:
            self.stdout.write("Nothing to do: every event with a note.com link "
                              "already has photos.")
            return

        self.stdout.write(f"{len(events)} event(s) to fill\n")
        total = 0

        for event in events:
            key = event.note_url.rstrip("/").split("/")[-1]
            try:
                body = (fetch(NOTE_API.format(key=key))
                        .get("data", {}).get("body", "")) or ""
            except (URLError, HTTPError, ValueError) as exc:
                self.stderr.write(f"  ! {event.code}: {exc}")
                continue

            urls = []
            for match in re.finditer(r'<img[^>]+src="([^"]+)"', body):
                clean = match.group(1).split("?")[0]
                if clean not in urls:
                    urls.append(clean)
            urls = urls[:options["max_per_event"]]

            if not urls:
                self.stdout.write(f"  {event.code}: article has no images")
                continue

            for index, url in enumerate(urls, start=1):
                stem = f"note-{key}-{index}"
                if event.photos.filter(image__contains=stem).exists():
                    continue

                if dry:
                    total += 1
                    self.stdout.write(console_safe(
                        f"  [add] {event.code:22} {url.split('/')[-1][:44]}",
                        self.stdout))
                    continue

                try:
                    data = fetch(url, as_json=False)
                except (URLError, HTTPError, OSError) as exc:
                    self.stderr.write(f"  ! image {url}: {exc}")
                    continue

                photo = EventPhoto(event=event, order=index * 10)
                ext = ".png" if url.lower().endswith(".png") else ".jpg"
                photo.image.save(f"{stem}{ext}", ContentFile(data), save=False)
                photo.save()
                total += 1
                self.stdout.write(console_safe(
                    f"  [add] {event.code:22} {stem}{ext}", self.stdout))

        verb = "would be added" if dry else "added"
        self.stdout.write(self.style.SUCCESS(f"\nDone: {total} photo(s) {verb}"))
