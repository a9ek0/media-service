# Media Service

Севрис для управления медиа-контентом с использованием Django и Django REST Framework.

## Возможности

* CRUD для постов, категорий, тегов
* Редактор текста через EditorJS
* Загрузка и хранение медиафайлов
* Swagger документация
* Тесты через pytest

## Технологии

* Django, Django REST Framework
* PostgreSQL
* EditorJS (через django-editorjs2)
* Swagger (drf-spectacular)
* pytest

## Установка

1. Клонировать репозиторий:

   ```bash
   git clone https://github.com/a9ek0/media-service.git
   cd media-service
   ```

2. Создать виртуальное окружение:

   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. Установить зависимости:

   ```bash
   pip install -r requirements.txt
   ```

4. Настроить `.env` файл:

   ```env
   SECRET_KEY=секретный-ключ
   DEBUG=True
   POSTGRES_DB=media_service
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=пароль
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   ```

5. Выполнить миграции и создать суперпользователя:

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. Запустить сервер:

   ```bash
   python manage.py runserver
   ```

## API

* Swagger UI: `http://localhost:8000/api/schema/swagger-ui/`
* Эндпоинты: `/api/posts/`, `/api/categories/`, `/api/tags/`, `/api/media/`

## Тесты

```bash
pytest
```

