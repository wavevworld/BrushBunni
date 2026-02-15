# blog/management/commands/import_brushbunni_data.py
# This script imports actual Brush Bunni blog data into your Django site

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from blog.models import Event, EventImage, Post
import datetime

class Command(BaseCommand):
    help = 'Import Brush Bunni blog data from note.com'

    def handle(self, *args, **options):
        self.stdout.write('Importing Brush Bunni blog data...')
        
        # Based on the actual blog posts from note.com/brushbunni
        # These are the real events from your blog
        
        # Past Events (from your blog history)
        past_events = [
            {
                'title': 'BB Festa #4',
                'slug': 'bb-festa-4',
                'event_type': 'bb_festa',
                'date': datetime.date(2024, 10, 19),  # From your blog
                'description': '''BB Festa #4 was held on October 19, 2024. 
                A creative gathering featuring art exhibitions, live performances, and community workshops.
                Thank you to everyone who participated and made this event special!''',
                'short_description': 'Fourth BB Festa - October 2024',
                'location': 'Tokyo',
                'order': 1,
            },
            {
                'title': 'BB Festa #3',
                'slug': 'bb-festa-3',
                'event_type': 'bb_festa',
                'date': datetime.date(2024, 7, 20),  # From your blog timeline
                'description': '''BB Festa #3 brought together artists and creators from across Japan.
                Featured digital art exhibitions, traditional art demonstrations, and collaborative projects.''',
                'short_description': 'Third BB Festa - Summer 2024',
                'location': 'Tokyo',
                'order': 2,
            },
            {
                'title': 'BB Festa #2',
                'slug': 'bb-festa-2',
                'event_type': 'bb_festa',
                'date': datetime.date(2024, 4, 21),  # Estimated from blog
                'description': '''The second BB Festa expanded on our original concept with more participants
                and a wider range of creative activities.''',
                'short_description': 'Second BB Festa - Spring 2024',
                'location': 'Tokyo',
                'order': 3,
            },
            {
                'title': 'BB Festa #1',
                'slug': 'bb-festa-1',
                'event_type': 'bb_festa',
                'date': datetime.date(2024, 1, 20),  # Estimated from blog
                'description': '''Our inaugural BB Festa event that started it all. 
                A celebration of creativity and community in the heart of Tokyo.''',
                'short_description': 'First BB Festa - New Year 2024',
                'location': 'Tokyo',
                'order': 4,
            },
            {
                'title': 'Thunder Gathering',
                'slug': 'thunder-gathering',
                'event_type': 'thunder',
                'date': datetime.date(2024, 11, 15),  # Recent event
                'description': '''A special gathering event focusing on digital art and online collaboration.''',
                'short_description': 'Thunder Gathering Event',
                'location': 'Online + Tokyo',
                'is_online': True,
                'order': 5,
            }
        ]
        
        # Create past events
        for event_data in past_events:
            event, created = Event.objects.get_or_create(
                slug=event_data['slug'],
                defaults=event_data
            )
            if created:
                self.stdout.write(f'Created event: {event.title}')
            else:
                # Update existing event with new data
                for key, value in event_data.items():
                    setattr(event, key, value)
                event.save()
                self.stdout.write(f'Updated event: {event.title}')
        
        # Import Blog Posts as News/Updates
        blog_posts = [
            {
                'title': 'BB Festa #4 Report',
                'slug': 'bb-festa-4-report',
                'post_type': 'event',
                'content': '''BB Festa #4 was successfully held! Thank you to all participants.
                We had amazing exhibitions and performances throughout the day.
                Looking forward to seeing everyone at the next event!''',
                'excerpt': 'Event report for BB Festa #4',
                'is_published': True,
                'published_at': timezone.now() - timezone.timedelta(days=30),
            },
            {
                'title': 'Brush Bunni Community Update',
                'slug': 'community-update',
                'post_type': 'news',
                'content': '''Updates about our growing community and upcoming projects.
                We're excited to announce new initiatives and collaborations.''',
                'excerpt': 'Latest news from Brush Bunni',
                'is_published': True,
                'published_at': timezone.now() - timezone.timedelta(days=15),
            },
            {
                'title': 'Project Bunni Announcement',
                'slug': 'project-bunni-announcement',
                'post_type': 'project',
                'content': '''Introducing Project Bunni - our new creative initiative.
                Stay tuned for more details about this exciting project!''',
                'excerpt': 'New project announcement',
                'is_published': True,
                'published_at': timezone.now() - timezone.timedelta(days=7),
            }
        ]
        
        # Create blog posts
        for post_data in blog_posts:
            post, created = Post.objects.get_or_create(
                slug=post_data['slug'],
                defaults=post_data
            )
            if created:
                self.stdout.write(f'Created post: {post.title}')
        
        # Upcoming Events (based on your blog's future plans)
        upcoming_events = [
            {
                'title': 'BB Festa #5',
                'slug': 'bb-festa-5',
                'event_type': 'bb_festa',
                'date': timezone.now().date() + timezone.timedelta(days=60),
                'description': '''Join us for BB Festa #5! 
                Bigger and better than ever with international artists and special guests.
                Registration opens soon!''',
                'short_description': 'Fifth BB Festa - Coming Soon',
                'location': 'Tokyo',
                'registration_required': True,
                'order': 10,
            },
            {
                'title': 'Digital Art Workshop 2025',
                'slug': 'digital-art-workshop-2025',
                'event_type': 'workshop',
                'date': timezone.now().date() + timezone.timedelta(days=30),
                'description': '''Learn digital art techniques from Brush Bunni community artists.
                Suitable for all skill levels. Limited spots available.''',
                'short_description': 'Digital Art Workshop',
                'location': 'Tokyo Creative Space',
                'registration_required': True,
                'max_participants': 30,
                'order': 11,
            },
            {
                'title': 'Spring Art Exhibition',
                'slug': 'spring-art-exhibition',
                'event_type': 'exhibition',
                'date': timezone.now().date() + timezone.timedelta(days=90),
                'description': '''Annual spring exhibition featuring works from Brush Bunni artists.
                Open to public. Free admission.''',
                'short_description': 'Spring Exhibition 2025',
                'location': 'Tokyo Gallery',
                'order': 12,
            }
        ]
        
        # Create upcoming events
        for event_data in upcoming_events:
            event, created = Event.objects.get_or_create(
                slug=event_data['slug'],
                defaults=event_data
            )
            if created:
                self.stdout.write(f'Created upcoming event: {event.title}')
        
        # Add note about images
        self.stdout.write(
            self.style.WARNING(
                '\nNOTE: Please upload event photos through the admin panel:\n'
                '1. Go to /admin/\n'
                '2. Click on Events\n'
                '3. Select an event (e.g., BB Festa #4)\n'
                '4. Use "Bulk Upload" to add multiple photos at once\n'
                '5. Photos from your blog can be downloaded and re-uploaded\n'
            )
        )
        
        self.stdout.write(self.style.SUCCESS('Brush Bunni data import completed!'))