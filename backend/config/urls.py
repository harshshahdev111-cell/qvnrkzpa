from common.api import APINotFoundView
from django.urls import include, path, re_path
from wind.views import index

urlpatterns = [
    path("api/v1/", include("wind.api.v1.urls", namespace="wind-v1")),
    # Preserve existing clients while exposing a versioned contract for new clients.
    path("api/", include("wind.api.v1.urls", namespace="wind-legacy")),
    re_path(r"^api(?:/.*)?$", APINotFoundView.as_view(), name="api-not-found"),
    path("", index, name="index"),
]
