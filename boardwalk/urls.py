from django.urls import include, path
from boards import api, views

urlpatterns = [path("api/cards/<int:card_id>/move/", api.card_move),
               path("api/boards/<int:board_id>/members/", api.member_set),
               path("api/columns/<int:column_id>/cards/", api.card_create),
               path("", views.boards, name="boards"),
               path("boards/<int:board_id>/", views.board, name="board"), path("health/", views.health), path("accounts/", include("django.contrib.auth.urls"))]
