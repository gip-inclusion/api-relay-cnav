from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from itoutils.django.commands import LoggedCommandMixin
from psycopg import sql


class Command(LoggedCommandMixin, BaseCommand):
    help = (
        "Grant DML privileges on the public schema to the application role (DJANGO_DB_APP_ROLE). "
        "Run after the migrations by the job user, owner of the objects."
    )

    def handle(self, *args: object, **options: object) -> None:
        if not (role := settings.DB_APP_ROLE):
            self.logger.warning("DB_APP_ROLE is not set, skipping.")
            return

        with connection.cursor() as cursor:

            def execute(statement: str) -> None:
                # A role is an identifier: it cannot travel as a query parameter (which only carries values)
                cursor.execute(sql.SQL(statement).format(sql.Identifier(role)))

            # Catch up on the objects created by past migration runs:
            # The privileges defined in the infrastructure repository only cover the objects existing at apply time
            execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {}")
            execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {}")

            # Cover the objects the job user will create in future migration runs
            execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {}")
            execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO {}")
