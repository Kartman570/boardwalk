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
    if column.limit and column.cards.filter(archived=False).count() >= column.limit:
        raise ValueError("Column has reached its card limit")
    return Card.objects.create(column=column, title=title, description=description,
                               position=column.cards.filter(archived=False).count())


class Conflict(ValueError):
    pass


@transaction.atomic
def move_card(card, destination, position, revision):
    from .models import Card
    if destination.board_id != card.column.board_id:
        raise ValueError("Cannot move cards between boards")
    Board.objects.select_for_update().get(id=destination.board_id)
    card = Card.objects.select_for_update().get(id=card.id)
    if card.archived:
        raise ValueError("Restore the card before moving it")
    if card.revision != revision:
        raise Conflict("Card has changed; reload before moving it")
    if type(position) is not int or position < 0:
        raise ValueError("Position must be a nonnegative integer")
    old_column = card.column_id
    target = list(destination.cards.filter(archived=False).exclude(id=card.id).order_by("position", "id"))
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
        for index, item in enumerate(Card.objects.filter(column_id=old_column, archived=False)):
            item.position = index
            item.revision += 1
            item.save(update_fields=["position", "revision"])
    card.refresh_from_db()
    return card


@transaction.atomic
def update_card(card, data):
    from .models import Card
    Board.objects.select_for_update().get(id=card.column.board_id)
    card = Card.objects.select_for_update().get(id=card.id)
    if data.get("revision") != card.revision:
        raise Conflict("Card has changed; reload before editing it")
    title = data.get("title", card.title)
    description = data.get("description", card.description)
    archived = data.get("archived", card.archived)
    if not isinstance(title, str) or not title.strip() or len(title) > 160:
        raise ValueError("Invalid card title")
    if not isinstance(description, str) or len(description) > 10000:
        raise ValueError("Invalid card description")
    if type(archived) is not bool:
        raise ValueError("Archived must be a boolean")
    if card.archived and not archived:
        count = card.column.cards.filter(archived=False).count()
        if card.column.limit and count >= card.column.limit:
            raise ValueError("Column has reached its card limit")
        card.position = count
    card.title, card.description, card.archived = title.strip(), description, archived
    card.revision += 1
    card.save()
    if archived:
        for index, item in enumerate(card.column.cards.filter(archived=False)):
            if item.position != index:
                item.position = index
                item.revision += 1
                item.save(update_fields=["position", "revision"])
    return card
