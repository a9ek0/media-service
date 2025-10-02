from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class BaseContentItem(models.Model):
    """Базовая модель для всего контента"""

    STATUS_CHOICES = [
        ("draft", _("Черновик")),
        ("published", _("Опубликован")),
    ]

    title = models.CharField(
        max_length=200,
        verbose_name=_("Заголовок"),
        help_text=_("Краткий заголовок, до 200 символов")
    )
    lead = models.TextField(
        blank=True,
        verbose_name=_("Лид/описание"),
        help_text=_("Описание контента")
    )

    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s",
        verbose_name=_("Категория")
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="%(class)s",
        verbose_name=_("Автор")
    )
    tags = models.ManyToManyField(
        'Tag',
        blank=True,
        related_name="%(class)s",
        verbose_name=_("Теги")
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
        verbose_name=_("Статус")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Дата создания")
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Дата публикации")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Обновлено")
    )

    title_picture = models.URLField(
        null=True,
        blank=True,
        verbose_name=_("Ссылка на обложку")
    )

    views = models.PositiveIntegerField(default=0, verbose_name=_("Просмотры"))

    class Meta:
        abstract = True
        ordering = ["-published_at", "-updated_at"]
        indexes = [
            models.Index(fields=['published_at']),
            models.Index(fields=['status']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['-published_at', 'status']),
            models.Index(fields=['category', 'status', '-published_at']),
        ]

    def save(self, *args, **kwargs):
        if self.status == 'draft' and self.published_at and self.published_at <= timezone.now():
            self.status = 'published'
        elif self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    @classmethod
    def publish_scheduled(cls):
        drafts_to_publish = cls.objects.filter(status='draft', published_at__lte=timezone.now())
        if drafts_to_publish.exists():
            drafts_to_publish.update(status='published')

    @property
    def is_published(self):
        return self.status == 'published'

    def __str__(self):
        return self.title
