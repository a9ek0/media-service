from django.db import models
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    """Категория для статьи/видео"""

    CATEGORY_TYPES = [
        ('article', _('Статья')),
        ('video', _('Видео')),
    ]

    type = models.CharField(
        max_length=20,
        choices=CATEGORY_TYPES,
        default='article',
        verbose_name=_("Тип категории"),
        help_text=_("Для совместимости с API v2")
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_("Название"),
        help_text=_("Пример: Новости, Технологии")
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name=_("Slug"),
        help_text=_("Автозаполняется. Используется в URL.")
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("Родительская категория"),
        help_text = _("Оставьте пустым для корневой категории")
    )

    class Meta:
        verbose_name = _("Категория")
        verbose_name_plural = _("Категории")
        ordering = ['name']

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Category id={self.id} name='{self.name}'>"
