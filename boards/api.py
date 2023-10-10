import json
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from .models import Column
from .services import add_card
from .access import get_board


def json_input(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        try:
            data = json.loads(request.body or b"{}")
            if not isinstance(data, dict):
                raise ValueError("Expected a JSON object")
            return view(request, data, *args, **kwargs)
        except (ValueError, TypeError, KeyError) as error:
            return JsonResponse({"error": str(error)}, status=400)
    return wrapped


@login_required
@require_POST
@json_input
def card_create(request, data, column_id):
    column = get_object_or_404(Column, id=column_id)
    get_board(request.user, column.board_id, write=True)
    card = add_card(column, data.get("title", ""), data.get("description", ""))
    return JsonResponse({"id": card.id, "title": card.title}, status=201)


@login_required
@require_POST
@json_input
def member_set(request, data, board_id):
    from django.contrib.auth import get_user_model
    from django.core.exceptions import PermissionDenied
    from .models import Membership
    board = get_board(request.user, board_id)
    if board.owner_id != request.user.id:
        raise PermissionDenied("Only the owner can change members")
    user = get_object_or_404(get_user_model(), username=data.get("username", ""))
    if user.id == board.owner_id:
        raise ValueError("The owner cannot be assigned a member role")
    role = data.get("role")
    if role not in ("viewer", "editor", "remove"):
        raise ValueError("Role must be viewer editor or remove")
    if role == "remove":
        Membership.objects.filter(board=board, user=user).delete()
    else:
        Membership.objects.update_or_create(board=board, user=user, defaults={"role": role})
    return JsonResponse({"username": user.username, "role": role})


@login_required
@require_POST
@json_input
def card_move(request, data, card_id):
    from .models import Card
    from .services import Conflict, move_card
    card = get_object_or_404(Card.objects.select_related("column"), id=card_id)
    get_board(request.user, card.column.board_id, write=True)
    destination = get_object_or_404(Column, id=data.get("column_id"))
    try:
        card = move_card(card, destination, data.get("position", 0), data.get("revision"))
    except Conflict as error:
        return JsonResponse({"error": str(error)}, status=409)
    return JsonResponse({"id": card.id, "column_id": card.column_id, "revision": card.revision})
