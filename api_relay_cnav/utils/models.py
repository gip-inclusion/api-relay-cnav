import uuid

from django.db import models


class UUIDModel(models.Model):
    id = models.UUIDField(default=uuid.uuid7, primary_key=True, editable=False)

    class Meta:
        abstract = True


class TimedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
