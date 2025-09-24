from django.db import models
from django.utils.translation import gettext_lazy as _


class Tag(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Название"),
        help_text=_("Пример: Новости, ПДД")
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name=_("Slug"),
        help_text=_("Автозаполняется. Используется в URL")
    )

    class Meta:
        verbose_name = _("Тег")
        verbose_name_plural = _("Теги")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Tag id={self.id} name='{self.name}'>"
