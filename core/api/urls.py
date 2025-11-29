from django.urls import path
from core.api.views import PartViewSet

urlpatterns = [
    path(
        "piece/<str:piece_id>/part",
        PartViewSet.as_view(),
        name="api_piece_part_create",
    ),
]
