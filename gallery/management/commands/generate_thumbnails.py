from django.db import models
from django.core.management.base import BaseCommand

from gallery.models import Photo
from gallery.tasks import process_photo_thumbnail


class Command(BaseCommand):
    help = "Queue thumbnail + medium generation for photos missing them"

    def handle(self, *args, **options):
        photos = Photo.objects.filter(
            models.Q(thumbnail__isnull=True) | models.Q(medium__isnull=True)
        )
        count = photos.count()
        if count == 0:
            self.stdout.write("All photos have thumbnails and medium images.")
            return

        self.stdout.write(f"Found {count} photos to process (via Celery)...")
        queued = 0
        for photo in photos:
            try:
                process_photo_thumbnail.delay(photo.pk)
                queued += 1
            except Exception as e:
                self.stdout.write(f"  ERROR queuing photo {photo.pk}: {e}")

        self.stdout.write(f"Queued {queued} photos for processing. The Celery worker will generate them.")
