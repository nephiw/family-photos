from django.core.management.base import BaseCommand

from gallery.models import Photo


class Command(BaseCommand):
    help = "Generate thumbnails for photos that are missing them"

    def handle(self, *args, **options):
        photos = Photo.objects.filter(thumbnail__isnull=True)
        count = photos.count()
        if count == 0:
            self.stdout.write("No photos missing thumbnails.")
            return

        self.stdout.write(f"Found {count} photos without thumbnails...")
        for photo in photos:
            try:
                thumbnail = photo.make_thumbnail()
                if thumbnail:
                    photo.thumbnail = thumbnail
                    photo.save(update_fields=["thumbnail"])
                    self.stdout.write(f"  OK photo {photo.pk}")
                else:
                    self.stdout.write(f"  SKIP photo {photo.pk} — thumbnail generation returned None")
            except Exception as e:
                self.stdout.write(f"  ERROR photo {photo.pk}: {e}")

        self.stdout.write("Done.")
