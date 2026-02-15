# blog/management/commands/migrate_event_data.py
# Create this file in your blog app directory structure:
# blog/
#   management/
#     __init__.py
#     commands/
#       __init__.py
#       migrate_event_data.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from blog.models import Event, EventImage
import os
from django.core.files import File
from pathlib import Path

class Command(BaseCommand):
    help = 'Migrates existing event data and creates sample events'

    def handle(self, *args, **options):
        self.stdout.write('Starting event data migration...')
        
        # Create sample past events if they don't exist
        past_events_data = [
            {
                'title': 'BB Festa #1',
                'slug': 'bb-festa-1',
                'event_type': 'bb_festa',
                'date': timezone.now().date() - timezone.timedelta(days=180),
                'description': 'Our first community festival celebrating digital art and creativity.',
                'short_description': 'First BB Festa event',
                'location': 'Tokyo Art Center',
                'order': 1,
            },
            {
                'title': 'BB Festa #2',
                'slug': 'bb-festa-2',
                'event_type': 'bb_festa',
                'date': timezone.now().date() - timezone.timedelta(days=120),
                'description': 'Second edition of our popular community festival.',
                'short_description': 'Second BB Festa event',
                'location': 'Tokyo Art Center',
                'order': 2,
            },
            {
                'title': 'BB Festa #3',
                'slug': 'bb-festa-3',
                'event_type': 'bb_festa',
                'date': timezone.now().date() - timezone.timedelta(days=60),
                'description': 'Third edition featuring international artists.',
                'short_description': 'Third BB Festa event',
                'location': 'Tokyo Art Center',
                'order': 3,
            },
            {
                'title': 'BB Festa #4',
                'slug': 'bb-festa-4',
                'event_type': 'bb_festa',
                'date': timezone.now().date() - timezone.timedelta(days=30),
                'description': 'Fourth edition with expanded workshops.',
                'short_description': 'Fourth BB Festa event',
                'location': 'Tokyo Art Center',
                'order': 4,
            },
            {
                'title': 'Thunder Gatherers #1',
                'slug': 'thunder-gatherers-1',
                'event_type': 'thunder',
                'date': timezone.now().date() - timezone.timedelta(days=15),
                'description': 'First Thunder Gatherers meetup.',
                'short_description': 'Thunder Gatherers premiere',
                'location': 'Online',
                'is_online': True,
                'order': 5,
            },
        ]
        
        for event_data in past_events_data:
            event, created = Event.objects.get_or_create(
                slug=event_data['slug'],
                defaults=event_data
            )
            if created:
                self.stdout.write(f'Created event: {event.title}')
                
                # Try to migrate existing images from static folder
                static_path = Path('blog/static/blog/Events')
                if static_path.exists():
                    # Map event to expected image files
                    image_mapping = {
                        'bb-festa-1': ['sample1.jpg', 'sample2.jpg'],
                        'bb-festa-2': ['sample3.jpg', 'sample4.jpg'],
                        'bb-festa-3': ['sample5.jpg'],
                        'bb-festa-4': ['sample1.jpg'],
                        'thunder-gatherers-1': ['sample2.jpg'],
                    }
                    
                    if event.slug in image_mapping:
                        for idx, image_file in enumerate(image_mapping[event.slug]):
                            image_path = static_path / image_file
                            if image_path.exists():
                                with open(image_path, 'rb') as f:
                                    image_instance = EventImage.objects.create(
                                        event=event,
                                        caption=f'Photo {idx + 1} from {event.title}',
                                        order=idx,
                                        is_featured=(idx == 0)
                                    )
                                    image_instance.image.save(image_file, File(f))
                                    self.stdout.write(f'  Added image: {image_file}')
            else:
                self.stdout.write(f'Event already exists: {event.title}')
        
        # Create sample upcoming events
        upcoming_events_data = [
            {
                'title': 'Digital Art Workshop',
                'slug': 'digital-art-workshop',
                'event_type': 'workshop',
                'date': timezone.now().date() + timezone.timedelta(days=30),
                'description': 'Learn digital art techniques from professional artists.',
                'short_description': 'Digital art workshop',
                'location': 'Tokyo Creative Space',
                'order': 10,
                'registration_required': True,
                'max_participants': 50,
            },
            {
                'title': 'Community Art Show',
                'slug': 'community-art-show',
                'event_type': 'exhibition',
                'date': timezone.now().date() + timezone.timedelta(days=60),
                'description': 'Showcase of community artworks.',
                'short_description': 'Community exhibition',
                'location': 'Tokyo Gallery',
                'order': 11,
            },
            {
                'title': 'Project Bunni Launch',
                'slug': 'project-bunni-launch',
                'event_type': 'community',
                'date': timezone.now().date() + timezone.timedelta(days=90),
                'description': 'Official launch of Project Bunni.',
                'short_description': 'Project launch event',
                'location': 'Online',
                'is_online': True,
                'order': 12,
            },
        ]
        
        for event_data in upcoming_events_data:
            event, created = Event.objects.get_or_create(
                slug=event_data['slug'],
                defaults=event_data
            )
            if created:
                self.stdout.write(f'Created upcoming event: {event.title}')
        
        self.stdout.write(self.style.SUCCESS('Data migration completed successfully!'))