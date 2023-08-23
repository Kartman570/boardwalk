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
