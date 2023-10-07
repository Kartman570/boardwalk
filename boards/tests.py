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


class AccessTests(TestCase):
    def setUp(self):
        from .models import Membership
        users = get_user_model().objects
        self.owner = users.create_user("owner")
        self.editor = users.create_user("editor")
        self.viewer = users.create_user("viewer")
        self.outsider = users.create_user("outsider")
        self.board = create_board(self.owner, "Private")
        Membership.objects.create(board=self.board, user=self.editor, role="editor")
        Membership.objects.create(board=self.board, user=self.viewer, role="viewer")
        self.url = "/api/columns/%s/cards/" % self.board.columns.first().id

    def test_editor_can_create(self):
        self.client.force_login(self.editor)
        self.assertEqual(self.client.post(self.url, {"title": "Card"},
                                         content_type="application/json").status_code, 201)

    def test_viewer_cannot_create(self):
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.post(self.url, {"title": "Card"},
                                         content_type="application/json").status_code, 403)
        self.assertEqual(self.client.get("/boards/%s/" % self.board.id).status_code, 200)

    def test_outsider_cannot_read(self):
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get("/boards/%s/" % self.board.id).status_code, 404)
        self.assertNotContains(self.client.get("/"), "Private")

    def test_only_owner_changes_members(self):
        url = "/api/boards/%s/members/" % self.board.id
        self.client.force_login(self.editor)
        self.assertEqual(self.client.post(url, {"username": "outsider", "role": "editor"},
                                         content_type="application/json").status_code, 403)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(url, {"username": "outsider", "role": "viewer"},
                                         content_type="application/json").status_code, 200)
        self.assertEqual(self.board.memberships.count(), 3)
