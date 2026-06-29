from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "gallery"

urlpatterns = [
    # Root redirect
    path("", views.home, name="home"),
    # Auth
    path(
        "auth/",
        auth_views.LoginView.as_view(
            template_name="gallery/login.html",
            extra_context={"next": "/"},
        ),
        name="auth_login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="auth_logout"),
    # Photos
    path("photos/", views.photo_list, name="photo_list"),
    path("photos/upload/", views.photo_upload, name="photo_upload"),
    path("photos/<int:pk>/", views.photo_detail, name="photo_detail"),
    path("photos/<int:pk>/delete/", views.photo_delete, name="photo_delete"),
    # Users (admin only)
    path("users/", views.user_list, name="user_list"),
    path("users/add/", views.user_add, name="user_add"),
    path("users/<int:pk>/", views.user_detail, name="user_detail"),
    # Download
    path("download-all/", views.download_zip, name="download_zip"),
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
