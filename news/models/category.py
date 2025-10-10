from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel

__all__ = ["Category"]


class Category(BaseModel):
    """Категория для статьи/видео"""

    class CategoryType(models.TextChoices):
        VIDEO = "V", _("Видео")
        ARTICLE = "A", _("Статья")

    type = models.CharField(
        choices=CategoryType.choices,
        default=CategoryType.ARTICLE,
        verbose_name=_("Тип категории"),
        help_text=_("Для совместимости с API v2"),
    )
    name = models.CharField(verbose_name=_("Название"), help_text=_("Пример: Новости, Технологии"))
    slug = models.SlugField(unique=True, verbose_name=_("Slug"), help_text=_("Автозаполняется. Используется в URL."))
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Родительская категория"),
        help_text=_("Оставьте пустым для корневой категории"),
    )

    class Meta:
        verbose_name = _("Категория")
        verbose_name_plural = _("Категории")
        ordering = ["name"]

    def __str__(self):
        return self.name
