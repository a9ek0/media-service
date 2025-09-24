from django.db import models
from django_editorjs2.fields import EditorJSField
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from . import Category, Tag, MediaAsset


class Post(models.Model):
    STATUS_CHOICES = [
        ("draft", _("Черновик")),
        ("published", _("Опубликован")),
    ]

    title = models.CharField(
        max_length=200,
        verbose_name=_("Заголовок"),
        help_text=_("Краткий заголовок статьи, до 200 символов")
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name=_("Slug"),
        help_text=_("Автозаполняется. Используется в URL")
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="posts",
        verbose_name=_("Категория")
    )
    excerpt = models.TextField(
        blank=True,
        verbose_name=_("Краткое описание"),
        help_text=_("Появится в списке постов")
    )
    body = models.TextField(
        blank=True,
        verbose_name=_("Текст (plain)"),
    )
    body_json = EditorJSField(
        blank=True,
        default=dict,
        verbose_name=_("Текст (JSON)")
    )
    cover = models.ForeignKey(
        MediaAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
        verbose_name=_("Обложка")
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
        verbose_name=_("Статус")
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name=_("Закрепить на главной"),
        help_text=_("Пост будет постоянно отображаться в верхней части главной страницы")
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
    views = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Просмотры")
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="posts",
        verbose_name=_("Теги")
    )

    class Meta:
        verbose_name = _("Пост")
        verbose_name_plural = _("Посты")
        ordering = ["-published_at", "-updated_at"]
        indexes = [
            models.Index(fields=['published_at']),
            models.Index(fields=['status']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['is_featured', 'status']),
            models.Index(fields=['-published_at', 'status']),
        ]

    def save(self, *args, **kwargs):
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        elif self.status == 'draft':
            self.published_at = None
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def __repr__(self):
        return f"<Post id={self.id} title='{self.title}' status={self.status}>"
