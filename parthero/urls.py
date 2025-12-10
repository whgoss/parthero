from django.contrib import admin
from django.urls import path, include
from core.views.views import (
    home,
    pieces,
    login_view,
    create_new_piece,
    piece,
    programs,
    upload_parts,
)
from core.views import organizations

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
    path("roster/", organizations.roster, name="roster"),
    path("musician/", organizations.musician, name="musician"),
    path("musician/<str:musician_id>/", organizations.musician, name="musician"),
    path("upload_roster/", organizations.upload_roster, name="upload_roster"),
    path("programs/", programs, name="programs"),
    path(
        "switch-organization/<str:organization_id>/",
        organizations.switch_organization,
        name="switch_organization",
    ),
    # API URL Paths
    path("api/", include("core.api.urls")),
]
