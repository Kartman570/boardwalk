from django.contrib.auth import get_user_model
from django.test import TestCase
from .models import Membership
from .services import create_board


class WorkflowTests(TestCase):
    def test_editor_flow_and_access_revocation(self):
        users = get_user_model().objects
        owner = users.create_user("owner")
        editor = users.create_user("editor")
        board = create_board(owner, "Workshop")
        Membership.objects.create(board=board, user=editor, role="editor")
        first, second = list(board.columns.all())[:2]
        self.client.force_login(editor)
        created = self.client.post("/api/columns/%s/cards/" % first.id,
                                   {"title": "Cut wood"}, content_type="application/json")
        card_id = created.json()["id"]
        moved = self.client.post("/api/cards/%s/move/" % card_id,
                                 {"column_id": second.id, "position": 0, "revision": 0},
                                 content_type="application/json")
        self.assertEqual(moved.status_code, 200)
        self.assertEqual(second.cards.get().title, "Cut wood")
        revision = moved.json()["revision"]
        archived = self.client.post("/api/cards/%s/" % card_id,
                                    {"archived": True, "revision": revision},
                                    content_type="application/json")
        self.assertEqual(archived.status_code, 200)
        self.client.force_login(owner)
        self.client.post("/api/boards/%s/members/" % board.id,
                         {"username": "editor", "role": "remove"}, content_type="application/json")
        self.client.force_login(editor)
        self.assertEqual(self.client.get("/api/boards/%s/cards/" % board.id).status_code, 404)

    def test_restore_obeys_column_limit(self):
        from .services import add_card
        user = get_user_model().objects.create_user("owner")
        board = create_board(user, "Small")
        column = board.columns.first()
        old = add_card(column, "Old")
        old.archived = True
        old.save()
        add_card(column, "Active")
        column.limit = 1
        column.save()
        self.client.force_login(user)
        response = self.client.post("/api/cards/%s/" % old.id,
                                    {"archived": False, "revision": 0},
                                    content_type="application/json")
        self.assertEqual(response.status_code, 400)
        old.refresh_from_db()
        self.assertTrue(old.archived)
