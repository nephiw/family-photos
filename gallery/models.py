import os
from datetime import datetime
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from PIL import Image, ImageOps


class Photo(models.Model):
    image = models.ImageField(upload_to="photos/")
    medium = models.ImageField(upload_to="medium/", blank=True, null=True)
    thumbnail = models.ImageField(upload_to="thumbnails/", blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="uploaded_photos"
    )
    caption = models.CharField(max_length=255, blank=True)
    date_taken = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new and self.image:
            self.extract_exif()
            self.image.seek(0)
        super().save(*args, **kwargs)
        if is_new and self.image and not self.thumbnail:
            from django.db import transaction

            from .tasks import process_photo_thumbnail

            transaction.on_commit(lambda: self._queue_thumbnail())

    def _queue_thumbnail(self):
        from .tasks import process_photo_thumbnail

        try:
            process_photo_thumbnail.delay(self.pk)
        except Exception as e:
            print(f"Could not queue thumbnail task for photo {self.pk}: {e}")

    def delete(self, *args, **kwargs):
        storage = self.image.storage
        if self.image and storage.exists(self.image.name):
            storage.delete(self.image.name)
        if self.medium and storage.exists(self.medium.name):
            storage.delete(self.medium.name)
        if self.thumbnail and storage.exists(self.thumbnail.name):
            storage.delete(self.thumbnail.name)
        super().delete(*args, **kwargs)

    def extract_exif(self):
        try:
            img = Image.open(self.image)
            exif = img._getexif()
            if exif is None:
                return

            date_str = exif.get(36867)
            if date_str:
                try:
                    self.date_taken = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                except (ValueError, TypeError):
                    pass

        except Exception as e:
            print(f"EXIF extraction error: {e}")

    def make_thumbnail(self):
        try:
            img = Image.open(self.image)
            img = ImageOps.exif_transpose(img)

            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            img.thumbnail((600, 600), Image.Resampling.LANCZOS)

            temp_handle = BytesIO()
            img.save(temp_handle, format="JPEG", quality=85)
            temp_handle.seek(0)

            filename = os.path.basename(self.image.name)
            name, ext = os.path.splitext(filename)
            thumb_name = f"{name}_thumb.jpg"

            return InMemoryUploadedFile(
                temp_handle,
                "ImageField",
                thumb_name,
                "image/jpeg",
                temp_handle.getbuffer().nbytes,
                None,
            )
        except Exception as e:
            print(f"Thumbnail generation error: {e}")
            return None

    def make_medium(self):
        try:
            img = Image.open(self.image)
            img = ImageOps.exif_transpose(img)

            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            img.thumbnail((1920, 1920), Image.Resampling.LANCZOS)

            temp_handle = BytesIO()
            img.save(temp_handle, format="JPEG", quality=85)
            temp_handle.seek(0)

            filename = os.path.basename(self.image.name)
            name, ext = os.path.splitext(filename)
            medium_name = f"{name}_medium.jpg"

            return InMemoryUploadedFile(
                temp_handle,
                "ImageField",
                medium_name,
                "image/jpeg",
                temp_handle.getbuffer().nbytes,
                None,
            )
        except Exception as e:
            print(f"Medium generation error: {e}")
            return None
