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


class OrderingTests(TestCase):
    def setUp(self):
        from .services import add_card
        self.user = get_user_model().objects.create_user("owner")
        self.board = create_board(self.user, "Work")
        self.source, self.target = list(self.board.columns.all())[:2]
        self.first = add_card(self.source, "First")
        self.second = add_card(self.source, "Second")
        self.client.force_login(self.user)

    def move(self, card, column, position=0, revision=0):
        return self.client.post("/api/cards/%s/move/" % card.id,
                                {"column_id": column.id, "position": position,
                                 "revision": revision}, content_type="application/json")

    def test_move_compacts_both_columns(self):
        self.assertEqual(self.move(self.first, self.target).status_code, 200)
        self.second.refresh_from_db()
        self.assertEqual(self.second.position, 0)
        self.assertEqual(self.target.cards.count(), 1)

    def test_stale_revision_is_conflict(self):
        self.assertEqual(self.move(self.first, self.target).status_code, 200)
        self.assertEqual(self.move(self.first, self.source).status_code, 409)

    def test_wip_limit_rolls_back(self):
        from .services import add_card
        self.target.limit = 1
        self.target.save()
        add_card(self.target, "Already here")
        self.assertEqual(self.move(self.first, self.target).status_code, 400)
        self.first.refresh_from_db()
        self.assertEqual(self.first.column_id, self.source.id)

    def test_cross_board_move_rejected(self):
        other = create_board(self.user, "Other").columns.first()
        self.assertEqual(self.move(self.first, other).status_code, 400)
        self.assertEqual(other.cards.count(), 0)

    def test_reorder(self):
        self.assertEqual(self.move(self.second, self.source).status_code, 200)
        self.assertEqual(list(self.source.cards.values_list("title", flat=True)), ["Second", "First"])
