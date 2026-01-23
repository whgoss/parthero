from django.urls import path
from core.api.views import PartCreateViewSet, PartViewSet

urlpatterns = [
    path(
        "piece/<str:piece_id>/part",
        PartCreateViewSet.as_view(),
        name="api_part_create",
    ),
    path(
        "piece/<str:piece_id>/part/<str:part_id>",
        PartViewSet.as_view(),
        name="api_part_update",
    ),
]
