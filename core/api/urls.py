from django.urls import path
from core.api.views import (
    PartAssetViewSet,
    PieceSearchViewSet,
    ProgramPieceViewSet,
    DomoWorkSearchViewSet,
)

part_asset_create = PartAssetViewSet.as_view({"post": "create"})
part_asset_patch = PartAssetViewSet.as_view({"patch": "partial_update"})
part_assets_list = PartAssetViewSet.as_view({"get": "list"})
piece_search = PieceSearchViewSet.as_view({"get": "list"})
program_piece = ProgramPieceViewSet.as_view({"put": "update", "delete": "delete"})
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
        "domo/search",
        domo_search,
        name="api_domo_search",
    ),
]
