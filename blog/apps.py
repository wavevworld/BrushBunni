from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blog'
    # The admin grouped everything under "Blog", which means nothing to the
    # people who actually use it — this app holds the whole website's content.
    verbose_name = 'Website content'
