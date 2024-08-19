from django.http import JsonResponse

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from .access import get_board, visible_boards
from .services import create_board


def health(request):
    return JsonResponse({"status": "ok"})


@login_required
@require_http_methods(["GET", "POST"])
def boards(request):
    if request.method == "POST":
        try:
            board = create_board(request.user, request.POST.get("name", ""))
        except ValueError as error:
            return JsonResponse({"error": str(error)}, status=400)
        return redirect("board", board_id=board.id)
    return render(request, "boards/index.html", {"boards": visible_boards(request.user)})


@login_required
def board(request, board_id):
    item = get_board(request.user, board_id)
    columns = [{"item": column, "cards": column.cards.filter(archived=False).prefetch_related(
        "labels", "comments__author")} for column in item.columns.all()]
    can_edit = item.owner_id == request.user.id or item.memberships.filter(
        user=request.user, role="editor").exists()
    return render(request, "boards/board.html", {"board": item, "columns": columns,
                                                 "can_edit": can_edit})
