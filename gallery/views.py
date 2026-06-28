import os
import zipfile
from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import RetroUserCreationForm
from .models import Photo


def home(request):
    if request.user.is_authenticated:
        return redirect("gallery:photo_list")
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
def photo_list(request):
    sort_field = request.GET.get("sort", "uploaded")
    sort_dir = request.GET.get("dir", "desc")

    if sort_dir == "asc":
        sort_by = SORT_FIELDS_ASC.get(sort_field, "-uploaded_at")
    else:
        sort_by = SORT_FIELDS.get(sort_field, "-uploaded_at")

    photos = Photo.objects.all().order_by(sort_by)
    if request.htmx and request.headers.get("HX-Target") == "photo-grid":
        return render(request, "gallery/partials/photo_grid.html", {"photos": photos, "sort": sort_field, "dir": sort_dir})

    users_count = User.objects.count()
    context = {
        "photos": photos,
        "users_count": users_count,
        "is_admin": request.user.is_superuser,
        "sort": sort_field,
        "dir": sort_dir,
    }
    return render(request, "gallery/photo_list.html", context)


@login_required
def photo_upload(request):
    if request.method == "POST":
        files = request.FILES.getlist("photos") or request.FILES.getlist("file")

        if not files:
            return HttpResponse("No photos selected", status=400)

        uploaded_photos = []
        for file in files:
            try:
                photo = Photo.objects.create(image=file, uploaded_by=request.user)
                uploaded_photos.append(photo)
            except Exception as e:
                print(f"Error saving photo: {e}")
                return HttpResponse(f"Error saving photo: {str(e)}", status=500)

        if request.htmx:
            photos = Photo.objects.all()
            return render(request, "gallery/partials/photo_grid.html", {"photos": photos})

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True, "count": len(uploaded_photos)})

        messages.success(request, f"Successfully uploaded {len(uploaded_photos)} photos!")
        return redirect("gallery:photo_list")

    return render(request, "gallery/upload.html")


@login_required
def photo_detail(request, pk):
    photo = get_object_or_404(Photo, pk=pk)
    if request.htmx:
        return render(request, "gallery/partials/photo_detail.html", {
            "photo": photo,
            "is_admin": request.user.is_superuser,
        })
    photos = Photo.objects.all()
    return render(
        request,
        "gallery/photo_detail_page.html",
        {
            "photo": photo,
            "photos": photos,
            "is_admin": request.user.is_superuser,
        },
    )


@login_required
def download_zip(request):
    photos = Photo.objects.all()
    if not photos.exists():
        messages.warning(request, "No photos to download.")
        return redirect("gallery:photo_list")

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
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

                with photo.image.open("rb") as f:
                    zip_file.writestr(name, f.read())
            except Exception as e:
                print(f"Failed to zip photo {photo.id}: {e}")

    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = 'attachment; filename="family_event_photos.zip"'
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
        photo.delete()
        messages.success(request, "Photo deleted successfully.")
        return redirect("gallery:photo_list")

    return redirect("gallery:photo_detail", pk=pk)


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
