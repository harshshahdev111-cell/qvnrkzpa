"""HTML entry point; API views live in wind.api.v1."""

from django.conf import settings
from django.http import FileResponse, HttpResponse


def index(request):
    path = settings.BASE_DIR / "public" / "index.html"
    if path.exists():
        return FileResponse(path.open("rb"), content_type="text/html")
    return HttpResponse(
        "Run the React frontend on http://localhost:5173 or build the Docker image."
    )
