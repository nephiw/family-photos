import json
import os
from datetime import timedelta

import zipstream
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.utils import timezone
from django.views.decorators.http import require_GET

from .forms import AdminUserUpdateForm, AlbumForm, ProfileForm, RetroUserCreationForm
from .models import Album, Photo, PhotoAlbum


def home(request):
    if request.user.is_authenticated:
        return redirect("gallery:album_list")
    return redirect("gallery:auth_login")


SORT_FIELDS = {
    "uploaded": "-uploaded_at",
    "taken": "-date_taken",
}
SORT_FIELDS_ASC = {
    "uploaded": "uploaded_at",
    "taken": "date_taken",
}


@login_required
def album_list(request):
    if request.user.is_superuser:
        albums = Album.objects.all()
    else:
        albums = Album.objects.filter(Q(created_by=request.user) | Q(name="Family Photos"))
    return render(request, "gallery/album_list.html", {"albums": albums})


@login_required
def album_detail(request, pk):
    album = get_object_or_404(Album, pk=pk)
    if album.name != "Family Photos" and album.created_by != request.user and not request.user.is_superuser:
        return redirect("gallery:album_list")
    photo_ids = album.photoalbum_set.values_list("photo_id", flat=True)
    photos = Photo.objects.filter(pk__in=photo_ids)

    if not photos.exists():
        return render(request, "gallery/album_empty.html", {"album": album})

    sort_field = request.GET.get("sort", "uploaded")
    sort_dir = request.GET.get("dir", "desc")

    if sort_dir == "asc":
        sort_by = SORT_FIELDS_ASC.get(sort_field, "-uploaded_at")
    else:
        sort_by = SORT_FIELDS.get(sort_field, "-uploaded_at")

    photos = photos.order_by(sort_by)

    if request.htmx and request.headers.get("HX-Target") == "photo-grid":
        return render(
            request,
            "gallery/partials/photo_grid.html",
            {"photos": photos, "sort": sort_field, "dir": sort_dir, "album": album},
        )

    albums = Album.objects.filter(Q(created_by=request.user) | Q(name="Family Photos")).order_by("name")
    context = {
        "photos": photos,
        "album": album,
        "albums": albums,
        "sort": sort_field,
        "dir": sort_dir,
    }
    return render(request, "gallery/album_detail.html", context)


@login_required
def album_create(request):
    if request.method == "POST":
        form = AlbumForm(request.POST)
        if form.is_valid():
            album = form.save(commit=False)
            album.created_by = request.user
            album.save()
            messages.success(request, f"Album '{album.name}' created!")
            return redirect("gallery:album_detail", pk=album.pk)
    else:
        form = AlbumForm()

    return render(request, "gallery/album_create.html", {"form": form})


@login_required
def album_delete(request, pk):
    album = get_object_or_404(Album, pk=pk)
    if request.method != "POST":
        return redirect("gallery:album_detail", pk=pk)
    if not request.user.is_superuser and album.created_by != request.user:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("You can only delete your own albums.")
    PhotoAlbum.objects.filter(album=album).delete()
    name = album.name
    album.delete()
    messages.success(request, f"Album '{name}' deleted.")
    return redirect("gallery:album_list")


@login_required
def album_choose_photos(request, pk):
    album = get_object_or_404(Album, pk=pk)
    if album.name != "Family Photos" and album.created_by != request.user and not request.user.is_superuser:
        return redirect("gallery:album_list")
    family_album = Album.objects.filter(name="Family Photos").first()
    if not family_album:
        return redirect("gallery:album_list")

    photo_ids = family_album.photoalbum_set.values_list("photo_id", flat=True)
    photos = Photo.objects.filter(pk__in=photo_ids).order_by("-uploaded_at")

    already_in = set(
        PhotoAlbum.objects.filter(album=album).values_list("photo_id", flat=True)
    )

    if request.method == "POST":
        selected = request.POST.getlist("photos")
        for photo_id in selected:
            PhotoAlbum.objects.get_or_create(
                photo_id=photo_id, album=album
            )
        messages.success(request, f"Added {len(selected)} photo(s) to '{album.name}'.")
        return redirect("gallery:album_detail", pk=album.pk)

    return render(
        request,
        "gallery/album_choose_photos.html",
        {"album": album, "photos": photos, "already_in": already_in},
    )


