# views.py — Updated with BB Notes support

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.db import models

from .models import Post, Event, EventPhoto, EventImage, BBNote

# Safe imports for optional models
try:
    from .models import SiteConfiguration, Category, Member, Gallery, Product
except ImportError:
    SiteConfiguration = Category = Member = Gallery = Product = None


def get_site_config():
    if SiteConfiguration:
        try:
            return SiteConfiguration.objects.filter(is_active=True).first()
        except:
            pass
    return None


def base_context():
    return {
        'site_config': get_site_config(),
        'current_year': timezone.now().year,
    }


def home(request):
    context = base_context()
    context.update({
        'current_page': 'home',
        'bg_image': 'blog/bg_about.jpg',
    })
    return render(request, 'blog/home.html', context)


def community(request):
    context = base_context()
    context.update({
        'current_page': 'community',
        'bg_image': 'blog/bg_community.jpg',
    })
    return render(request, 'blog/community.html', context)


def be_online(request):
    """BB Online page — now shows BB Notes from note.com"""
    context = base_context()
    context.update({
        'current_page': 'be_online',
        'bg_image': 'blog/bg_online.jpg',
    })
    
    try:
        notes = BBNote.objects.filter(is_visible=True).order_by(
            '-is_pinned', 'order', '-published_date', '-created_at'
        )
        context['notes'] = notes
    except Exception:
        context['notes'] = []
    
    return render(request, 'blog/be_online.html', context)


def events(request):
    """Events page with past/upcoming split"""
    context = base_context()
    context.update({
        'current_page': 'events',
        'bg_image': 'blog/bg_events.jpg',
    })
    
    try:
        past_events = Event.objects.filter(
            is_active=True, status='past'
        ).prefetch_related('photos').order_by('order', '-date')
        
        upcoming_events = Event.objects.filter(
            is_active=True, status='upcoming'
        ).prefetch_related('photos').order_by('date', 'order')
        
        if not upcoming_events:
            today = timezone.now().date()
            upcoming_events = Event.objects.filter(
                is_active=True, date__gte=today
            ).prefetch_related('photos').order_by('date', 'order')
        
        context.update({
            'past_events': past_events,
            'upcoming_events': upcoming_events,
        })
    except Exception as e:
        context.update({
            'past_events': [],
            'upcoming_events': [],
        })
    
    return render(request, 'blog/events.html', context)


def shop(request):
    context = base_context()
    context.update({
        'current_page': 'shop',
        'bg_image': 'blog/bg_shop.jpg',
    })
    return render(request, 'blog/shop.html', context)


def project_bunni(request):
    context = base_context()
    context.update({
        'current_page': 'project_bunni',
        'bg_image': 'blog/bg_shop.jpg',
        'project_image': 'blog/images/PJBUNNI.jpg',
    })
    return render(request, 'blog/project_bunni.html', context)


def members(request):
    context = base_context()
    context.update({
        'current_page': 'members',
        'bg_image': 'blog/bg_members.jpg',
    })
    return render(request, 'blog/members.html', context)


def contact(request):
    context = base_context()
    context.update({
        'current_page': 'contact',
        'bg_image': 'blog/bg_contact.jpg',
    })
    return render(request, 'blog/contact.html', context)


def event_detail(request, slug):
    """Single event detail page"""
    context = base_context()
    context.update({
        'current_page': 'events',
        'bg_image': 'blog/bg_events.jpg',
    })
    
    try:
        event = get_object_or_404(Event, slug=slug, is_active=True)
        
        event_photos = []
        try:
            event_photos = event.photos.all().order_by('order', '-is_featured', '-uploaded_at')
        except:
            try:
                event_photos = event.images.all().order_by('order', '-is_featured', '-uploaded_at')
            except:
                pass
        
        related_events = Event.objects.filter(
            is_active=True, event_type=event.event_type
        ).exclude(id=event.id).order_by('order', '-date')[:3]
        
        if not related_events:
            related_events = Event.objects.filter(
                is_active=True
            ).exclude(id=event.id).order_by('-date')[:3]
        
        context.update({
            'event': event,
            'event_photos': event_photos,
            'related_events': related_events,
        })
        
        return render(request, 'blog/event_detail.html', context)
    
    except Event.DoesNotExist:
        return redirect('events')
    except Exception:
        return redirect('events')
