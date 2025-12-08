from django.contrib import admin
from django.urls import path, include
from core.views.views import (
    home,
    pieces,
    switch_organization,
    login_view,
    create_new_piece,
    piece,
    upload_parts,
    roster,
    programs,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", login_view, name="login"),
    path("", home, name="home"),
    path("create_piece/", create_new_piece, name="create_piece"),
    path("pieces/", pieces, name="pieces"),
    path("piece/<str:piece_id>/", piece, name="piece"),
    path(
        "piece/<str:piece_id>/parts",
        upload_parts,
        name="upload_parts",
    ),
    path("roster/", roster, name="roster"),
    path("programs/", programs, name="programs"),
    path(
        "switch-organization/<str:organization_id>/",
        switch_organization,
        name="switch_organization",
    ),
    # API URL Paths
    path("api/", include("core.api.urls")),
]
