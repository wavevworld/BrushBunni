# blog/migrations/XXXX_add_bbnote_and_event_note_url.py
# Rename this to the next migration number in your migrations folder

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),  # Change this to your latest migration
    ]

    operations = [
        # Add note_url to Event
        migrations.AddField(
            model_name='event',
            name='note_url',
            field=models.URLField(blank=True, max_length=500, help_text='Link to note.com article'),
        ),
        
        # Create BBNote model
        migrations.CreateModel(
            name='BBNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Article title', max_length=200)),
                ('url', models.URLField(help_text='Full URL from note.com', max_length=500)),
                ('description', models.CharField(blank=True, help_text='Short description (optional)', max_length=300)),
                ('thumbnail', models.ImageField(blank=True, help_text='Preview image (optional)', null=True, upload_to='bbnotes/')),
                ('published_date', models.DateField(blank=True, help_text='When the article was published on note.com', null=True)),
                ('is_pinned', models.BooleanField(default=False, help_text='Pin to top of list')),
                ('is_visible', models.BooleanField(default=True, help_text='Show on website')),
                ('order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'BB Note',
                'verbose_name_plural': 'BB Notes',
                'ordering': ['-is_pinned', 'order', '-published_date', '-created_at'],
            },
        ),
    ]
