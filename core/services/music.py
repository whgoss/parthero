from typing import List
from core.dtos.music import PieceDTO
from core.models import Piece


def get_pieces_for_organization(organization_id: str) -> List[PieceDTO]:
    pieces = Piece.objects.filter(organization__id__in=[organization_id])
    return [PieceDTO.from_model(piece) for piece in pieces]


def get_pieces_count_for_organization(organization_id: str) -> int:
    return Piece.objects.filter(organization__id__in=[organization_id]).count()
