# Deploying brushbunni.com

The server runs nginx + Django, and the site is updated with `git pull` on the
server. Read the whole of step 0 before typing anything: the repository still
tracks `db.sqlite3` and `media/`, so a careless pull can overwrite live data.

---

## 0. Back up first (every time, no exceptions)

The production database holds events, BB Notes and contact messages that exist
**only** on the server. `media/` holds every photo uploaded through the admin.

```bash
cd /path/to/brushbunni                 # the deploy checkout
mkdir -p ~/backups
tar czf ~/backups/bb-$(date +%F-%H%M).tar.gz db.sqlite3 media/
ls -lh ~/backups | tail -3
```

Keep at least the last few archives.

---

## 1. Find out why the site is behind

As of the last check the live site was serving files from **21 Feb 2026** —
several commits behind `main`. The most likely cause is that `git pull` has
been failing because the tracked `db.sqlite3` and `media/` files are modified
on the server (the admin writes to them constantly), and git refuses to
overwrite local changes.

```bash
git status                 # expect: modified db.sqlite3, modified/untracked media files
git log --oneline -3       # what the server actually has
git log --oneline -3 origin/main
```

If `git status` shows `db.sqlite3` and `media/` as modified, that confirms it.

---

## 2. Stop tracking runtime data (do this once)

Runtime data must not live in git. Locally (already prepared in `.gitignore`):

```bash
# On the DEV machine, before committing:
git rm -r --cached staticfiles db.sqlite3 media
git commit -m "chore: stop tracking generated static, database and uploads"
git push
```

Nothing is deleted from your disk — only from git's index.

Then on the SERVER, with the backup from step 0 in hand:

```bash
git stash                  # park the server's local modifications
git pull
git stash drop             # the stash only held db/media noise
```

After the pull, git no longer tracks `db.sqlite3` or `media/`, so they simply
stay on disk untouched. Verify:

```bash
ls -lh db.sqlite3          # should still be the live database
ls media/events | wc -l    # should still list the uploaded photos
```

If anything is missing, restore from the backup:

```bash
tar xzf ~/backups/bb-<timestamp>.tar.gz
```

---

## 3. Normal deploy

```bash
cd /path/to/brushbunni
tar czf ~/backups/bb-$(date +%F-%H%M).tar.gz db.sqlite3 media/   # step 0
git pull

source .venv/bin/activate                 # whatever the venv is called here
pip install -r requirements.txt

python manage.py migrate                  # 0004 is NOT applied on prod yet
python manage.py collectstatic --noinput  # required: filenames are hashed now

sudo systemctl restart brushbunni         # or: gunicorn / uwsgi service name
```

`collectstatic` is mandatory on every deploy. Static files are now served
under content-hashed names (`style.1b3eff1293fc.css`); the templates look those
names up in `staticfiles/staticfiles.json`, which `collectstatic` writes.

---

## 4. Environment variables

Set these for the service (systemd unit, `.env`, or however it is wired):

```
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<a long random value — NOT the default in settings.py>
DJANGO_ALLOWED_HOSTS=brushbunni.com,www.brushbunni.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://brushbunni.com,https://www.brushbunni.com
DJANGO_HTTPS=True
```

Generate a key with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

`DJANGO_HTTPS=True` turns on the HTTPS-only cookies, the SSL redirect and HSTS.
Only enable it once TLS works and nginx sets `X-Forwarded-Proto`.

---

## 5. nginx: cache headers for static files

Currently nginx serves `/static/` with **no** `Cache-Control` at all, so
browsers re-validate every asset on every visit. Now that filenames carry a
content hash, a one-year immutable cache is safe.

In the `server { ... }` block:

```nginx
location /static/ {
    alias /path/to/brushbunni/staticfiles/;
    expires 1y;
    add_header Cache-Control "public, immutable";
    access_log off;

    # serve the pre-compressed .gz that collectstatic produced
    gzip_static on;
}

location /media/ {
    alias /path/to/brushbunni/media/;
    expires 30d;
    add_header Cache-Control "public";
    access_log off;
}
```

`/media/` is currently served by Django itself (see `brushbunni/urls.py`),
which ties up a worker per image. Once the nginx block above is live, that
Django route becomes dead weight and can be removed.

Apply and reload:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

---

## 6. Verify after deploying

```bash
curl -sI https://brushbunni.com/static/blog/style.*.css | grep -i cache-control
curl -s -o /dev/null -w "%{size_download}\n" https://brushbunni.com/static/blog/bg_about.webp
curl -s https://brushbunni.com/robots.txt
curl -s -o /dev/null -w "%{http_code}\n" https://brushbunni.com/sitemap.xml
```

Expected after a correct deploy:

- `bg_about.webp` returns ~282 KB (it was an 11 MB JPEG before)
- `Cache-Control: public, immutable`
- `robots.txt` lists the sitemap URL
- the mobile burger menu appears on a phone-width screen

Then submit `https://brushbunni.com/sitemap.xml` in Google Search Console, and
check the link preview with the Facebook Sharing Debugger or by pasting the URL
into Discord.
