from django.urls import path

from .views import DashboardView, SourceStatusView

app_name = "wind"
urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("status/", SourceStatusView.as_view(), name="status"),
]
