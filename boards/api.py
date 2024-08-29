import json
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from .models import Activity, Column
from .services import add_card
from .access import get_board


def json_input(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        try:
            data = json.loads(request.body or b"{}")
            if not isinstance(data, dict):
                raise ValueError("Expected a JSON object")
            with transaction.atomic():
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
    Activity.objects.create(board=column.board, actor=request.user,
                            action="card added", detail=card.title)
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
    Activity.objects.create(board=destination.board, actor=request.user,
                            action="card moved", detail=card.title + " -> " + destination.name)
    return JsonResponse({"id": card.id, "column_id": card.column_id, "revision": card.revision})


@login_required
@require_POST
@json_input
def column_limit(request, data, column_id):
    column = get_object_or_404(Column, id=column_id)
    get_board(request.user, column.board_id, write=True)
    limit = data.get("limit")
    if type(limit) is not int or not 0 <= limit <= 10000:
        raise ValueError("Limit must be an integer between zero and ten thousand")
    column.limit = limit
    column.save(update_fields=["limit"])
    return JsonResponse({"id": column.id, "limit": limit})


@login_required
@require_POST
@json_input
def comment_add(request, data, card_id):
    from .models import Card, Comment
    card = get_object_or_404(Card.objects.select_related("column"), id=card_id)
    get_board(request.user, card.column.board_id, write=True)
    body = data.get("body", "")
    if not isinstance(body, str) or not body.strip() or len(body) > 4000:
        raise ValueError("Comment must contain 1 to 4000 characters")
    comment = Comment.objects.create(card=card, author=request.user, body=body.strip())
    Activity.objects.create(board=card.column.board, actor=request.user,
                            action="comment added", detail=card.title)
    return JsonResponse({"id": comment.id, "body": comment.body}, status=201)


@login_required
def activity(request, board_id):
    board = get_board(request.user, board_id)
    entries = list(board.activity.values("id", "actor__username", "action", "detail")[:100])
    return JsonResponse({"activity": entries})


@login_required
@require_POST
@json_input
def card_labels(request, data, card_id):
    from .models import Card, Label
    card = get_object_or_404(Card.objects.select_related("column"), id=card_id)
    board = get_board(request.user, card.column.board_id, write=True)
    names = data.get("labels", [])
    if (not isinstance(names, list) or len(names) > 12
            or any(not isinstance(name, str) or not name.strip() or len(name) > 40
                   for name in names)):
        raise ValueError("Use up to twelve nonempty label names of at most forty characters")
    labels = [Label.objects.get_or_create(board=board, name=name.strip())[0] for name in names]
    card.labels.set(labels)
    Activity.objects.create(board=board, actor=request.user,
                            action="labels changed", detail=card.title)
    return JsonResponse({"labels": sorted({label.name for label in labels})})


@login_required
@require_POST
@json_input
def card_update(request, data, card_id):
    from .models import Card
    from .services import Conflict, update_card
    card = get_object_or_404(Card.objects.select_related("column"), id=card_id)
    board = get_board(request.user, card.column.board_id, write=True)
    try:
        card = update_card(card, data)
    except Conflict as error:
        return JsonResponse({"error": str(error)}, status=409)
    Activity.objects.create(board=board, actor=request.user,
                            action="card updated", detail=card.title)
    return JsonResponse({"id": card.id, "revision": card.revision, "archived": card.archived})


@login_required
def cards(request, board_id):
    from django.db.models import Q
    from .models import Card
    board = get_board(request.user, board_id)
    rows = Card.objects.filter(column__board=board, archived=request.GET.get("archived") == "1")
    query = request.GET.get("q", "").strip()
    if query:
        rows = rows.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if request.GET.get("label"):
        rows = rows.filter(labels__name=request.GET["label"])
    items = [{"id": card.id, "title": card.title, "description": card.description,
              "column_id": card.column_id, "position": card.position, "revision": card.revision,
              "labels": [label.name for label in card.labels.all()],
              "comments": [{"author": comment.author.username, "body": comment.body}
                           for comment in card.comments.all()]} for card in rows.prefetch_related(
                               "labels", "comments__author")[:200]]
    return JsonResponse({"cards": items})
