from django.contrib.auth import get_user_model
from django.test import TestCase
from .models import Board
from .services import create_board


class BoardTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("owner", password="testing-password")
        self.client.force_login(self.user)

    def test_create_and_render(self):
        response = self.client.post("/", {"name": "Weekend"})
        board = Board.objects.get()
        self.assertRedirects(response, "/boards/%s/" % board.id)
        self.assertEqual(board.columns.count(), 3)

    def test_invalid_name_does_not_create_board(self):
        self.assertEqual(self.client.post("/", {"name": " "}).status_code, 400)
        self.assertEqual(Board.objects.count(), 0)

    def test_card_endpoint(self):
        board = create_board(self.user, "One")
        column = board.columns.first()
        response = self.client.post("/api/columns/%s/cards/" % column.id,
                                    {"title": "Build shelf"}, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(column.cards.get().title, "Build shelf")
