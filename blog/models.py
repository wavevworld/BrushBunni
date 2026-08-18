import re
from io import BytesIO

from django.db import models
from django.core.files.base import ContentFile
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from PIL import Image, ImageOps


def optimize_image_field(image_field, max_width=1600, quality=82):
    """Downscale + re-encode a freshly uploaded image in place.

    Keeps the same file name so DB paths stay valid. Silently skips
    non-image files (e.g. uploaded videos) and anything Pillow can't open.
    Call with save=False semantics: it only rewrites the FieldFile content.
    """
    name = (image_field.name or "").lower()
    if not name.endswith((".jpg", ".jpeg", ".png")):
        return  # videos / webp / unknown — leave untouched
    try:
        image_field.open()
        img = Image.open(image_field)
        img = ImageOps.exif_transpose(img)  # honour camera orientation
    except Exception:
        return

    if img.width > max_width:
        height = round(img.height * max_width / img.width)
        img = img.resize((max_width, height))

    buffer = BytesIO()
    if name.endswith(".png"):
        img.save(buffer, format="PNG", optimize=True)
    else:
        img.convert("RGB").save(
            buffer, format="JPEG", quality=quality, optimize=True, progressive=True
        )
    image_field.save(image_field.name, ContentFile(buffer.getvalue()), save=False)


# =============================================================================
# EVENTS
# =============================================================================

class Event(models.Model):
    EVENT_TYPES = [
        ('bb_festa', 'BB Festa'),
        ('thunder', 'Thunder Gatherers'),
        ('workshop', 'Workshop'),
        ('exhibition', 'Exhibition'),
        ('community', 'Community Event'),
    ]
    
    code = models.CharField(max_length=50, unique=True, help_text="e.g., BBFESTA-1, BBFESTA-2")
    slug = models.SlugField(
        max_length=80, unique=True, blank=True, verbose_name="Web address",
        help_text="Filled in automatically from the name. This is the part "
                  "that appears in the page's link.")
    title = models.CharField(max_length=200)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='bb_festa')
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=200, blank=True)
    note_url = models.URLField(max_length=500, blank=True, 
                               help_text="Link to note.com article")
    
    # Event timing
    date = models.DateField()
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    
    # Location
    location = models.CharField(
        max_length=200, blank=True, verbose_name="Venue",
        help_text="The place itself, e.g. \"Demachi Gadget, Demachiyanagi\".")
    city = models.CharField(
        max_length=100, blank=True,
        help_text="Kyoto, Tokyo, and so on. Kept separate from the venue so "
                  "search engines can read where the event was held.")
    is_online = models.BooleanField(
        default=False, verbose_name="Online event",
        help_text="Tick for events with no physical venue.")
    
    # Registration
    max_participants = models.PositiveIntegerField(blank=True, null=True)
    registration_required = models.BooleanField(default=False)
    registration_deadline = models.DateTimeField(blank=True, null=True)
    registration_url = models.URLField(
        max_length=500, blank=True,
        help_text="Sign-up link (e.g. Google Form) shown as a Register button")
    
    # Ordering
    is_active = models.BooleanField(
        default=True, verbose_name="Show on the website",
        help_text="Untick to hide this event without deleting it.")
    order = models.PositiveIntegerField(
        default=0, verbose_name="Position",
        help_text="Lower numbers come first. Leave at 0 to sort by date.")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-date']
        verbose_name = "Event"
        verbose_name_plural = "Events"

    def __str__(self):
        return self.code
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.code)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('event_detail', kwargs={'slug': self.slug})

    @property
    def is_upcoming(self):
        """Derived from the date, never stored.

        This used to be a `status` column recomputed in save(), which meant an
        event stayed "Upcoming" for months after it happened until somebody
        re-saved it in the admin.
        """
        return self.date >= timezone.localdate()

    @property
    def status(self):
        return 'upcoming' if self.is_upcoming else 'past'
    
    # Which code prefix belongs to which public series name. The prefix is
    # checked as well as the type because the data is not always consistent —
    # THUNG1 is stored as event_type 'bb_festa', and naming it from the type
    # alone would publish it as "BB FESTA #1", both wrong and a duplicate of
    # the real BBFESTA-1.
    SERIES = [
        ('BBFESTA', 'BB FESTA'),
        ('THUNG', 'THUNDER GATHERERS'),
        ('THUNDER', 'THUNDER GATHERERS'),
    ]

    @property
    def display_name(self):
        """The name a visitor should see.

        Codes like WACHAJ2 are internal identifiers, but they were reaching the
        page whenever `title` had never been filled in — the upcoming-events
        card was publishing a database key. A real title now wins, and a code
        with no title behind it is at least made readable.
        """
        code = (self.code or '').strip()
        title = (self.title or '').strip()

        squashed = code.replace('-', '').replace('_', '').upper()
        for prefix, name in self.SERIES:
            if squashed.startswith(prefix):
                number = squashed[len(prefix):]
                return f"{name} #{number}" if number.isdigit() else name

        if title and title.upper() != code.upper():
            return title

        # No usable title: turn SOME-CODE2 into "Some Code 2" rather than
        # shouting an identifier at the reader.
        words = re.sub(r'[-_]+', ' ', code)
        words = re.sub(r'(?<=[A-Za-z])(?=\d)', ' ', words)
        return words.title() or code


