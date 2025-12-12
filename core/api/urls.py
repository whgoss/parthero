from django.urls import path
from core.api.views import PartCreateViewSet, PartViewSet

urlpatterns = [
    path(
        "edition/<str:edition_id>/part",
        PartCreateViewSet.as_view(),
        name="api_piece_part_create",
    ),
    path(
        "edition/<str:edition_id>/part/<str:part_id>",
        PartViewSet.as_view(),
        name="api_piece_part_update",
    ),
]
