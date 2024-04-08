from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from boards.models import Board
from boards.services import add_card, create_board


class Command(BaseCommand):
    help = "Create a small demo board for a local account"

    def add_arguments(self, parser):
        parser.add_argument("--username", default="demo")
        parser.add_argument("--password", required=True)

    @transaction.atomic
    def handle(self, *args, **options):
        if len(options["password"]) < 10:
            raise CommandError("Use a password of at least ten characters")
        user, created = get_user_model().objects.get_or_create(username=options["username"])
        if created:
            user.set_password(options["password"])
            user.save()
        if Board.objects.filter(owner=user, name="Workshop").exists():
            self.stdout.write("Demo board already exists")
            return
        board = create_board(user, "Workshop")
        first, second, third = list(board.columns.all())
        add_card(first, "Sort spare parts", "Put screws and hinges into separate trays.")
        add_card(first, "Measure the shelf", "Check the wall clearance before cutting.")
        add_card(second, "Sand the tabletop", "Start with the rough edges.")
        add_card(third, "Find the toolbox")
        self.stdout.write("Created Workshop for " + user.username)
