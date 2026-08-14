"""
BrushBunni Admin — Clean Redesign
===================================
Sidebar:  Events  |  BB Notes  |  Contact Messages
"""

from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.utils.html import format_html
from django.utils import timezone
from django.contrib import messages
from django.db.models import Max
from django import forms
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import path, reverse

from .models import (Event, EventPhoto, BBNote, ContactMessage, Gallery,
                     Member, PageContent)


# ─── Hide unnecessary sidebar items ─────────────────────────────────────────
admin.site.unregister(Group)
admin.site.unregister(User)

# ─── Branding ────────────────────────────────────────────────────────────────
admin.site.site_header = "BrushBunni"
admin.site.site_title = "BrushBunni"
admin.site.index_title = ""


# =============================================================================
# MULTI-FILE UPLOAD WIDGET
# =============================================================================

class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True
    def __init__(self, attrs=None):
        super().__init__({
            'accept': 'image/*,video/mp4,video/quicktime,video/webm',
            'multiple': True, 'class': 'photo-upload-input',
            **(attrs or {}),
        })

class MultiFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultiFileInput())
        super().__init__(*args, **kwargs)
    def clean(self, data, initial=None):
        if isinstance(data, (list, tuple)):
            return [super(MultiFileField, self).clean(d, initial) for d in data]
        return super().clean(data, initial)


# =============================================================================
# FILTERS
# =============================================================================

class StatusFilter(admin.SimpleListFilter):
    """Upcoming/Past filter computed from the date.

    `parameter_name` is deliberately plain 'status': the tab strip rendered by
    admin/js/brushbunni.js links to ?status=past / ?status=upcoming, and those
    links must keep working now that the stored status column is gone.
    """

    title = "status"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return [('upcoming', 'Upcoming'), ('past', 'Past')]

    def queryset(self, request, queryset):
        today = timezone.localdate()
        if self.value() == 'upcoming':
            return queryset.filter(date__gte=today)
        if self.value() == 'past':
            return queryset.filter(date__lt=today)
        return queryset


# =============================================================================
# EVENT FORM
# =============================================================================

