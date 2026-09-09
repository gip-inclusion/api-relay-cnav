from django.core.management.base import BaseCommand
from itoutils.django.commands import LoggedCommandMixin

from api_relay_cnav.rate_limit.limiter import cleanup_obsolete_buckets


class Command(LoggedCommandMixin, BaseCommand):
    help = "Remove obsolete bucket"

    def handle(self, *args: object, **options: object) -> None:
        cleanup_obsolete_buckets()
