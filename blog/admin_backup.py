from django.contrib import admin
from django.utils.html import format_html
from django import forms
from django.db import models
from .models import Event, EventPhoto  # Only import Event and EventPhoto

# Customize the admin site
admin.site.site_header = "Brush Bunni Events Admin"
admin.site.site_title = "Events Admin"
admin.site.index_title = "Manage Events & Photos"


# Multiple file upload widget
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


# Inline for Event Photos
class EventPhotoInline(admin.TabularInline):
    model = EventPhoto
    extra = 1
    fields = ('image_preview', 'image', 'caption', 'is_featured', 'order')
    readonly_fields = ('image_preview',)
    ordering = ('order',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="100" height="75" style="object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Preview'


# Event Admin Form with bulk upload
class EventAdminForm(forms.ModelForm):
    bulk_photos = MultipleFileField(
        required=False, 
        label="Bulk Upload Photos",
        help_text="Select multiple photos to upload at once"
    )
    
    class Meta:
        model = Event
        fields = '__all__'


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    form = EventAdminForm
    list_display = ('code', 'title', 'event_type', 'status', 'date', 'photo_count', 'order', 'is_active')
    list_filter = ('status', 'event_type', 'is_active', 'date')
    search_fields = ('code', 'title', 'description', 'location')
    prepopulated_fields = {'slug': ('code',)}
    date_hierarchy = 'date'
    inlines = [EventPhotoInline]
    list_editable = ('order', 'is_active', 'status')
    ordering = ('order', '-date')
    
    fieldsets = (
        ('Event Identification', {
            'fields': ('code', 'slug', 'title', 'event_type'),
            'description': 'Use codes like BBFESTA-1, BBFESTA-2, THUNDER-1, etc.'
        }),
        ('Event Details', {
            'fields': ('short_description', 'description')
        }),
        ('Date & Time', {
            'fields': ('date', 'start_time', 'end_time')
        }),
        ('Location', {
            'fields': ('location', 'is_online')
        }),
        ('Registration', {
            'fields': ('registration_required', 'registration_deadline', 'max_participants'),
            'classes': ('collapse',)
        }),
        ('Bulk Photo Upload', {
            'fields': ('bulk_photos',),
            'description': 'Upload multiple photos at once. Save the event first, then photos will be added.',
            'classes': ('collapse',)
        }),
        ('Status & Display', {
            'fields': ('status', 'is_active', 'order'),
            'description': 'Status is auto-set based on date but can be manually overridden.'
        }),
    )
    
    def photo_count(self, obj):
        count = obj.photos.count()
        if count > 0:
            return format_html('<span style="color: green;"><b>{}</b> photos</span>', count)
        return format_html('<span style="color: orange;">No photos</span>')
    photo_count.short_description = 'Photos'
    
    def save_model(self, request, obj, form, change):
        # Save the event first
        super().save_model(request, obj, form, change)
        
        # Auto-set order if not provided
        if obj.order == 0:
            max_order = Event.objects.aggregate(models.Max('order'))['order__max'] or 0
            obj.order = max_order + 10
            obj.save()
        
        # Handle bulk photo uploads
        bulk_photos = form.cleaned_data.get('bulk_photos')
        if bulk_photos:
            if not isinstance(bulk_photos, (list, tuple)):
                bulk_photos = [bulk_photos]
            
            # Get the current max order for this event's photos
            max_order = obj.photos.aggregate(models.Max('order'))['order__max'] or 0
            
            for idx, image in enumerate(bulk_photos):
                if image:
                    EventPhoto.objects.create(
                        event=obj,
                        image=image,
                        caption=f"Photo {idx + 1} from {obj.code}",
                        order=max_order + (idx + 1) * 10
                    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing event
            return ['status']  # Make status read-only as it's auto-calculated
        return []
    
    actions = ['duplicate_event', 'set_upcoming', 'set_past']
    
    def duplicate_event(self, request, queryset):
        for event in queryset:
            # Create a copy of the event
            new_event = Event.objects.create(
                code=f"{event.code}-COPY",
                title=f"{event.title} (Copy)",
                event_type=event.event_type,
                description=event.description,
                short_description=event.short_description,
                date=event.date,
                start_time=event.start_time,
                end_time=event.end_time,
                location=event.location,
                is_online=event.is_online,
                max_participants=event.max_participants,
                registration_required=event.registration_required,
                registration_deadline=event.registration_deadline,
                is_active=False,  # Set as inactive by default
                order=event.order + 1
            )
            # Copy photos
            for photo in event.photos.all():
                EventPhoto.objects.create(
                    event=new_event,
                    image=photo.image,
                    caption=photo.caption,
                    is_featured=photo.is_featured,
                    order=photo.order
                )
        self.message_user(request, f"Duplicated {queryset.count()} event(s)")
    duplicate_event.short_description = "Duplicate selected events"
    
    def set_upcoming(self, request, queryset):
        queryset.update(status='upcoming')
        self.message_user(request, f"Set {queryset.count()} event(s) as upcoming")
    set_upcoming.short_description = "Mark as Upcoming"
    
    def set_past(self, request, queryset):
        queryset.update(status='past')
        self.message_user(request, f"Set {queryset.count()} event(s) as past")
    set_past.short_description = "Mark as Past"


@admin.register(EventPhoto)
class EventPhotoAdmin(admin.ModelAdmin):
    list_display = ('event_code', 'image_preview', 'caption', 'is_featured', 'order', 'uploaded_at')
    list_filter = ('is_featured', 'uploaded_at', 'event__event_type', 'event__code')
    search_fields = ('caption', 'event__code', 'event__title')
    list_editable = ('order', 'is_featured', 'caption')
    ordering = ('event', 'order', '-uploaded_at')
    list_per_page = 50
    
    def event_code(self, obj):
        return obj.event.code
    event_code.short_description = 'Event Code'
    event_code.admin_order_field = 'event__code'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="150" height="100" style="object-fit: cover; border-radius: 4px; cursor: pointer;" onclick="window.open(\'{}\', \'_blank\')" title="Click to open full size"/>',
                obj.image.url, obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Preview'
    
    actions = ['set_featured', 'unset_featured', 'reorder_photos']
    
    def set_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f"Set {queryset.count()} photo(s) as featured")
    set_featured.short_description = "Set as Featured"
    
    def unset_featured(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(request, f"Removed featured status from {queryset.count()} photo(s)")
    unset_featured.short_description = "Remove Featured Status"
    
    def reorder_photos(self, request, queryset):
        # Reorder photos by their upload date
        for idx, photo in enumerate(queryset.order_by('uploaded_at')):
            photo.order = (idx + 1) * 10
            photo.save()
        self.message_user(request, f"Reordered {queryset.count()} photo(s) by upload date")
    reorder_photos.short_description = "Reorder by Upload Date"

# NO EventImage admin here - completely removed!