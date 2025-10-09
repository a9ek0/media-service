from django.db import models
from django.utils.translation import gettext_lazy as _

__all__ = ["Tag"]


class Tag(models.Model):
    """Тег для статьи/видео"""

    name = models.CharField(unique=True, verbose_name=_("Название"), help_text=_("Пример: Новости, ПДД"))
    slug = models.SlugField(unique=True, verbose_name=_("Slug"), help_text=_("Автозаполняется. Используется в URL"))

    class Meta:
        verbose_name = _("Тег")
        verbose_name_plural = _("Теги")
        ordering = ["name"]

    def __str__(self):
        return self.name
