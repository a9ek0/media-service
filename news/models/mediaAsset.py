from django.db import models
from django.utils.translation import gettext_lazy as _


class MediaAsset(models.Model):
    file = models.FileField(
        upload_to="uploads/%Y/%m/%d/",
        verbose_name=_("Файл"),
        help_text=_("Изображение")
    )
    alt = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Описание (alt)"),
        help_text=_("Текст для атрибута alt")
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Дата загрузки")
    )
    original_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Оригинальное имя файла"),
        help_text=_("Имя файла при загрузке")
    )

    class Meta:
        verbose_name = _("Медиафайл")
        verbose_name_plural = _("Медиафайлы")
        ordering = ["-uploaded_at"]
        indexes = [models.Index(fields=['uploaded_at'])]

    def __str__(self):
        return self.original_name or str(self.file)

    def __repr__(self):
        return f"<MediaAsset id={self.id} file='{self.file.name}'>"
