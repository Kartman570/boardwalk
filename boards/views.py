from django.http import JsonResponse


def health(request):
    return JsonResponse({"status": "ok"})


from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from .access import get_board, visible_boards
from .services import create_board


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
    return render(request, "boards/board.html", {"board": item})
