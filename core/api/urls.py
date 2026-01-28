from django.urls import path
from core.api.views import PartAssetViewSet, PieceSearchViewSet, ProgramPieceViewSet

part_asset_create = PartAssetViewSet.as_view({"post": "create"})
part_asset_patch = PartAssetViewSet.as_view({"patch": "partial_update"})
piece_search = PieceSearchViewSet.as_view({"get": "list"})
program_piece = ProgramPieceViewSet.as_view({"put": "update", "delete": "delete"})

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
]
