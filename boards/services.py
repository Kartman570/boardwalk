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


@transaction.atomic
def add_card(column, title, description=""):
    from .models import Card
    title = title.strip()
    if not title or len(title) > 160 or len(description) > 10000:
        raise ValueError("Card title or description has an invalid length")
    Board.objects.select_for_update().get(id=column.board_id)
    return Card.objects.create(column=column, title=title, description=description,
                               position=column.cards.count())