class EventPhoto(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='events/', 
                              help_text="Upload event photos (JPG, PNG)")
    caption = models.CharField(max_length=200, blank=True)
    is_featured = models.BooleanField(
        default=False, verbose_name="Use as the main photo",
        help_text="The large image at the top of the event's page.")
    order = models.PositiveIntegerField(
        default=0, verbose_name="Position",
        help_text="Lower numbers come first.")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-is_featured', '-uploaded_at']
        verbose_name = "Event Photo"
        verbose_name_plural = "Event Photos"

    def save(self, *args, **kwargs):
        # Compress only freshly uploaded images (never re-compress on plain re-saves).
        if self.image and self._image_is_new():
            optimize_image_field(self.image, max_width=1600, quality=82)
        super().save(*args, **kwargs)

    def _image_is_new(self):
        if not self.pk:
            return True
        try:
            return EventPhoto.objects.get(pk=self.pk).image.name != self.image.name
        except EventPhoto.DoesNotExist:
            return True

    def __str__(self):
        return f"Photo for {self.event.code}"

    def is_video(self):
        if self.image:
            video_extensions = ['.mp4', '.mov', '.webm', '.avi']
            return any(self.image.url.lower().endswith(ext) for ext in video_extensions)
        return False


# =============================================================================
# BB NOTES - Links to note.com articles
# =============================================================================

