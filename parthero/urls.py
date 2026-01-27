from django.contrib import admin
from django.urls import path, include
from core.views.views import (
    home,
    get_pieces_view,
    get_parts_view,
    login_view,
    create_new_piece,
    select_piece,
    search,
    get_piece_view,
    programs,
    download_part_asset,
)
from core.views import organizations

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", login_view, name="login"),
    path("", home, name="home"),
    path("create_piece/", create_new_piece, name="create_piece"),
    path("pieces/", get_pieces_view, name="pieces"),
    path("piece/<str:piece_id>/", get_piece_view, name="piece"),
    path("piece/<str:piece_id>/parts/", get_parts_view, name="get_parts"),
    path(
        "piece/<str:piece_id>/asset/<str:part_asset_id>/download",
        download_part_asset,
        name="download_part_asset",
    ),
    path("roster/", organizations.roster, name="roster"),
    path("musician/", organizations.musician, name="musician"),
    path("musician/<str:musician_id>/", organizations.musician, name="musician"),
    path("upload_roster/", organizations.upload_roster, name="upload_roster"),
    path("programs/", programs, name="programs"),
    path("search/", search, name="search"),
    path(
        "switch-organization/<str:organization_id>/",
        organizations.switch_organization,
        name="switch_organization",
    ),
    path("select_piece/", select_piece, name="select_piece"),
    # API URL Paths
    path("api/", include("core.api.urls")),
]
