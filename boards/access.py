from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import Board


def visible_boards(user):
    return Board.objects.filter(Q(owner=user) | Q(memberships__user=user)).distinct()


def get_board(user, board_id, write=False):
    board = get_object_or_404(visible_boards(user), id=board_id)
    if write and board.owner_id != user.id:
        if not board.memberships.filter(user=user, role="editor").exists():
            raise PermissionDenied("This board is read-only")
    return board
