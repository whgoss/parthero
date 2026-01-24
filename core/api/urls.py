from django.urls import path
from core.api.views import PartAssetViewSet

part_asset_create = PartAssetViewSet.as_view({"post": "create"})
part_asset_patch = PartAssetViewSet.as_view({"patch": "partial_update"})

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
]
