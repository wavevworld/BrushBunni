# Generated migration for adding note_url field to Event model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),  # Replace with your latest migration
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='note_url',
            field=models.URLField(
                blank=True,
                help_text='Link to BB Note article (e.g., https://note.com/brushbunni/...)',
                max_length=500
            ),
        ),
    ]
