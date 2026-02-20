from django.urls import path
from core.api.views import (
    PartAssetViewSet,
    PieceSearchViewSet,
    ProgramChecklistViewSet,
    MagicAssignmentConfirmViewSet,
    MagicAssignmentPartViewSet,
    MagicAssignmentViewSet,
    MagicDeliveryDownloadViewSet,
    MagicDeliveryViewSet,
    ProgramAssignmentViewSet,
    ProgramPieceViewSet,
    ProgramMusicianViewSet,
    ProgramMusicianInstrumentViewSet,
    RosterMusicianViewSet,
    DomoWorkSearchViewSet,
)

part_asset_create = PartAssetViewSet.as_view({"post": "create"})
part_asset_patch = PartAssetViewSet.as_view({"patch": "partial_update"})
part_assets_list = PartAssetViewSet.as_view({"get": "list"})
piece_search = PieceSearchViewSet.as_view({"get": "list"})
program_pieces = ProgramPieceViewSet.as_view({"get": "list"})
program_piece = ProgramPieceViewSet.as_view({"put": "update", "delete": "delete"})
program_musicians_list = ProgramMusicianViewSet.as_view(
    {"get": "list", "post": "create"}
)
program_musicians_delete = ProgramMusicianViewSet.as_view({"delete": "delete"})
program_musician_instrument_update = ProgramMusicianInstrumentViewSet.as_view(
    {"put": "update", "delete": "delete"}
)
program_checklist = ProgramChecklistViewSet.as_view(
    {"get": "retrieve", "patch": "partial_update"}
)
program_assignments = ProgramAssignmentViewSet.as_view({"get": "list"})
program_assignment_part = ProgramAssignmentViewSet.as_view({"patch": "partial_update"})
musicians_search = RosterMusicianViewSet.as_view({"get": "list"})
domo_search = DomoWorkSearchViewSet.as_view({"get": "list"})
magic_assignments_data = MagicAssignmentViewSet.as_view({"get": "retrieve"})
magic_assignments_part = MagicAssignmentPartViewSet.as_view({"patch": "partial_update"})
magic_assignments_confirm = MagicAssignmentConfirmViewSet.as_view({"post": "create"})
magic_delivery_data = MagicDeliveryViewSet.as_view({"get": "retrieve"})
magic_delivery_downloads = MagicDeliveryDownloadViewSet.as_view({"get": "list"})
magic_delivery_piece_downloads = MagicDeliveryDownloadViewSet.as_view(
    {"get": "retrieve"}
)


urlpatterns = [
    path(
        "pieces/<str:piece_id>/asset",
        part_asset_create,
        name="api_part_asset_create",
    ),
    path(
        "pieces/<str:piece_id>/asset/<str:part_asset_id>",
        part_asset_patch,
        name="api_part_asset_patch",
    ),
    path(
        "pieces/search",
        piece_search,
        name="api_piece_search",
    ),
    path(
        "programs/<str:program_id>/pieces",
        program_pieces,
        name="api_program_pieces",
    ),
    path(
        "programs/<str:program_id>/pieces/<str:piece_id>",
        program_piece,
        name="api_program_piece_update",
    ),
    path(
        "pieces/<str:piece_id>/assets",
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
        program_checklist,
        name="api_program_checklist_patch",
    ),
    path(
        "programs/<str:program_id>/assignments",
        program_assignments,
        name="api_program_assignments",
    ),
    path(
        "programs/<str:program_id>/assignments/part/<str:part_id>",
        program_assignment_part,
        name="api_program_assignment_part",
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
    path(
        "magic/<str:token>/assignments",
        magic_assignments_data,
        name="api_magic_assignments_data",
    ),
    path(
        "magic/<str:token>/assignments/part/<str:part_id>",
        magic_assignments_part,
        name="api_magic_assignments_part",
    ),
    path(
        "magic/<str:token>/assignments/confirm",
        magic_assignments_confirm,
        name="api_magic_assignments_confirm",
    ),
    path(
        "magic/<str:token>/delivery",
        magic_delivery_data,
        name="api_magic_delivery_data",
    ),
    path(
        "magic/<str:token>/delivery/downloads",
        magic_delivery_downloads,
        name="api_magic_delivery_downloads",
    ),
    path(
        "magic/<str:token>/delivery/downloads/piece/<str:piece_id>",
        magic_delivery_piece_downloads,
        name="api_magic_delivery_piece_downloads",
    ),
]
