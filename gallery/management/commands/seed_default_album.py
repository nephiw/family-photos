from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from gallery.models import Album, Photo, PhotoAlbum


class Command(BaseCommand):
    help = "Create the default 'Family Photos' album and associate all existing photos"

    def handle(self, *args, **options):
        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            self.stdout.write(self.style.ERROR("No admin user found. Create one first."))
            return

        album, created = Album.objects.get_or_create(
            name="Family Photos",
            defaults={
                "description": "All family photos",
                "created_by": admin,
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created album '{album.name}'"))
        else:
            self.stdout.write(f"Album '{album.name}' already exists")

        photos = Photo.objects.exclude(albums=album)
        count = photos.count()
        if count > 0:
            for photo in photos:
                PhotoAlbum.objects.get_or_create(photo=photo, album=album)
            self.stdout.write(self.style.SUCCESS(f"Added {count} photos to '{album.name}'"))
        else:
            self.stdout.write("All photos already in album")
