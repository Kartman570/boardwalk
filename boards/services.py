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
    if column.limit and column.cards.count() >= column.limit:
        raise ValueError("Column has reached its card limit")
    return Card.objects.create(column=column, title=title, description=description,
                               position=column.cards.count())


class Conflict(ValueError):
    pass


@transaction.atomic
def move_card(card, destination, position, revision):
    from .models import Card
    if destination.board_id != card.column.board_id:
        raise ValueError("Cannot move cards between boards")
    Board.objects.select_for_update().get(id=destination.board_id)
    card = Card.objects.select_for_update().get(id=card.id)
    if card.revision != revision:
        raise Conflict("Card has changed; reload before moving it")
    if type(position) is not int or position < 0:
        raise ValueError("Position must be a nonnegative integer")
    old_column = card.column_id
    target = list(destination.cards.exclude(id=card.id).order_by("position", "id"))
    if position > len(target):
        raise ValueError("Position is beyond the end of the column")
    if destination.limit and len(target) >= destination.limit:
        raise ValueError("Column has reached its card limit")
    target.insert(position, card)
    for index, item in enumerate(target):
        item.position = index
        item.column = destination
        item.revision += 1
        item.save(update_fields=["position", "column", "revision"])
    if old_column != destination.id:
        for index, item in enumerate(Card.objects.filter(column_id=old_column)):
            item.position = index
            item.revision += 1
            item.save(update_fields=["position", "revision"])
    card.refresh_from_db()
    return card
