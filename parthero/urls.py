from django.contrib import admin
from django.urls import path, include
from core.views.views import (
    home,
    get_pieces_view,
    login_view,
    create_piece_view,
    select_piece,
    search,
    get_piece_view,
    download_part_asset,
)
from core.views.programs import create_program_view, get_program_view, get_programs_view
from core.views.magic_links import assignment_magic_link_view, delivery_magic_link_view
from core.views import organizations

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", login_view, name="login"),
    path("", home, name="home"),
    path("create_piece/", create_piece_view, name="create_piece"),
    path("pieces/", get_pieces_view, name="pieces"),
    path("pieces/<str:piece_id>/", get_piece_view, name="piece"),
    path(
        "pieces/<str:piece_id>/asset/<str:part_asset_id>/download",
        download_part_asset,
        name="download_part_asset",
    ),
    path("roster/", organizations.roster, name="roster"),
    path("musicians/", organizations.musician, name="musician"),
    path("musicians/<str:musician_id>/", organizations.musician, name="musician"),
    path("upload_roster/", organizations.upload_roster, name="upload_roster"),
    path("programs/", get_programs_view, name="programs"),
    path("programs/<str:program_id>/", get_program_view, name="program"),
    path("create_program/", create_program_view, name="create_program"),
    path("search/", search, name="search"),
    path(
        "switch-organization/<str:organization_id>/",
        organizations.switch_organization,
        name="switch_organization",
    ),
    path("select_piece/", select_piece, name="select_piece"),
    # Magic link workflow
    path(
        "magic/<str:token>/assignments/",
        assignment_magic_link_view,
        name="magic_assignments",
    ),
    path(
        "magic/<str:token>/delivery/",
        delivery_magic_link_view,
        name="magic_delivery",
    ),
    # API URL Paths
    path("api/", include("core.api.urls")),
]
