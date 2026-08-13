"""Pull the community's note.com posts into BB Notes.

    ./.venv/Scripts/python.exe manage.py sync_note_articles --dry-run
    ./.venv/Scripts/python.exe manage.py sync_note_articles

Re-runnable: entries are matched on their note.com URL, so running it again
picks up new posts and refreshes titles/dates without creating duplicates.

Posts are published as bilingual pairs (one Japanese, one English, each with
its own URL). Only the English ones are imported by default, because the site
itself is English and importing both shows every topic twice. Pass
--include-japanese to take everything.

Uses urllib rather than requests so the project gains no new dependency.
"""

import json
import re
import urllib.request
from urllib.error import URLError, HTTPError

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from blog.models import BBNote

API = ("https://note.com/api/v2/creators/brushbunni/contents"
       "?kind=note&page={page}")

# Kana or CJK anywhere in the title means this is the Japanese edition.
JAPANESE = re.compile(r'[ぁ-んァ-ヶ一-龠]')

UA = {"User-Agent": "BrushBunni-site/1.0 (+https://brushbunni.com)"}


def fetch_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_bytes(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def strip_html(html):
    text = re.sub(r"<[^>]*>", "", html or "")
    return re.sub(r"\s+", " ", text).strip()


def console_safe(text, stream):
    """Article titles carry en-dashes and Japanese; the Windows console here
    is cp932 and raises on characters it cannot encode. Only the printed line
    is degraded — what gets stored in the database is always the original."""
    encoding = getattr(stream, "encoding", None) or "utf-8"
    return text.encode(encoding, errors="replace").decode(encoding, errors="replace")


class Command(BaseCommand):
    help = "Import note.com/brushbunni posts into BB Notes"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true",
                            help="Show what would change, write nothing")
        parser.add_argument("--include-japanese", action="store_true",
                            help="Import the Japanese editions too")
        parser.add_argument("--max-pages", type=int, default=10)

    def handle(self, *args, **options):
        dry = options["dry_run"]
        articles = self.collect(options["max_pages"])
        if not articles:
            self.stderr.write(self.style.ERROR("No articles returned by note.com"))
            return

        if not options["include_japanese"]:
            articles = [a for a in articles if not JAPANESE.search(a["name"])]

        self.stdout.write(f"{len(articles)} article(s) to sync"
                          f"{' (dry run)' if dry else ''}\n")

        created = updated = 0
        for art in articles:
            note = BBNote.objects.filter(url=art["url"]).first()
            action = "update" if note else "create"

            if dry:
                self.stdout.write(console_safe(
                    f"  [{action}] {art['published']}  {art['name']}", self.stdout))
                continue

            if note is None:
                note = BBNote(url=art["url"])
                created += 1
            else:
                updated += 1

            note.title = art["name"][:200]
            note.description = art["summary"][:300]
            note.published_date = art["published"] or None

            # Only fetch the header image when we don't already have one, so a
            # re-run is cheap and never re-uploads the same picture.
            if art["eyecatch"] and not note.thumbnail:
                try:
                    data = fetch_bytes(art["eyecatch"])
                    ext = ".png" if ".png" in art["eyecatch"].lower() else ".jpg"
                    # save=False: BBNote.save() below optimises and persists it.
                    note.thumbnail.save(f"note-{art['key']}{ext}",
                                        ContentFile(data), save=False)
                except (URLError, HTTPError, OSError) as exc:
                    self.stderr.write(f"  ! image failed for {art['key']}: {exc}")

            note.save()
            self.stdout.write(console_safe(
                f"  [{action}] {art['published']}  {note.title}", self.stdout))

        if not dry:
            # ASCII only: this console is cp932 and cannot encode an em-dash.
            self.stdout.write(self.style.SUCCESS(
                f"\nDone: {created} created, {updated} updated, "
                f"{BBNote.objects.count()} total"))

    def collect(self, max_pages):
        out = []
        for page in range(1, max_pages + 1):
            try:
                payload = fetch_json(API.format(page=page))
            except (URLError, HTTPError, ValueError) as exc:
                self.stderr.write(f"page {page}: {exc}")
                break

            data = payload.get("data") or {}
            for item in data.get("contents") or []:
                out.append({
                    "key": item.get("key", ""),
                    "name": item.get("name", ""),
                    "url": f"https://note.com/brushbunni/n/{item.get('key','')}",
                    "published": (item.get("publishAt") or "")[:10],
                    "eyecatch": item.get("eyecatch") or "",
                    "summary": strip_html(item.get("body", ""))[:300],
                })

            if data.get("isLastPage", True):
                break
        return out
