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
from django.urls import path

from .models import Event, EventPhoto, BBNote


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
                  'date', 'start_time', 'end_time', 'location', 'is_online', 'note_url']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'location': forms.TextInput(attrs={'placeholder': 'Venue name'}),
            'short_description': forms.TextInput(attrs={'placeholder': 'Brief description'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Details...'}),
            'note_url': forms.URLInput(attrs={'placeholder': 'https://note.com/brushbunni/n/...'}),
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
    list_display = ['event_thumb', 'event_name', 'type_badge', 'date_display','status_badge']
    list_display_links = ['event_thumb', 'event_name']
    list_filter = ['status', 'event_type', 'is_online', 'date']
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
                'upload_photos',
            ],
        }),
    ]
    exclude = ['code', 'title', 'slug', 'status', 'is_active', 'order',
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
    search_fields = []
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