SORT_FIELDS = {
    "uploaded": "-uploaded_at",
    "taken": "-date_taken",
}
SORT_FIELDS_ASC = {
    "uploaded": "uploaded_at",
    "taken": "date_taken",
}


@login_required
def photo_list(request):
    family_photos = Album.objects.filter(name="Family Photos").first()
    if family_photos:
        return redirect("gallery:album_detail", pk=family_photos.pk)
    return redirect("gallery:album_list")


@login_required
def photo_upload(request):
    album_id = request.GET.get("album") or request.POST.get("album")
    album = None
    if album_id:
        album = get_object_or_404(Album, pk=album_id)

    if request.method == "POST":
        files = request.FILES.getlist("photos") or request.FILES.getlist("file")
        album_id = request.POST.get("album")
        album = None
        if album_id:
            album = get_object_or_404(Album, pk=album_id)

        if not files:
            return HttpResponse("No photos selected", status=400)

        uploaded_photos = []
        family_photos = Album.objects.filter(name="Family Photos").first()
        for file in files:
            try:
                photo = Photo.objects.create(image=file, uploaded_by=request.user)
                uploaded_photos.append(photo)
                if family_photos:
                    PhotoAlbum.objects.get_or_create(photo=photo, album=family_photos)
                if album and album != family_photos:
                    PhotoAlbum.objects.get_or_create(photo=photo, album=album)
            except Exception as e:
                print(f"Error saving photo: {e}")
                return HttpResponse(f"Error saving photo: {str(e)}", status=500)

        if request.htmx:
            if album:
                photo_ids = album.photoalbum_set.values_list("photo_id", flat=True)
                photos = Photo.objects.filter(pk__in=photo_ids)
            else:
                photos = Photo.objects.all()
            return render(
                request, "gallery/partials/photo_grid.html", {"photos": photos, "album": album}
            )

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True, "count": len(uploaded_photos)})

        messages.success(
            request, f"Successfully uploaded {len(uploaded_photos)} photos!"
        )
        if album:
            return redirect("gallery:album_detail", pk=album.pk)
        if family_photos:
            return redirect("gallery:album_detail", pk=family_photos.pk)
        return redirect("gallery:album_list")

    albums = Album.objects.all()
    return render(
        request,
        "gallery/upload.html",
        {"selected_album": album, "albums": albums},
    )


@login_required
def photo_detail(request, pk):
    photo = get_object_or_404(Photo, pk=pk)

    user_albums = Album.objects.filter(
        models.Q(created_by=request.user) | models.Q(name="Family Photos")
    ).distinct()
    photo_albums = photo.albums.filter(pk__in=user_albums.values_list("pk", flat=True))

    back_album = None
    album_param = request.GET.get("album")
    if album_param and album_param.isdigit():
        back_album = user_albums.filter(pk=int(album_param)).first()
    if not back_album:
        back_album = Album.objects.filter(name="Family Photos").first()

    if request.htmx:
        return render(
            request,
            "gallery/partials/photo_detail.html",
            {
                "photo": photo,
                "is_admin": request.user.is_superuser,
                "photo_albums": photo_albums,
            },
        )
    photos = Photo.objects.all()
    return render(
        request,
        "gallery/photo_detail_page.html",
        {
            "photo": photo,
            "photos": photos,
            "is_admin": request.user.is_superuser,
            "photo_albums": photo_albums,
            "back_album": back_album,
        },
    )


