from django.db import models


class RateLimitCounter(models.Model):
    pk = models.CompositePrimaryKey("limiter_key", "client_key", "bucket_key")

    limiter_key = models.TextField(verbose_name="Identifiant du limiteur")
    client_key = models.TextField(verbose_name="Clef concernée par la limitation")
    bucket_key = models.BigIntegerField(verbose_name="Identifiant du bucket")
    bucket_count = models.PositiveIntegerField(verbose_name="Compteur du bucket")

    cleanup_timestamp = models.DateTimeField(verbose_name="Date à partir de laquelle la ligne peut être nettoyée")

    def __str__(self) -> str:
        return f"RateLimitCounter(pk={self.pk})"