class EventForm(forms.ModelForm):
    name = forms.CharField(
        max_length=50, label="Name",
        help_text="e.g. BBFESTA-5",
        widget=forms.TextInput(attrs={'placeholder': 'BBFESTA-1', 'style': 'font-weight:700; font-size:16px;'}),
    )
    upload_photos = MultiFileField(required=False, label="Upload Photos",
                                    help_text="Select multiple files")

    class Meta:
        model = Event
        fields = ['event_type', 'short_description', 'description',
                  'date', 'start_time', 'end_time', 'location', 'is_online',
                  'note_url', 'registration_url']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'location': forms.TextInput(attrs={'placeholder': 'Venue name'}),
            'short_description': forms.TextInput(attrs={'placeholder': 'Brief description'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Details...'}),
            'note_url': forms.URLInput(attrs={'placeholder': 'https://note.com/brushbunni/n/...'}),
            'registration_url': forms.URLInput(attrs={'placeholder': 'https://forms.gle/... (sign-up form)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['name'].initial = self.instance.code


# =============================================================================
# PHOTO INLINE
# =============================================================================

class PhotoInline(admin.TabularInline):
    model = EventPhoto
    extra = 0
    fields = ['photo_preview', 'caption']
    readonly_fields = ['photo_preview']
    ordering = ['order']
    can_delete = True
    verbose_name = "Photo"
    verbose_name_plural = "Photos"

    def photo_preview(self, obj):
        if not obj.image:
            return ""
        url = obj.image.url
        is_vid = any(url.lower().endswith(e) for e in ['.mp4', '.mov', '.webm'])
        if is_vid:
            return format_html(
                '<div class="photo-thumb video-thumb">'
                '<a href="{}" target="_blank">▶ Video</a></div>', url)
        return format_html(
            '<div class="photo-thumb">'
            '<a href="{}" target="_blank"><img src="{}"></a></div>', url, url)
    photo_preview.short_description = ""


# =============================================================================
# EVENT ADMIN
# =============================================================================

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    form = EventForm
    inlines = [PhotoInline]

    # ── List view ────────────────────────────────────────────────────────────
    # drag_handle must be listed for admin/js/brushbunni.js to wire up row
    # dragging — the reorder endpoint below already existed but was unreachable.
    list_display = ['drag_handle', 'event_thumb', 'event_name', 'type_badge',
                    'date_display', 'status_badge']
    list_display_links = ['event_thumb', 'event_name']
    list_filter = [StatusFilter, 'event_type', 'is_online', 'date']
    search_fields = ['code', 'title', 'short_description', 'location', 'description']
    date_hierarchy = 'date'
    ordering = ['order', '-date']
    list_per_page = 50
    actions = None

    # ── Edit form ────────────────────────────────────────────────────────────
    fieldsets = [
        (None, {
            'fields': [
                ('name', 'event_type'),
                ('date', 'start_time', 'end_time'),
                ('location', 'is_online'),
                'short_description',
                'description',
                'note_url',
                'registration_url',
                'upload_photos',
            ],
        }),
    ]
    exclude = ['code', 'title', 'slug', 'is_active', 'order',
               'registration_required', 'registration_deadline', 'max_participants']

    # ── Custom AJAX URLs ─────────────────────────────────────────────────────
    def get_urls(self):
        urls = super().get_urls()
        return [
            path('reorder/', self.admin_site.admin_view(self.reorder_events),
                 name='reorder_events'),
            path('reorder-photos/', self.admin_site.admin_view(self.reorder_photos),
                 name='reorder_photos'),
            path('delete-photo/<int:photo_id>/', self.admin_site.admin_view(self.delete_photo),
                 name='delete_photo'),
        ] + urls

    def reorder_events(self, request):
        if request.method == 'POST':
            import json
            try:
                data = json.loads(request.body)
                for i, eid in enumerate(data.get('order', [])):
                    Event.objects.filter(pk=eid).update(order=i * 10)
                return JsonResponse({'status': 'ok'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        return JsonResponse({'status': 'error'}, status=405)

    def reorder_photos(self, request):
        if request.method == 'POST':
            import json
            try:
                data = json.loads(request.body)
                for i, pid in enumerate(data.get('order', [])):
                    EventPhoto.objects.filter(pk=pid).update(order=i * 10)
                return JsonResponse({'status': 'ok'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        return JsonResponse({'status': 'error'}, status=405)

    def delete_photo(self, request, photo_id):
        if request.method == 'POST':
            try:
                photo = EventPhoto.objects.get(pk=photo_id)
                photo.image.delete(save=False)
                photo.delete()
                return JsonResponse({'status': 'ok'})
            except EventPhoto.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Not found'}, status=404)
        return JsonResponse({'status': 'error'}, status=405)

    # ── List display columns ─────────────────────────────────────────────────
    def drag_handle(self, obj):
        return format_html('<span class="drag-handle" data-id="{}">⋮⋮</span>', obj.pk)
    drag_handle.short_description = ""

    def event_thumb(self, obj):
        photo = obj.photos.first()
        if photo and photo.image:
            return format_html('<img src="{}" class="list-thumb">', photo.image.url)
        return format_html('<span class="list-thumb empty">📷</span>')
    event_thumb.short_description = ""
    def status_badge(self, obj):
        if obj.status == 'upcoming':
            return format_html('<span style="background:#dcfce7;color:#166534;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:700">Upcoming</span>')
        return format_html('<span style="background:#f3f4f6;color:#6b7280;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:700">Past</span>')
    status_badge.short_description = ""

    def event_name(self, obj):
        return format_html('<strong>{}</strong><br><span style="color:#999;font-size:12px">{}</span>',
                       obj.title or obj.code, obj.code)
    event_name.short_description = "Title"
    event_name.admin_order_field = 'title'

    def type_badge(self, obj):
        colors = {
            'bb_festa': ('#fce7f3', '#be185d'),
            'thunder': ('#e0e7ff', '#3730a3'),
            'workshop': ('#d1fae5', '#065f46'),
            'exhibition': ('#fef3c7', '#92400e'),
            'community': ('#dbeafe', '#1e40af'),
        }
        bg, fg = colors.get(obj.event_type, ('#f3f4f6', '#6b7280'))
        return format_html(
            '<span style="background:{};color:{};padding:3px 10px;border-radius:12px;'
            'font-size:12px;font-weight:600;white-space:nowrap">{}</span>',
            bg, fg, obj.get_event_type_display())
    type_badge.short_description = "Type"

    def date_display(self, obj):
        today = timezone.now().date()
        fmt = obj.date.strftime('%b %d, %Y')
        if obj.date < today:
            return format_html('<span style="color:#999">{}</span>', fmt)
        elif obj.date == today:
            return format_html('<span style="color:#f59e0b;font-weight:700">Today!</span>')
        return format_html('<span style="color:#10b981;font-weight:600">{}</span>', fmt)
    date_display.short_description = "Date"
    date_display.admin_order_field = 'date'




    # ── Save logic ───────────────────────────────────────────────────────────
    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        context['show_save_and_add_another'] = False
        context['show_save_and_continue'] = False
        return super().render_change_form(request, context, add, change, form_url, obj)

    def save_model(self, request, obj, form, change):
        name = form.cleaned_data.get('name', '').strip().upper()
        obj.code = name
        obj.title = name
        obj.is_active = True

        if not change:
            max_order = Event.objects.aggregate(m=Max('order'))['m'] or 0
            obj.order = max_order + 10

        super().save_model(request, obj, form, change)

        # Handle photo uploads
        photos = form.cleaned_data.get('upload_photos')
        if photos:
            photos_list = photos if isinstance(photos, list) else [photos]
            max_photo_order = obj.photos.aggregate(m=Max('order'))['m'] or 0
            count = 0
            for idx, f in enumerate(photos_list):
                if f:
                    EventPhoto.objects.create(
                        event=obj, image=f,
                        order=max_photo_order + (idx + 1) * 10)
                    count += 1
            if count:
                messages.success(request, f'✓ Uploaded {count} photo(s)')

    class Media:
        css = {'all': ['admin/css/brushbunni.css']}
        js = ['admin/js/brushbunni.js']


# =============================================================================
# BB NOTES ADMIN
# =============================================================================

@admin.register(BBNote)
class BBNoteAdmin(admin.ModelAdmin):
    list_display = ['drag_handle', 'note_thumb', 'title_display', 'note_date',
                    'is_pinned', 'is_visible', 'open_link']
    list_display_links = ['note_thumb', 'title_display']
    list_editable = ['is_pinned', 'is_visible']
    list_filter = ['is_pinned', 'is_visible']
    ordering = ['-is_pinned', 'order', '-published_date']
    list_per_page = 50
    search_fields = ['title', 'description']
    actions = None

    fieldsets = [
        (None, {
            'fields': [
                'title',
                'url',
                'description',
                'thumbnail',
                'published_date',
                ('is_pinned', 'is_visible'),
            ]
        }),
    ]
    exclude = ['order']

    # ── Custom URLs ──────────────────────────────────────────────────────────
    def get_urls(self):
        urls = super().get_urls()
        return [
            path('reorder/', self.admin_site.admin_view(self.reorder_notes),
                 name='reorder_notes'),
        ] + urls

    def reorder_notes(self, request):
        if request.method == 'POST':
            import json
            try:
                data = json.loads(request.body)
                for i, nid in enumerate(data.get('order', [])):
                    BBNote.objects.filter(pk=nid).update(order=i * 10)
                return JsonResponse({'status': 'ok'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        return JsonResponse({'status': 'error'}, status=405)

    # ── List columns ─────────────────────────────────────────────────────────
    def drag_handle(self, obj):
        return format_html('<span class="drag-handle" data-id="{}">⋮⋮</span>', obj.pk)
    drag_handle.short_description = ""

    def note_thumb(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" class="list-thumb">', obj.thumbnail.url)
        return format_html('<span class="list-thumb empty">📝</span>')
    note_thumb.short_description = ""

    def title_display(self, obj):
        return format_html('<strong>{}</strong>', obj.title)
    title_display.short_description = "Title"

    def note_date(self, obj):
        if obj.published_date:
            return obj.published_date.strftime('%b %d, %Y')
        return format_html('<span style="color:#ccc">—</span>')
    note_date.short_description = "Date"

    def pinned_icon(self, obj):
        return "📌" if obj.is_pinned else ""
    pinned_icon.short_description = "Pin"

    def visible_icon(self, obj):
        if obj.is_visible:
            return format_html('<span style="color:#10b981">●</span>')
        return format_html('<span style="color:#ccc">●</span>')
    visible_icon.short_description = "Vis"

    def open_link(self, obj):
        return format_html(
            '<a href="{}" target="_blank" style="text-decoration:none;'
            'background:#ff6b35;color:white;padding:4px 12px;border-radius:12px;'
            'font-size:12px;font-weight:600">Open ↗</a>', obj.url)
    open_link.short_description = ""

    # ── Save ─────────────────────────────────────────────────────────────────
    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        context['show_save_and_add_another'] = False
        context['show_save_and_continue'] = False
        return super().render_change_form(request, context, add, change, form_url, obj)

    def save_model(self, request, obj, form, change):
        if not change:
            max_order = BBNote.objects.aggregate(m=Max('order'))['m'] or 0
            obj.order = max_order + 10
        super().save_model(request, obj, form, change)

    class Media:
        css = {'all': ['admin/css/brushbunni.css']}
        js = ['admin/js/brushbunni.js']


# =============================================================================
# CONTACT MESSAGES ADMIN
# =============================================================================

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['subject', 'name', 'email', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    list_editable = ['is_read']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['name', 'email', 'subject', 'message', 'created_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    actions = ['mark_read', 'mark_unread']

    @admin.action(description="Mark selected as read")
    def mark_read(self, request, queryset):
        queryset.update(is_read=True)

    @admin.action(description="Mark selected as unread")
    def mark_unread(self, request, queryset):
        queryset.update(is_read=False)

    def has_add_permission(self, request):
        return False  # messages arrive from the website, never added by hand


# =============================================================================
# PAGE TEXTS
# =============================================================================

@admin.register(PageContent)
class PageContentAdmin(admin.ModelAdmin):
    list_display = ['page_display', 'heading', 'has_body', 'updated_at']
    list_display_links = ['page_display', 'heading']
    ordering = ['page']
    actions = None

    fieldsets = [
        (None, {
            'fields': ['page', 'heading', 'intro', 'body', 'image'],
        }),
        ("Button (optional)", {
            'fields': [('cta_label', 'cta_url')],
            'description': "Adds a button under the text, e.g. a Discord invite.",
        }),
        ("Search engines (optional)", {
            'fields': ['meta_description'],
            'classes': ['collapse'],
        }),
    ]

    def page_display(self, obj):
        return obj.get_page_display()
    page_display.short_description = "Page"
    page_display.admin_order_field = 'page'

    def has_body(self, obj):
        return bool(obj.body)
    has_body.short_description = "Text written"
    has_body.boolean = True

    def get_readonly_fields(self, request, obj=None):
        # Which page a row belongs to is fixed once created — changing it would
        # silently blank one page and overwrite another.
        return ['page'] if obj else []

    def has_add_permission(self, request):
        # One row per page; every page already exists after the data migration.
        return PageContent.objects.count() < len(PageContent.PAGE_CHOICES)

    def has_delete_permission(self, request, obj=None):
        return False  # the pages themselves are fixed; clear the fields instead

    class Media:
        css = {'all': ['admin/css/brushbunni.css']}
        js = ['admin/js/brushbunni.js']


# =============================================================================
# MEMBERS
# =============================================================================

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['drag_handle', 'avatar_thumb', 'name', 'role',
                    'is_featured', 'is_visible']
    list_display_links = ['avatar_thumb', 'name']
    list_editable = ['is_featured', 'is_visible']
    list_filter = ['role', 'is_visible', 'is_featured']
    search_fields = ['name', 'bio', 'instagram_handle', 'discord_username']
    ordering = ['-is_featured', 'order', 'name']
    actions = None

    fieldsets = [
        (None, {
            'fields': [('name', 'role'), 'bio', 'avatar'],
        }),
        ("Links (optional)", {
            'fields': ['portfolio_url', 'instagram_handle', 'discord_username'],
        }),
        ("Visibility", {
            'fields': [('is_featured', 'is_visible')],
        }),
    ]
    exclude = ['order']

    def get_urls(self):
        urls = super().get_urls()
        return [
            path('reorder/', self.admin_site.admin_view(self.reorder_members),
                 name='reorder_members'),
        ] + urls

    def reorder_members(self, request):
        if request.method == 'POST':
            import json
            try:
                data = json.loads(request.body)
                for i, mid in enumerate(data.get('order', [])):
                    Member.objects.filter(pk=mid).update(order=i * 10)
                return JsonResponse({'status': 'ok'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        return JsonResponse({'status': 'error'}, status=405)

    def drag_handle(self, obj):
        return format_html('<span class="drag-handle" data-id="{}">⋮⋮</span>', obj.pk)
    drag_handle.short_description = ""

    def avatar_thumb(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" class="list-thumb">', obj.avatar.url)
        return format_html('<span class="list-thumb empty">🐰</span>')
    avatar_thumb.short_description = ""

    def save_model(self, request, obj, form, change):
        if not change:
            max_order = Member.objects.aggregate(m=Max('order'))['m'] or 0
            obj.order = max_order + 10
        super().save_model(request, obj, form, change)

    class Media:
        css = {'all': ['admin/css/brushbunni.css']}
        js = ['admin/js/brushbunni.js']




# =============================================================================
# GALLERY
# =============================================================================

class BulkArtworkForm(forms.Form):
    """Add a batch of artwork in one go.

    A gallery is filled a dozen pieces at a time, and the stock admin makes
    that a dozen separate form submissions. The credit and event usually apply
    to the whole batch, so they are asked for once.
    """

    images = MultiFileField(
        label="Artwork files",
        help_text="Choose as many images as you like — one artwork is created "
                  "per file.")
    artist = forms.ModelChoiceField(
        queryset=Member.objects.all(), required=False,
        label="Artist (a member)",
        help_text="Leave empty if the artist is not on the Members page.")
    artist_name = forms.CharField(
        max_length=120, required=False, label="…or type a name",
        help_text="For a guest artist without a member profile.")
    event = forms.ModelChoiceField(
        queryset=Event.objects.filter(is_active=True), required=False,
        label="Shown at (optional)")
    is_visible = forms.BooleanField(
        initial=True, required=False, label="Publish straight away",
        help_text="Untick to upload them hidden and review before they go live.")

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("artist") and not cleaned.get("artist_name"):
            raise forms.ValidationError(
                "Give a credit: pick a member, or type the artist's name.")
        return cleaned


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    change_list_template = "admin/blog/gallery/change_list.html"
    list_display = ['art_thumb', 'title', 'credit_display', 'event',
                    'is_featured', 'is_visible', 'order']
    list_display_links = ['art_thumb', 'title']
    list_editable = ['is_featured', 'is_visible', 'order']
    list_filter = ['is_visible', 'is_featured', 'event', 'artist']
    search_fields = ['title', 'description', 'artist_name', 'artist__name', 'tags']
    autocomplete_fields = ['artist', 'event']
    ordering = ['-is_featured', 'order', '-created_at']

    fieldsets = [
        (None, {
            'fields': ['title', 'image', 'description'],
        }),
        ("Credit", {
            'fields': ['artist', 'artist_name'],
            'description': "Pick a member, or type a name for a guest artist "
                           "who is not on the Members page.",
        }),
        ("Where it was shown", {
            'fields': ['event', 'tags'],
        }),
        ("Visibility", {
            'fields': [('is_featured', 'is_visible'), 'order'],
        }),
    ]

    def art_thumb(self, obj):
        if obj.image:
            return format_html('<img src="{}" class="list-thumb">', obj.image.url)
        return format_html('<span class="list-thumb empty">🎨</span>')
    art_thumb.short_description = ""

    def credit_display(self, obj):
        return obj.credit
    credit_display.short_description = "Artist"

    def save_model(self, request, obj, form, change):
        # New pieces go to the end rather than colliding on order=0.
        if not change and not obj.order:
            obj.order = (Gallery.objects.aggregate(m=Max('order'))['m'] or 0) + 10
        super().save_model(request, obj, form, change)

    def get_urls(self):
        return [
            path('bulk-upload/', self.admin_site.admin_view(self.bulk_upload),
                 name='blog_gallery_bulk_upload'),
        ] + super().get_urls()

    def bulk_upload(self, request):
        form = BulkArtworkForm(request.POST or None, request.FILES or None)

        if request.method == 'POST' and form.is_valid():
            files = request.FILES.getlist('images')
            if not files:
                form.add_error('images', "Choose at least one image.")
            else:
                order = (Gallery.objects.aggregate(m=Max('order'))['m'] or 0)
                created = 0
                for upload in files:
                    order += 10
                    art = Gallery(
                        # A filename is a better starting title than "Untitled";
                        # she can rename in the list view afterwards.
                        title=upload.name.rsplit('.', 1)[0][:200],
                        artist=form.cleaned_data['artist'],
                        artist_name=form.cleaned_data['artist_name'],
                        event=form.cleaned_data['event'],
                        is_visible=form.cleaned_data['is_visible'],
                        order=order,
                    )
                    art.image = upload
                    art.save()
                    created += 1

                messages.success(
                    request,
                    f"Added {created} artwork{'s' if created != 1 else ''}. "
                    f"Rename or reorder them below.")
                return redirect(reverse('admin:blog_gallery_changelist'))

        return render(request, 'admin/blog/gallery/bulk_upload.html', {
            **self.admin_site.each_context(request),
            'form': form,
            'opts': self.model._meta,
            'title': "Upload artwork",
        })

    class Media:
        css = {'all': ['admin/css/brushbunni.css']}
        js = ['admin/js/brushbunni.js']