class BBNote(models.Model):
    title = models.CharField(max_length=200, help_text="Article title")
    url = models.URLField(max_length=500, verbose_name="Link",
                          help_text="Full URL from note.com")
    description = models.CharField(max_length=300, blank=True,
                                   verbose_name="Summary",
                                   help_text="Short description (optional)")
    thumbnail = models.ImageField(upload_to='bbnotes/', blank=True, null=True,
                                  verbose_name="Cover image",
                                  help_text="Preview image (optional)")
    published_date = models.DateField(blank=True, null=True,
                                      verbose_name="Published",
                                      help_text="When the article was published on note.com")
    # Plain-language labels, matching Gallery and Event. These read as
    # "Is pinned" / "Is visible" in the list header otherwise — Django's
    # default, and the only two columns in the admin still phrased that way.
    is_pinned = models.BooleanField(default=False,
                                    verbose_name="Pin to the top",
                                    help_text="Pinned notes appear first.")
    is_visible = models.BooleanField(default=True,
                                     verbose_name="Show on the website",
                                     help_text="Untick to hide without deleting.")
    order = models.PositiveIntegerField(default=0, verbose_name="Position",
                                        help_text="Lower numbers come first.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', 'order', '-published_date', '-created_at']
        verbose_name = "BB Note"
        verbose_name_plural = "BB Notes"

    def save(self, *args, **kwargs):
        # Thumbnails render tiny (56px), so 400px is plenty.
        if self.thumbnail and self._thumbnail_is_new():
            optimize_image_field(self.thumbnail, max_width=400, quality=85)
        super().save(*args, **kwargs)

    def _thumbnail_is_new(self):
        if not self.pk:
            return True
        try:
            return BBNote.objects.get(pk=self.pk).thumbnail.name != self.thumbnail.name
        except BBNote.DoesNotExist:
            return True

    def __str__(self):
        return self.title


# =============================================================================
# EDITABLE PAGE CONTENT
# =============================================================================

class PageContent(models.Model):
    """Text for the simple pages, so the owner can edit them without a deploy.

    One row per page. Views fall back to sensible defaults when a row is
    missing, so a page never renders blank.
    """

    PAGE_CHOICES = [
        ('home', 'About Us (home page)'),
        ('community', 'Community'),
        ('members', 'Members'),
        ('project_bunni', 'Project Bunni'),
    ]

    page = models.CharField(max_length=30, choices=PAGE_CHOICES, unique=True)
    heading = models.CharField(max_length=200, blank=True,
                               help_text="Big title at the top of the page")
    intro = models.CharField(max_length=300, blank=True,
                             help_text="One line under the title (optional)")
    body = models.TextField(blank=True,
                            help_text="Main text. Blank lines start a new paragraph.")
    image = models.ImageField(upload_to='pages/', blank=True, null=True,
                              help_text="Optional image shown with the text")
    cta_label = models.CharField(max_length=60, blank=True,
                                 help_text="Button text, e.g. 'Join our Discord'")
    cta_url = models.URLField(blank=True, help_text="Where the button links to")
    meta_description = models.CharField(
        max_length=300, blank=True,
        help_text="Search-engine and social-preview description (optional)")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['page']
        verbose_name = "Page text"
        verbose_name_plural = "Page texts"

    def save(self, *args, **kwargs):
        if self.image and self._image_is_new():
            optimize_image_field(self.image, max_width=1200, quality=85)
        super().save(*args, **kwargs)

    def _image_is_new(self):
        if not self.pk:
            return True
        try:
            return PageContent.objects.get(pk=self.pk).image.name != self.image.name
        except PageContent.DoesNotExist:
            return True

    def __str__(self):
        return self.get_page_display()


# =============================================================================
# MEMBERS & ARTWORK
# =============================================================================

class Member(models.Model):
    """A person shown on the Members page.

    Deliberately NOT tied to django.contrib.auth.User: community members are
    listed on the site but never log in, and requiring a user account for each
    one made the admin unusable for the site owner.
    """

    ROLE_CHOICES = [
        ('founder', 'Founder'),
        ('organizer', 'Organizer'),
        ('artist', 'Artist'),
        ('member', 'Member'),
    ]

    name = models.CharField(max_length=100, help_text="Name shown on the site")
    slug = models.SlugField(max_length=120, unique=True, blank=True,
                            help_text="Auto-filled from the name; used in the "
                                      "profile page URL")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member',
                            verbose_name="Role")
    bio = models.TextField(blank=True, verbose_name="Short bio",
                           help_text="A short line or two about them")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True,
                               verbose_name="Photo")
    portfolio_url = models.URLField(blank=True, verbose_name="Portfolio link",
                                    help_text="Portfolio or website")
    instagram_handle = models.CharField(
        max_length=100, blank=True, verbose_name="Instagram",
        help_text="Without the @")
    discord_username = models.CharField(max_length=100, blank=True,
                                        verbose_name="Discord username")
    is_featured = models.BooleanField(
        default=False, verbose_name="Pin to the top",
        help_text="Featured members appear before everyone else.")
    is_visible = models.BooleanField(
        default=True, verbose_name="Show on the website",
        help_text="Untick to hide this person without deleting them.")
    order = models.PositiveIntegerField(
        default=0, verbose_name="Position",
        help_text="Lower numbers come first, among members who are not pinned.")
    join_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_featured', 'order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._unique_slug()
        # Avatars render at ~160px, so anything above 600px is wasted bytes.
        if self.avatar and self._avatar_is_new():
            optimize_image_field(self.avatar, max_width=600, quality=85)
        super().save(*args, **kwargs)

    def _unique_slug(self):
        """Two members can share a name, but the URL cannot.

        Falls back to "member" when slugify() returns nothing at all, which is
        what happens for a name written entirely in Japanese.
        """
        base = slugify(self.name) or "member"
        slug, n = base, 2
        taken = Member.objects.exclude(pk=self.pk)
        while taken.filter(slug=slug).exists():
            slug = f"{base}-{n}"
            n += 1
        return slug

    def _avatar_is_new(self):
        if not self.pk:
            return True
        try:
            return Member.objects.get(pk=self.pk).avatar.name != self.avatar.name
        except Member.DoesNotExist:
            return True

    def get_absolute_url(self):
        return reverse('member_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.name


class Gallery(models.Model):
    """One piece of artwork shown in the community gallery.

    Submissions arrive through the per-event Google Form and are published
    here from the admin, so there is deliberately no public upload path.
    """

    title = models.CharField(max_length=200, verbose_name="Title of the piece")
    description = models.TextField(blank=True, verbose_name="Description")
    image = models.ImageField(upload_to='gallery/', verbose_name="Artwork")

    # Credit. `artist` links the piece to a Member profile; `artist_name`
    # covers guest artists who exhibit at a BB Festa without being members.
    # SET_NULL, not CASCADE: removing someone from the Members page must not
    # delete the artwork they contributed.
    artist = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True,
                               blank=True, related_name='artworks',
                               verbose_name="Artist (member profile)")
    artist_name = models.CharField(
        max_length=120, blank=True, verbose_name="Artist name (guest)",
        help_text="Credit for an artist who is not on the Members page. "
                  "Ignored when an artist is chosen above.")

    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True,
                              blank=True, related_name='artworks',
                              verbose_name="Shown at event",
                              help_text="Optional: the event this was shown at")
    tags = models.CharField(
        max_length=200, blank=True,
        help_text="Optional keywords, separated by commas. Not shown on "
                  "the website — they are for your own searching.")

    is_featured = models.BooleanField(
        default=False, verbose_name="Use as the folder cover",
        help_text="This piece becomes the picture on the artist's folder "
                  "in the Gallery.")
    is_visible = models.BooleanField(
        default=True, verbose_name="Show on the website",
        help_text="Untick to hide this piece without deleting it.")
    order = models.PositiveIntegerField(
        default=0, verbose_name="Position",
        help_text="Lower numbers come first within this artist's folder.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Artwork"
        verbose_name_plural = "Gallery"
        ordering = ['-is_featured', 'order', '-created_at']

    def save(self, *args, **kwargs):
        if self.image and self._image_is_new():
            optimize_image_field(self.image, max_width=1600, quality=85)
        super().save(*args, **kwargs)

    def _image_is_new(self):
        if not self.pk:
            return True
        try:
            return Gallery.objects.get(pk=self.pk).image.name != self.image.name
        except Gallery.DoesNotExist:
            return True

    @property
    def credit(self):
        """Who to show under the piece, whether or not they have a profile."""
        if self.artist:
            return self.artist.name
        return self.artist_name or "Unknown artist"

    def __str__(self):
        return f"{self.title} by {self.credit}"


# =============================================================================
# CONTACT
# =============================================================================

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False, verbose_name="Read",
                                  help_text="Tick once you have dealt with it.")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Received")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} - {self.name}"
