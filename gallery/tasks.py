import os
from celery import shared_task
from .models import Photo

@shared_task
def process_photo_thumbnail(photo_id):
    try:
        photo = Photo.objects.get(pk=photo_id)
    except Photo.DoesNotExist:
        return f"Photo {photo_id} not found"

    if not photo.image:
        return f"Photo {photo_id} has no image"

    results = []

    if not photo.thumbnail:
        thumb_file = photo.make_thumbnail()
        if thumb_file:
            photo.thumbnail.save(thumb_file.name, thumb_file, save=False)
            results.append("thumbnail")
        else:
            results.append("thumbnail_failed")

    if not photo.medium:
        medium_file = photo.make_medium()
        if medium_file:
            photo.medium.save(medium_file.name, medium_file, save=False)
            results.append("medium")
        else:
            results.append("medium_failed")

    if results:
        photo.save(update_fields=["thumbnail", "medium"])

    return f"Generated {', '.join(results)} for photo {photo_id}"
