from django.urls import include, path
from boards import views

urlpatterns = [path("health/", views.health), path("accounts/", include("django.contrib.auth.urls"))]
