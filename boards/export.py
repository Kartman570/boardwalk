import csv
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .access import get_board
from .models import Card


def cell(value):
    value = str(value)
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value


@login_required
def export_board(request, board_id):
    board = get_board(request.user, board_id)
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="board.csv"'
    writer = csv.writer(response)
    writer.writerow(["id", "column", "title", "description", "archived", "labels"])
    for card in Card.objects.filter(column__board=board).select_related("column").prefetch_related(
            "labels"):
        writer.writerow([card.id, cell(card.column.name), cell(card.title), cell(card.description),
                         card.archived, cell(", ".join(label.name for label in card.labels.all()))])
    return response