@login_required
def photo_add_to_album(request, pk):
    photo = get_object_or_404(Photo, pk=pk)
    user_albums = Album.objects.filter(
        models.Q(created_by=request.user) | models.Q(name="Family Photos")
    ).distinct()

    if request.method == "POST":
        if request.POST.get("create_and_add"):
            new_name = request.POST.get("new_album_name", "").strip()
            if not new_name:
                messages.warning(request, "Please provide an album name.")
                return redirect("gallery:photo_add_to_album", pk=pk)
            album = Album.objects.create(name=new_name, created_by=request.user)
            PhotoAlbum.objects.get_or_create(photo=photo, album=album)
            messages.success(request, f"Created album '{album.name}' and added photo.")
            return redirect("gallery:photo_detail", pk=pk)
        album_id = request.POST.get("album")
        album = get_object_or_404(Album, pk=album_id)
        PhotoAlbum.objects.get_or_create(photo=photo, album=album)
        messages.success(request, f"Photo added to '{album.name}'.")
        return redirect("gallery:photo_detail", pk=pk)

    already_in = set(
        PhotoAlbum.objects.filter(
            photo=photo, album__in=user_albums
        ).values_list("album_id", flat=True)
    )

    return render(
        request,
        "gallery/photo_add_to_album.html",
        {"photo": photo, "albums": user_albums, "already_in": already_in},
    )


@login_required
def bulk_delete(request, album_pk):
    album = get_object_or_404(Album, pk=album_pk)
    if request.method != "POST":
        return redirect("gallery:album_detail", pk=album_pk)

    photo_ids = request.POST.getlist("photos")
    if not photo_ids:
        messages.warning(request, "No photos selected.")
        return redirect("gallery:album_detail", pk=album_pk)

    count = 0
    for photo_id in photo_ids:
        try:
            photo = Photo.objects.get(pk=photo_id)
        except Photo.DoesNotExist:
            continue
        PhotoAlbum.objects.filter(photo=photo, album=album).delete()
        count += 1
        if not photo.albums.exists():
            photo.delete()

    messages.success(request, f"Removed {count} photo(s) from '{album.name}'.")
    return redirect("gallery:album_detail", pk=album_pk)


@login_required
def bulk_add_to_album(request, album_pk):
    source_album = get_object_or_404(Album, pk=album_pk)
    if request.method != "POST":
        return redirect("gallery:album_detail", pk=album_pk)

    raw = request.POST.get("photos", "")
    photo_ids = [pid.strip() for pid in raw.split(",") if pid.strip()]
    target_album_id = request.POST.get("target_album")

    if not photo_ids:
        messages.warning(request, "No photos selected.")
        return redirect("gallery:album_detail", pk=album_pk)

    if not target_album_id:
        messages.warning(request, "No target album selected.")
        return redirect("gallery:album_detail", pk=album_pk)

    target_album = get_object_or_404(Album, pk=target_album_id)
    added = 0
    for photo_id in photo_ids:
        _, created = PhotoAlbum.objects.get_or_create(
            photo_id=photo_id, album=target_album
        )
        if created:
            added += 1

    messages.success(request, f"Added {added} photo(s) to '{target_album.name}'.")
    return redirect("gallery:album_detail", pk=album_pk)


@login_required
def bulk_create_album(request, album_pk):
    source_album = get_object_or_404(Album, pk=album_pk)
    if request.method != "POST":
        return redirect("gallery:album_detail", pk=album_pk)

    raw = request.POST.get("photos", "")
    photo_ids = [pid.strip() for pid in raw.split(",") if pid.strip()]
    new_album_name = request.POST.get("new_album_name", "").strip()

    if not photo_ids:
        messages.warning(request, "No photos selected.")
        return redirect("gallery:album_detail", pk=album_pk)

    if not new_album_name:
        messages.warning(request, "Please provide an album name.")
        return redirect("gallery:album_detail", pk=album_pk)

    new_album = Album.objects.create(name=new_album_name, created_by=request.user)
    for photo_id in photo_ids:
        PhotoAlbum.objects.get_or_create(photo_id=photo_id, album=new_album)

    messages.success(
        request, f"Created album '{new_album.name}' with {len(photo_ids)} photo(s)."
    )
    return redirect("gallery:album_detail", pk=new_album.pk)


