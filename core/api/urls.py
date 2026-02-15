from django.urls import path
from core.api.views import (
    PartAssetViewSet,
    PieceSearchViewSet,
    ProgramChecklistViewSet,
    ProgramPieceViewSet,
    ProgramMusicianViewSet,
    ProgramMusicianInstrumentViewSet,
    MusicianSearchViewSet,
    DomoWorkSearchViewSet,
)

part_asset_create = PartAssetViewSet.as_view({"post": "create"})
part_asset_patch = PartAssetViewSet.as_view({"patch": "partial_update"})
part_assets_list = PartAssetViewSet.as_view({"get": "list"})
piece_search = PieceSearchViewSet.as_view({"get": "list"})
program_piece = ProgramPieceViewSet.as_view({"put": "update", "delete": "delete"})
program_musicians_list = ProgramMusicianViewSet.as_view(
    {"get": "list", "post": "create"}
)
program_musicians_delete = ProgramMusicianViewSet.as_view({"delete": "delete"})
program_musician_instrument_update = ProgramMusicianInstrumentViewSet.as_view(
    {"put": "update", "delete": "delete"}
)
program_checklist_patch = ProgramChecklistViewSet.as_view({"patch": "partial_update"})
musicians_search = MusicianSearchViewSet.as_view({"get": "list"})
domo_search = DomoWorkSearchViewSet.as_view({"get": "list"})


urlpatterns = [
    path(
        "piece/<str:piece_id>/asset",
        part_asset_create,
        name="api_part_asset_create",
    ),
    path(
        "piece/<str:piece_id>/asset/<str:part_asset_id>",
        part_asset_patch,
        name="api_part_asset_patch",
    ),
    path(
        "pieces/search",
        piece_search,
        name="api_piece_search",
    ),
    path(
        "program/<str:program_id>/pieces/<str:piece_id>",
        program_piece,
        name="api_program_piece_update",
    ),
    path(
        "piece/<str:piece_id>/assets",
        part_assets_list,
        name="api_piece_part_assets",
    ),
    path(
        "programs/<str:program_id>/musicians",
        program_musicians_list,
        name="api_program_musicians",
    ),
    path(
        "programs/<str:program_id>/musicians/<str:program_musician_id>",
        program_musicians_delete,
        name="api_program_musicians_delete",
    ),
    path(
        "programs/<str:program_id>/musicians/<str:program_musician_id>/instruments",
        program_musician_instrument_update,
        name="api_program_musician_instrument_update",
    ),
    path(
        "programs/<str:program_id>/checklist",
        program_checklist_patch,
        name="api_program_checklist_patch",
    ),
    path(
        "musicians/search",
        musicians_search,
        name="api_musicians_search",
    ),
    path(
        "domo/search",
        domo_search,
        name="api_domo_search",
    ),
]
