from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


# =============================================================================
# EVENTS
# =============================================================================

class Event(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('past', 'Past'),
    ]
    
    EVENT_TYPES = [
        ('bb_festa', 'BB Festa'),
        ('thunder', 'Thunder Gatherers'),
        ('workshop', 'Workshop'),
        ('exhibition', 'Exhibition'),
        ('community', 'Community Event'),
    ]
    
    code = models.CharField(max_length=50, unique=True, help_text="e.g., BBFESTA-1, BBFESTA-2")
    slug = models.SlugField(max_length=80, unique=True, blank=True)
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
    location = models.CharField(max_length=200, blank=True)
    is_online = models.BooleanField(default=False)
    
    # Registration
    max_participants = models.PositiveIntegerField(blank=True, null=True)
    registration_required = models.BooleanField(default=False)
    registration_deadline = models.DateTimeField(blank=True, null=True)
    
    # Status and ordering
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='past')
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    
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
        if self.date:
            today = timezone.now().date()
            self.status = 'upcoming' if self.date >= today else 'past'
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('event_detail', kwargs={'slug': self.slug})
    
    @property
    def is_upcoming(self):
        return self.status == 'upcoming'
    
    @property
    def display_name(self):
        if self.event_type == 'bb_festa':
            if '-' in self.code:
                parts = self.code.split('-')
                return f"BB FESTA #{parts[-1]}"
        elif self.event_type == 'thunder':
            if '-' in self.code:
                parts = self.code.split('-')
                return f"THUNDER GATHERERS #{parts[-1]}"
        return self.title


class EventPhoto(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='events/', 
                              help_text="Upload event photos (JPG, PNG)")
    caption = models.CharField(max_length=200, blank=True)
    is_featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-is_featured', '-uploaded_at']
        verbose_name = "Event Photo"
        verbose_name_plural = "Event Photos"

    def __str__(self):
        return f"Photo for {self.event.code}"
    
    def is_video(self):
        if self.image:
            video_extensions = ['.mp4', '.mov', '.webm', '.avi']
            return any(self.image.url.lower().endswith(ext) for ext in video_extensions)
        return False


# Backward compatibility
class EventImage(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='event_images/')
    caption = models.CharField(max_length=200, blank=True)
    is_featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-is_featured', '-uploaded_at']

    def __str__(self):
        return f"Media for {self.event.title}"


# =============================================================================
# BB NOTES - Links to note.com articles
# =============================================================================

class BBNote(models.Model):
    title = models.CharField(max_length=200, help_text="Article title")
    url = models.URLField(max_length=500, help_text="Full URL from note.com")
    description = models.CharField(max_length=300, blank=True, 
                                   help_text="Short description (optional)")
    thumbnail = models.ImageField(upload_to='bbnotes/', blank=True, null=True,
                                  help_text="Preview image (optional)")
    published_date = models.DateField(blank=True, null=True,
                                      help_text="When the article was published on note.com")
    is_pinned = models.BooleanField(default=False, 
                                     help_text="Pin to top of list")
    is_visible = models.BooleanField(default=True,
                                      help_text="Show on website")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', 'order', '-published_date', '-created_at']
        verbose_name = "BB Note"
        verbose_name_plural = "BB Notes"

    def __str__(self):
        return self.title


# =============================================================================
# OTHER MODELS (kept for compatibility)
# =============================================================================

class Post(models.Model):
    POST_TYPES = [
        ('about', 'About Us'),
        ('community', 'Community'),
        ('event', 'Event'),
        ('news', 'News'),
        ('project', 'Project'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    content = models.TextField()
    excerpt = models.TextField(max_length=300, blank=True)
    post_type = models.CharField(max_length=20, choices=POST_TYPES, default='news')
    author = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    featured_image = models.ImageField(upload_to='posts/', blank=True, null=True)
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)


class SiteConfiguration(models.Model):
    site_name = models.CharField(max_length=100, default="Brush Bunni")
    site_description = models.TextField(blank=True)
    background_image = models.ImageField(upload_to='backgrounds/', blank=True, null=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    contact_email = models.EmailField(blank=True)
    discord_link = models.URLField(blank=True)
    instagram_link = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Configuration"
        verbose_name_plural = "Site Configuration"

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        if self.is_active:
            SiteConfiguration.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#6c5ce7")
    icon = models.ImageField(upload_to='category_icons/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Member(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('moderator', 'Moderator'),
        ('artist', 'Artist'),
        ('member', 'Member'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    portfolio_url = models.URLField(blank=True)
    instagram_handle = models.CharField(max_length=100, blank=True)
    discord_username = models.CharField(max_length=100, blank=True)
    is_featured = models.BooleanField(default=False)
    join_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.display_name or self.user.username


class Gallery(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    artist = models.ForeignKey(Member, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='gallery/')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.CharField(max_length=200, blank=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Gallery"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} by {self.artist}"


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    is_digital = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'slug': self.slug})

    @property
    def is_in_stock(self):
        return self.stock_quantity > 0 if not self.is_digital else True


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} - {self.name}"


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
