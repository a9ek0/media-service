from django.db import models


class BaseModel(models.Model):
    """Базовая модель предметной области."""

    class Meta:
        abstract = True
