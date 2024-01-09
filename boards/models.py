from django.conf import settings
from django.db import models


class Board(models.Model):
    name = models.CharField(max_length=120)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class Column(models.Model):
    limit = models.PositiveIntegerField(default=0)
    board = models.ForeignKey(Board, related_name="columns", on_delete=models.CASCADE)
    name = models.CharField(max_length=80)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]


class Card(models.Model):
    labels = models.ManyToManyField("Label", blank=True, related_name="cards")
    revision = models.PositiveIntegerField(default=0)
    column = models.ForeignKey(Column, related_name="cards", on_delete=models.CASCADE)
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]


class Membership(models.Model):
    board = models.ForeignKey(Board, related_name="memberships", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=[("editor", "Editor"), ("viewer", "Viewer")])

    class Meta:
        constraints = [models.UniqueConstraint(fields=["board", "user"], name="unique_membership")]


class Comment(models.Model):
    card = models.ForeignKey(Card, related_name="comments", on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField()

    class Meta:
        ordering = ["id"]


class Activity(models.Model):
    board = models.ForeignKey(Board, related_name="activity", on_delete=models.CASCADE)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=80)
    detail = models.TextField(blank=True)

    class Meta:
        ordering = ["-id"]


class Label(models.Model):
    board = models.ForeignKey(Board, related_name="labels", on_delete=models.CASCADE)
    name = models.CharField(max_length=40)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["board", "name"], name="unique_board_label")]
