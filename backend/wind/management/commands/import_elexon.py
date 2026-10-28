from django.core.management.base import BaseCommand, CommandError
from integrations.elexon import ElexonClient

from wind.services.ingestion import ImportFailure, import_history


class Command(BaseCommand):
    help = "Import real Elexon January 2026 decision data. Safe to rerun."

    def handle(self, *args, **options):
        try:
            actuals, forecasts = import_history(
                ElexonClient(), report=self.stdout.write
            )
        except ImportFailure as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {actuals} actuals and {forecasts} forecast vintages."
            )
        )
