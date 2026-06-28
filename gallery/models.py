import os
from datetime import datetime, timedelta
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.utils import timezone
from PIL import Image, ImageOps


class Photo(models.Model):
    image = models.ImageField(upload_to="photos/")
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
        # Generate thumbnail on new upload
        if self.image and not self.thumbnail:
            self.extract_exif()
            self.thumbnail = self.make_thumbnail()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        storage = self.image.storage
        if self.image and storage.exists(self.image.name):
            storage.delete(self.image.name)
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
                    self.date_taken = datetime.strptime(
                        date_str, "%Y:%m:%d %H:%M:%S"
                    )
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
