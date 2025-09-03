from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    slug = models.SlugField(max_length=100, verbose_name="Slug")
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="Родительская категория"
    )
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['slug', 'parent'],
                name='unique_slug_per_parent'
            )
        ]

    def __str__(self):
        return self.name

class MediaAsset(models.Model):
    file = models.FileField(upload_to="", verbose_name="Файл")
    alt = models.CharField(max_length=100, blank=True, verbose_name="Описание (alt)")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")
    original_name = models.CharField(max_length=100, blank=True, verbose_name="Оригинальное имя файла")

    class Meta:
        verbose_name = "Медиафайл"
        verbose_name_plural = "Медиафайлы"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.original_name or str(self.file)

class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")
    slug = models.SlugField(max_length=100, unique=True, db_index=True, verbose_name="Slug")

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ["name"]

    def __str__(self):
        return self.name

class Post(models.Model):
    STATUS_CHOICES = [
        ("draft", "Черновик"),
        ("published", "Опубликован"),
    ]

    title = models.CharField(max_length=200, verbose_name="Заголовок")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="Slug")
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Категория"
    )
    excerpt = models.TextField(blank=True, verbose_name="Краткое описание")
    body = models.TextField(verbose_name="Текст")
    cover = models.ForeignKey(
        MediaAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
        verbose_name="Обложка"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
        verbose_name="Статус"
    )
    is_featured = models.BooleanField(default=False, verbose_name="Закрепить на главной")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата публикации")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")
    views = models.PositiveIntegerField(default=0, verbose_name="Просмотры")
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts", verbose_name="Теги")

    class Meta:
        verbose_name = "Пост"
        verbose_name_plural = "Посты"
        ordering = ["-published_at", "-updated_at"]
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['published_at']),
        ]

    def __str__(self):
        return self.title
