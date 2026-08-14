"""Fill the Gallery from the images already published on note.com.

    ./.venv/Scripts/python.exe manage.py import_note_images --dry-run
    ./.venv/Scripts/python.exe manage.py import_note_images --limit 24

Every image here is the community's own, taken from the community's own posts,
and each row keeps a link back to the article it came from so the credit can
always be checked.

Artist Spotlight posts are titled "BRUSHBUNNI ARTIST SPOTLIGHT : <name>", so
the artist can be read straight off the title and the work credited properly.
Anything else is imported without a credit rather than guessing one — an
unattributed photo is a gap someone can fill, a wrong attribution is worse
than nothing.

Re-runnable: rows are matched on the source image URL, so running it again
adds only what is new.
"""

import json
import re
import urllib.request
from urllib.error import URLError, HTTPError

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from blog.models import Gallery

LIST_API = ("https://note.com/api/v2/creators/brushbunni/contents"
            "?kind=note&page={page}")
NOTE_API = "https://note.com/api/v3/notes/{key}"

JAPANESE = re.compile(r'[ぁ-んァ-ヶ一-龠]')
SPOTLIGHT = re.compile(r'ARTIST\s+SPOTLIGHT\s*[:：]\s*(.+)$', re.I)
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
    help = "Import images from note.com posts into the Gallery"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--limit", type=int, default=0,
                            help="Stop after N new artworks (0 = no limit)")
        parser.add_argument("--max-pages", type=int, default=10)
        parser.add_argument(
            "--credited-only", action="store_true",
            help="Only Artist Spotlight posts, whose artist can be read from "
                 "the title. Everything else is event photography with no "
                 "reliable credit, which does not belong in an art gallery.")

    def handle(self, *args, **options):
        dry, limit = options["dry_run"], options["limit"]

        posts = self.collect_posts(options["max_pages"])
        posts = [p for p in posts if not JAPANESE.search(p["name"])]
        if options["credited_only"]:
            posts = [p for p in posts if SPOTLIGHT.search(p["name"])]
        self.stdout.write(f"{len(posts)} English post(s) to read\n")

        created = skipped = 0
        for post in posts:
            if limit and created >= limit:
                break
            try:
                body = (fetch(NOTE_API.format(key=post["key"]))
                        .get("data", {}).get("body", "")) or ""
            except (URLError, HTTPError, ValueError) as exc:
                self.stderr.write(f"  ! {post['key']}: {exc}")
                continue

            urls = []
            for match in re.finditer(r'<img[^>]+src="([^"]+)"', body):
                clean = match.group(1).split("?")[0]
                if clean not in urls:
                    urls.append(clean)
            if not urls:
                continue

            spotlight = SPOTLIGHT.search(post["name"])
            credit = spotlight.group(1).strip() if spotlight else ""

            for index, url in enumerate(urls, start=1):
                if limit and created >= limit:
                    break
                if Gallery.objects.filter(description__contains=url).exists():
                    skipped += 1
                    continue

                # The article's name is not the artwork's name, and repeating
                # it on every card just echoes the credit underneath. These
                # pieces are untitled as published, so say so and number them.
                title = f"Untitled #{index}" if credit else post["name"].strip()

                if dry:
                    created += 1
                    self.stdout.write(console_safe(
                        f"  [create] {credit or '(no credit)':28} {title[:54]}",
                        self.stdout))
                    continue

                try:
                    data = fetch(url, as_json=False)
                except (URLError, HTTPError, OSError) as exc:
                    self.stderr.write(f"  ! image {url}: {exc}")
                    continue

                art = Gallery(
                    title=title[:200],
                    artist_name=credit[:120],
                    # Keeps provenance attached to the row itself, which is what
                    # makes a wrong credit fixable later.
                    description=f"From note.com: https://note.com/brushbunni/n/"
                                f"{post['key']}\nSource image: {url}",
                    is_visible=True,
                )
                ext = ".png" if url.lower().endswith(".png") else ".jpg"
                art.image.save(f"note-{post['key']}-{index}{ext}",
                               ContentFile(data), save=False)
                art.save()
                created += 1
                self.stdout.write(console_safe(
                    f"  [create] {credit or '(no credit)':28} {title[:54]}",
                    self.stdout))

        if dry:
            self.stdout.write(f"\nDry run: {created} would be created, "
                              f"{skipped} already present")
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\nDone: {created} created, {skipped} already present, "
                f"{Gallery.objects.count()} artworks total"))

    def collect_posts(self, max_pages):
        out = []
        for page in range(1, max_pages + 1):
            try:
                data = fetch(LIST_API.format(page=page)).get("data") or {}
            except (URLError, HTTPError, ValueError) as exc:
                self.stderr.write(f"page {page}: {exc}")
                break
            for item in data.get("contents") or []:
                out.append({"key": item.get("key", ""),
                            "name": item.get("name", "")})
            if data.get("isLastPage", True):
                break
        return out
