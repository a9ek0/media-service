# Media Service

Сервис для управления новостями и видео-контентом с использованием Django и Django REST Framework.

## Возможности

* Единая лента новостей и видео
* Иерархические категории контента
* Публикация и планирование контента
* API v2 для мобильных приложений
* Автоматическое получение метаданных видео (YouTube, RuTube)
* Админ-панель на основе Django Unfold
* Swagger документация

## Технологии

* Django, Django REST Framework
* PostgreSQL (psycopg[c])
* Django Unfold (админ-панель)
* Swagger (drf-spectacular)
* Markdown для контента
* Django TestCase

## Быстрый старт

### Предварительные требования

* Python 3.10+
* PostgreSQL 13+
* uv (менеджер зависимостей)

### Установка и запуск

1. Клонировать репозиторий:
   ```bash
   git clone https://github.com/a9ek0/media-service
   cd media-service
   ```

2. Создать виртуальное окружение и установить зависимости:
   ```bash
   uv venv
   uv sync
   ```

3. Создать базу данных PostgreSQL и настроить переменные окружения:
   ```bash
   cp .env.example .env
   # Отредактировать .env - указать DATABASE_URL и другие настройки
   ```

4. Выполнить миграции:
   ```bash
   ./manage.py migrate
   ```

5. Создать суперпользователя:
   ```bash
   ./manage.py createsuperuser
   ```

6. Запустить сервер разработки:
   ```bash
   ./manage.py runserver
   ```

## API v2

### Эндпоинты

* `GET /news/feed` - Лента новостей и видео
* `POST /news/feed` - Лента с исключением элементов
* `GET /news/categories` - Дерево категорий
* `GET /news/{id}` - HTML представление контента

### Документация API

* Swagger UI: `http://localhost:8000/api/docs/`

## Тестирование

```bash
# Запуск всех тестов
./manage.py test

# Запуск тестов с покрытием
./manage.py test --verbosity=2
```

## Разработка

### Форматирование кода
```bash
black .
```

### Проверка типов
```bash
mypy .
```
