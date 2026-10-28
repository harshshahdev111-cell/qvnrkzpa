"""Thin DRF views: validate, invoke the use case, serialize, respond."""

from common.api import StandardAPIView
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response

from wind.selectors import source_status
from wind.services.analysis import analyze

from .renderers import DecisionCSVRenderer
from .serializers import (
    DashboardSerializer,
    DecisionQuerySerializer,
    SourceStatusSerializer,
)


class DashboardView(StandardAPIView):
    success_message = "Decision dashboard retrieved successfully."

    renderer_classes = [JSONRenderer, BrowsableAPIRenderer, DecisionCSVRenderer]

    def get(self, request):
        query = DecisionQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data
        result = analyze(params["decision_date"], params["cutoff"])
        if params.get("export") == "csv":
            request.accepted_renderer = DecisionCSVRenderer()
            request.accepted_media_type = "text/csv"
        response = Response(DashboardSerializer(result).data)
        if request.accepted_renderer.format == "csv":
            response["Content-Disposition"] = (
                f'attachment; filename="wind-{params["decision_date"]}.csv"'
            )
        return response


class SourceStatusView(StandardAPIView):
    success_message = "Source status retrieved successfully."

    def get(self, request):
        return Response(SourceStatusSerializer(source_status()).data)
