from collections.abc import Iterable

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models


class InterOpsCall(models.Model):
    timestamp = models.DateTimeField(verbose_name="horodatage", auto_now_add=True)

    request_uid = models.UUIDField(
        verbose_name="Identifiant de la requête", help_text="Fourni par le client", db_index=True
    )

    request_content = models.JSONField(encoder=DjangoJSONEncoder)
    interops_request_content = models.TextField()
    interops_response_content = models.TextField()
    interops_response_status_code = models.PositiveSmallIntegerField(
        verbose_name="Code de statut HTTP de la réponse InterOps"
    )
    response_content = models.JSONField(encoder=DjangoJSONEncoder, null=True)

    class Meta:
        verbose_name = "appel à InterOps"
        verbose_name_plural = "appels à InterOps"

    def __str__(self) -> str:
        return f"InterOpsCall(pk={self.pk}, timestamp={self.timestamp})"

    def save(
        self,
        *,
        force_insert: bool = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
    ) -> None:
        if self.pk is not None:
            raise RuntimeError("This model is append-only, you cannot modify existing objects")
        return super().save(
            force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields
        )
