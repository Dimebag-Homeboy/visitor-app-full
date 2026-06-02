# Система регистрации посетителей

**Остановка приложения:** `docker compose down`  
**Полная очистка данных (удаление томов БД):** `docker compose down -v`

## Тестовые учётные записи (создаются автоматически при первом запуске)

| Роль           | Логин       | Пароль     |
|----------------|-------------|------------|
| Администратор  | `admin`     | `admin123` |
| Секретарь      | `secretary` | `secret123`|
| Охранник       | `guard`     | `guard123` |

---

Веб-приложение для учёта посетителей с ролевой моделью (администратор, секретарь, охрана).  
Построено на **FastAPI**, **PostgreSQL**, **Docker**, с JWT-аутентификацией, HttpOnly cookie, миграциями Alembic, тестами и адаптивным интерфейсом.

## Содержание

- [Технологии](#технологии)
- [Установка и запуск через Docker](#установка-и-запуск-через-docker)
- [Ручной запуск (без Docker)](#ручной-запуск-без-docker)
- [Тестирование](#тестирование)
- [Примеры запросов к API](#примеры-запросов-к-api)
- [Роли и права](#роли-и-права)
- [Документация API (Swagger)](#документация-api-swagger)
- [Структура проекта](#структура-проекта)
- [Устранение неполадок](#устранение-неполадок)

## Технологии

- **Backend**: FastAPI, SQLAlchemy, Alembic, Pydantic, JWT, bcrypt
- **Database**: PostgreSQL (в Docker) / SQLite (для тестов)
- **Frontend**: Vanilla JS, HTML5, CSS3 (адаптив, тёмная тема)
- **DevOps**: Docker, Docker Compose, GitHub Actions (CI)
- **Testing**: pytest, httpx

## Установка и запуск через Docker

**Требования:** Docker Desktop / Docker Engine, Git.

```bash
# 1. Клонировать репозиторий
git clone https://github.com/ваш-аккаунт/visitor-app.git
cd visitor-app

# 2. Создать файл .env на основе примера
cp .env.example .env

# 3. Сгенерировать SECRET_KEY (обязательно) и добавить в .env
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Скопируйте вывод и вставьте в .env как SECRET_KEY

# 4. Запустить контейнеры
docker compose up --build
#остановка: 
docker compose down
#Полная очистка данных (удаление томов БД): 
docker compose down -v
# Приложение будет доступно по адресу http://localhost:8000