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

    if photo.thumbnail:
        return f"Photo {photo_id} already has a thumbnail"

    # Call the model's thumbnail helper to generate the InMemoryUploadedFile
    thumb_file = photo.make_thumbnail()
    if thumb_file:
        # Save the generated thumbnail file to the thumbnail field
        # photo.thumbnail.save will copy it to storage and save the model
        photo.thumbnail.save(thumb_file.name, thumb_file, save=True)
        return f"Thumbnail generated for photo {photo_id}"
    
    return f"Failed to generate thumbnail for photo {photo_id}"
