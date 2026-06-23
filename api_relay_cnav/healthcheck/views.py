import logging

from django.contrib.auth.decorators import login_not_required
from django.db import connection, transaction
from django.http import HttpRequest, HttpResponse


logger = logging.getLogger(__name__)


@login_not_required
@transaction.non_atomic_requests()
def healthcheck(request: HttpRequest) -> HttpResponse:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
    except Exception:
        logger.exception("Could not query database")
        return HttpResponse(status=500, content=b"Error")
    return HttpResponse(status=200, content=b"OK")
