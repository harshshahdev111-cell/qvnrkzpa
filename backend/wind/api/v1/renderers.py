"""CSV representation of the same decision view used by the JSON API."""

import csv
import io

from rest_framework.renderers import BaseRenderer


class DecisionCSVRenderer(BaseRenderer):
    media_type = "text/csv"
    format = "csv"
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        stream = io.StringIO()
        if renderer_context and renderer_context["response"].status_code >= 400:
            writer = csv.writer(stream)
            writer.writerow(["error"])
            writer.writerow([data["message"]])
        else:
            writer = csv.DictWriter(
                stream,
                fieldnames=[
                    "start_time",
                    "forecast",
                    "actual",
                    "publish_time",
                    "error",
                ],
            )
            writer.writeheader()
            writer.writerows(data["data"]["rows"])
        return stream.getvalue().encode(self.charset)
