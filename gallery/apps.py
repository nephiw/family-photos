import os

from django.apps import AppConfig


class GalleryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gallery'

    def ready(self):
        username = os.getenv('ADMIN_USERNAME')
        password = os.getenv('ADMIN_PASSWORD')
        if username and password:
            from django.contrib.auth.models import User
            if not User.objects.filter(username=username).exists():
                User.objects.create_superuser(username=username, password=password)
                print(f"Admin user '{username}' created")
