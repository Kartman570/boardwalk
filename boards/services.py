from django.db import transaction
from .models import Board, Column


@transaction.atomic
def create_board(user, name):
    name = name.strip()
    if not name or len(name) > 120:
        raise ValueError("Board name must contain 1 to 120 characters")
    board = Board.objects.create(owner=user, name=name)
    for index, title in enumerate(("To do", "Doing", "Done")):
        Column.objects.create(board=board, name=title, position=index)
    return board