@login_required
def download_zip(request, album_pk=None):
    if album_pk:
        album = get_object_or_404(Album, pk=album_pk)
        photo_ids = album.photoalbum_set.values_list("photo_id", flat=True)
        photos = Photo.objects.filter(pk__in=photo_ids)
        filename = f"{album.name.lower().replace(' ', '_')}_album.zip"
    else:
        photos = Photo.objects.all()
        filename = "family_photos.zip"

    if not photos.exists():
        messages.warning(request, "No photos to download.")
        if album_pk:
            return redirect("gallery:album_detail", pk=album_pk)
        return redirect("gallery:album_list")

    def safe_chunks(p):
        try:
            f = p.image.open("rb")
        except Exception as e:
            print(f"Failed to open photo {p.id} for zip: {e}")
            return
        try:
            with f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    yield chunk
        except Exception as e:
            print(f"Failed reading photo {p.id} for zip: {e}")

    zs = zipstream.ZipStream(compress_type=zipstream.ZIP_DEFLATED)
    used_names = set()
    for photo in photos:
        try:
            name = os.path.basename(photo.image.name)
            base, ext = os.path.splitext(name)
            counter = 1
            while name in used_names:
                name = f"{base}_{counter}{ext}"
                counter += 1
            used_names.add(name)
            zs.add(safe_chunks(photo), name)
        except Exception as e:
            print(f"Failed to zip photo {photo.id}: {e}")

    response = StreamingHttpResponse(zs, content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
def photo_delete(request, pk):
    photo = get_object_or_404(Photo, pk=pk)
    if not (request.user.is_superuser or photo.uploaded_by == request.user):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"error": "Forbidden"}, status=403)
        messages.error(request, "You do not have permission to delete this photo.")
        return redirect("gallery:photo_detail", pk=pk)

    if request.method == "POST":
        album_pk = request.POST.get("album_pk") or request.GET.get("album_pk")

        if album_pk:
            PhotoAlbum.objects.filter(photo=photo, album_id=album_pk).delete()
            messages.success(request, "Photo removed from album.")

            if not photo.albums.exists():
                photo.delete()
                messages.success(request, "Photo deleted (was not in any other album).")

            return redirect("gallery:album_detail", pk=album_pk)
        else:
            PhotoAlbum.objects.filter(photo=photo).delete()
            photo.delete()
            messages.success(request, "Photo deleted successfully.")
            return redirect("gallery:album_list")

    return redirect("gallery:photo_detail", pk=pk)


