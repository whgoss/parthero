from core.api.views.assignments import ProgramAssignmentViewSet
from core.api.views.domo import DomoWorkSearchViewSet
from core.api.views.magic_links import (
    MagicAssignmentConfirmViewSet,
    MagicAssignmentPartViewSet,
    MagicAssignmentViewSet,
)
from core.api.views.music import PartAssetViewSet, PieceSearchViewSet
from core.api.views.organizations import MusicianSearchViewSet
from core.api.views.programs import (
    ProgramChecklistViewSet,
    ProgramMusicianInstrumentViewSet,
    ProgramMusicianViewSet,
    ProgramPieceViewSet,
)

__all__ = [
    "DomoWorkSearchViewSet",
    "MagicAssignmentConfirmViewSet",
    "MagicAssignmentPartViewSet",
    "MagicAssignmentViewSet",
    "ProgramAssignmentViewSet",
    "MusicianSearchViewSet",
    "PartAssetViewSet",
    "PieceSearchViewSet",
    "ProgramChecklistViewSet",
    "ProgramMusicianInstrumentViewSet",
    "ProgramMusicianViewSet",
    "ProgramPieceViewSet",
]
