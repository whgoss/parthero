from django.contrib import admin
from django.urls import path, include
from core.views.views import (
    home,
    pieces,
    switch_organization,
    login_view,
    create_new_piece,
    upload_parts,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", login_view, name="login"),
    path("", home, name="home"),
    path("pieces/", pieces, name="pieces"),
    path("create_piece/", create_new_piece, name="create_piece"),
    path(
        "piece/<str:piece_id>/parts",
        upload_parts,
        name="upload_parts",
    ),
    path(
        "switch-organization/<str:organization_id>/",
        switch_organization,
        name="switch_organization",
    ),
    path("api/", include("core.api.urls")),
]
