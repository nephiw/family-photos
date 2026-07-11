from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "gallery"

urlpatterns = [
    path("", views.home, name="home"),
    path(
        "auth/",
        auth_views.LoginView.as_view(
            template_name="gallery/login.html",
            extra_context={"next": "/"},
        ),
        name="auth_login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="auth_logout"),
    # Albums
    path("albums/", views.album_list, name="album_list"),
    path("albums/create/", views.album_create, name="album_create"),
    path("albums/<int:pk>/", views.album_detail, name="album_detail"),
    path("albums/<int:pk>/choose/", views.album_choose_photos, name="album_choose_photos"),
    path("albums/<int:pk>/delete/", views.album_delete, name="album_delete"),
    # Photos
    path("photos/", views.photo_list, name="photo_list"),
    path("photos/upload/", views.photo_upload, name="photo_upload"),
    path("photos/<int:pk>/", views.photo_detail, name="photo_detail"),
    path("photos/<int:pk>/delete/", views.photo_delete, name="photo_delete"),
    path("photos/<int:pk>/add-to-album/", views.photo_add_to_album, name="photo_add_to_album"),
    # Bulk actions
    path("albums/<int:album_pk>/bulk/delete/", views.bulk_delete, name="bulk_delete"),
    path("albums/<int:album_pk>/bulk/add-to-album/", views.bulk_add_to_album, name="bulk_add_to_album"),
    path("albums/<int:album_pk>/bulk/create-album/", views.bulk_create_album, name="bulk_create_album"),
    path("albums/<int:album_pk>/bulk/download/", views.bulk_download, name="bulk_download"),
    # Users (admin only)
    path("users/", views.user_list, name="user_list"),
    path("users/add/", views.user_add, name="user_add"),
    path("users/<int:pk>/", views.user_detail, name="user_detail"),
    path("users/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path("users/<int:user_pk>/albums/", views.user_albums, name="user_albums"),
    path("users/<int:user_pk>/albums/<int:pk>/", views.user_album_detail, name="user_album_detail"),
    # Profile
    path("profile/", views.profile, name="profile"),
    # Download
    path("download-all/", views.download_zip, name="download_zip"),
    path("albums/<int:album_pk>/download/", views.download_zip, name="album_download_zip"),
    # Thumbnail polling
    path(
        "photos/thumbnail-status/",
        views.thumbnail_status,
        name="thumbnail_status",
    ),
    path(
        "photos/partial/card/<int:pk>/",
        views.photo_card_partial,
        name="photo_card_partial",
    ),
]