@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("gallery:profile")
    else:
        form = ProfileForm(instance=request.user)

    photo_count = Photo.objects.filter(uploaded_by=request.user).count()
    return render(
        request,
        "gallery/profile.html",
        {"form": form, "photo_count": photo_count},
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
def user_list(request):
    users = User.objects.all()
    return render(request, "gallery/user_list.html", {"users": users})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def user_add(request):
    if request.method == "POST":
        form = RetroUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User '{user.username}' created successfully!")
            return redirect("gallery:user_list")
    else:
        form = RetroUserCreationForm()

    return render(request, "gallery/user_add.html", {"form": form})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    photo_count = Photo.objects.filter(uploaded_by=user).count()
    return render(
        request,
        "gallery/user_detail.html",
        {"profile_user": user, "photo_count": photo_count},
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
def user_albums(request, user_pk):
    profile_user = get_object_or_404(User, pk=user_pk)
    albums = Album.objects.filter(created_by=profile_user)
    return render(
        request,
        "gallery/user_albums.html",
        {"profile_user": profile_user, "albums": albums},
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
def user_album_detail(request, user_pk, pk):
    profile_user = get_object_or_404(User, pk=user_pk)
    album = get_object_or_404(Album, pk=pk, created_by=profile_user)
    photo_ids = album.photoalbum_set.values_list("photo_id", flat=True)
    photos = Photo.objects.filter(pk__in=photo_ids)

    if not photos.exists():
        return render(
            request,
            "gallery/user_album_empty.html",
            {"profile_user": profile_user, "album": album},
        )

    sort_field = request.GET.get("sort", "uploaded")
    sort_dir = request.GET.get("dir", "desc")

    if sort_dir == "asc":
        sort_by = SORT_FIELDS_ASC.get(sort_field, "-uploaded_at")
    else:
        sort_by = SORT_FIELDS.get(sort_field, "-uploaded_at")

    photos = photos.order_by(sort_by)

    if request.htmx and request.headers.get("HX-Target") == "photo-grid":
        return render(
            request,
            "gallery/partials/photo_grid.html",
            {"photos": photos, "sort": sort_field, "dir": sort_dir, "album": album},
        )

    context = {
        "profile_user": profile_user,
        "photos": photos,
        "album": album,
        "sort": sort_field,
        "dir": sort_dir,
    }
    return render(request, "gallery/user_album_detail.html", context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def user_edit(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = AdminUserUpdateForm(request.POST, instance=target_user)
        if form.is_valid():
            form.save()
            messages.success(
                request, f"User '{target_user.username}' updated successfully!"
            )
            return redirect("gallery:user_detail", pk=pk)
    else:
        form = AdminUserUpdateForm(instance=target_user)

    return render(
        request, "gallery/user_edit.html", {"form": form, "target_user": target_user}
    )


@login_required
@require_GET
def thumbnail_status(request):
    recent = timezone.now() - timedelta(hours=1)
    ready = Photo.objects.filter(
        thumbnail__isnull=False,
        uploaded_at__gte=recent,
    ).values_list("pk", flat=True)
    pending = Photo.objects.filter(
        thumbnail__isnull=True,
        uploaded_at__gte=recent,
    ).count()
    return JsonResponse({"ready": list(ready), "pending": pending})


@login_required
def bulk_download(request, album_pk):
    album = get_object_or_404(Album, pk=album_pk)
    raw = request.POST.get("photos", "")
    ids = [int(x) for x in raw.split(",") if x.strip().isdigit()]
    if not ids:
        messages.warning(request, "No photos selected.")
        return redirect("gallery:album_detail", pk=album_pk)

    photos = Photo.objects.filter(pk__in=ids)
    if not photos.exists():
        messages.warning(request, "No photos found.")
        return redirect("gallery:album_detail", pk=album_pk)

    filename = f"{album.name.lower().replace(' ', '_')}_selected.zip"

    def safe_chunks(p):
        try:
            f = p.image.open("rb")
        except Exception as e:
            print(f"Failed to open photo {p.id} for zip: {e}")
            return
        try:
            with f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    yield chunk
        except Exception as e:
            print(f"Failed reading photo {p.id} for zip: {e}")

    zs = zipstream.ZipStream(compress_type=zipstream.ZIP_DEFLATED)
    used_names = set()
    for photo in photos:
        try:
            name = os.path.basename(photo.image.name)
            base, ext = os.path.splitext(name)
            counter = 1
            while name in used_names:
                name = f"{base}_{counter}{ext}"
                counter += 1
            used_names.add(name)
            zs.add(safe_chunks(photo), name)
        except Exception as e:
            print(f"Failed to zip photo {photo.id}: {e}")

    response = StreamingHttpResponse(zs, content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
def set_album_cover(request, album_pk, photo_pk):
    album = get_object_or_404(Album, pk=album_pk)
    photo = get_object_or_404(Photo, pk=photo_pk)
    if request.user != album.created_by and not request.user.is_superuser:
        messages.error(request, "You don't have permission to edit this album.")
        return redirect("gallery:album_detail", pk=album_pk)
    if not album.photos.filter(pk=photo_pk).exists():
        messages.error(request, "Photo is not in this album.")
        return redirect("gallery:album_detail", pk=album_pk)
    album.cover_photo = photo
    album.save(update_fields=["cover_photo"])
    messages.success(request, f"Set photo as the cover for '{album.name}'.")
    return redirect(f"{reverse('gallery:photo_detail', args=[photo_pk])}?album={album_pk}")


@login_required
def photo_card_partial(request, pk):
    photo = get_object_or_404(Photo, pk=pk)
    return render(request, "gallery/partials/photo_card.html", {"photo": photo})
