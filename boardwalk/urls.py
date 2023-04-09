from django.urls import include, path
from boards import views

urlpatterns = [path("", views.boards, name="boards"),
               path("boards/<int:board_id>/", views.board, name="board"), path("health/", views.health), path("accounts/", include("django.contrib.auth.urls"))]
