import os

from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError


class GalleryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gallery'

    def ready(self):
        username = os.getenv('ADMIN_USERNAME')
        password = os.getenv('ADMIN_PASSWORD')
        if username and password:
            try:
                from django.contrib.auth.models import User
                if not User.objects.filter(username=username).exists():
                    User.objects.create_superuser(username=username, password=password)
                    print(f"Admin user '{username}' created")
            except (OperationalError, ProgrammingError):
                pass

        self._seed_default_album()

    def _seed_default_album(self):
        try:
            from django.contrib.auth.models import User
            from .models import Album, Photo, PhotoAlbum

            admin = User.objects.filter(is_superuser=True).first()
            if not admin:
                return

            album, created = Album.objects.get_or_create(
                name="Family Photos",
                defaults={"description": "All family photos", "created_by": admin},
            )
            if created:
                print("Created default 'Family Photos' album")

            photos = Photo.objects.exclude(albums=album)
            if photos.exists():
                for photo in photos:
                    PhotoAlbum.objects.get_or_create(photo=photo, album=album)
                print(f"Added {photos.count()} photos to 'Family Photos' album")
        except (OperationalError, ProgrammingError):
            pass
