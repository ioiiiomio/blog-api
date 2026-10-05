# Blog API — Homework 1

Build a blog REST API. Read everything before you start.

## Git

1. Create a **public** GitHub repository called `blog-api`.
2. Create a branch `hw1` and do all your work there.
3. When done, **merge** `hw1` into `main` (do **not** delete the branch).
4. Future homeworks will follow the same pattern: `hw2`, `hw3`, etc. — each merged into `main`, never deleted.

## Project Structure

Your project **must** follow this layout from day one.

- `manage.py`
- `.gitignore`
- `requirements/` — split dependencies
  - `base.txt` — shared dependencies
  - `dev.txt` — dev-only (starts with `-r base.txt`)
  - `prod.txt` — prod-only (starts with `-r base.txt`)
- `logs/` — log files (add to `.gitignore`)
- `apps/` — all Django apps
  - `auths/` — custom user model, JWT authentication
  - `blog/` — posts, comments, categories, tags
- `settings/` — project-level package
  - `.env` — secrets (never commit this)
  - `conf.py` — reads `.env` via `python-decouple`, exports config variables
  - `base.py` — shared settings, imports from `conf.py`
  - `urls.py` — root URL configuration
  - `wsgi.py`
  - `asgi.py`
  - `env/` — environment overrides
    - `local.py` — imports from `base.py`, sets `DEBUG=True`, SQLite, etc.
    - `prod.py` — imports from `base.py`, sets `DEBUG=False`, PostgreSQL, etc.

`settings/` is both the Django project package (`urls.py`, `wsgi.py`, `asgi.py`) and the configuration root. `manage.py` reads `BLOG_ENV_ID` from `settings/.env` to pick `settings.env.local` or `settings.env.prod` as `DJANGO_SETTINGS_MODULE`.

Load order: `manage.py` → `settings/env/local.py` → `settings/base.py` → `settings/conf.py` → `settings/.env`.

Prefix all env variables with `BLOG_` (e.g. `BLOG_SECRET_KEY`, `BLOG_REDIS_URL`) so they don't clash with other projects.

## Apps

All apps live inside `apps/`. After `startapp`, set `name = 'apps.auths'` (or `'apps.blog'`) in each `apps.py` and register them in `INSTALLED_APPS` with that full path.

- `apps.auths` — custom user model, JWT authentication
- `apps.blog` — posts, comments, categories, tags

---

## Code Standards

Follow these rules throughout the project:

- **PEP 8** — use a linter (`ruff` or `flake8`).
- **Constants** — no magic strings or numbers in code. Use constants.
- **Imports** — standard library + third party first, then django rest framework, then django, then local.
- **Naming** — `snake_case` for variables/functions, `PascalCase` for classes, `UPPER_CASE` for constants.
- **Type hints** — annotate function arguments and return types, e.g. `def get_posts_by_author(author_id: int) -> QuerySet[Post]`, `def create_user(email: str, password: str) -> User`.

---

## Models

Before writing any code, create an **ERD (Entity-Relationship Diagram)** of all models described below. Use any tool you like (dbdiagram.io, draw.io, Mermaid, etc.). Export it as an image, add it to the repository at `docs/erd.png` (or `.svg`), and embed it in your project's `README.md`.

### `auths` app — Custom User

Django's default `User` model uses `username` as the login field. We want **email** instead.

You need to:
1. Create a custom user model extending `AbstractBaseUser` + `PermissionsMixin`.
2. Create a custom manager (`BaseUserManager` subclass) with `create_user` and `create_superuser`.
3. Set `USERNAME_FIELD = 'email'`.
4. Set `AUTH_USER_MODEL = 'auths.User'` in `base.py` **before** your first migration. (The model label is `auths.User`, not `apps.auths.User` — Django uses the app label, which is the last segment of `name`.)

**Fields:**

- `email` — `EmailField(unique=True)`, primary login field
- `first_name` — `CharField(max_length=50)`, required
- `last_name` — `CharField(max_length=50)`, required
- `is_active` — `BooleanField`, default `True`
- `is_staff` — `BooleanField`, default `False`

The manager should normalize the email (lowercase) and handle password hashing.

### `blog` app

**Category:**

- `name` — `CharField(max_length=100)`, unique
- `slug` — `SlugField(unique=True)`, URL-friendly identifier

**Tag:**

- `name` — `CharField(max_length=50)`, unique
- `slug` — `SlugField(unique=True)`

**Post:**

- `author` — `ForeignKey(User)`, `on_delete=CASCADE`
- `title` — `CharField(max_length=200)`
- `slug` — `SlugField(unique=True)`
- `body` — `TextField`
- `category` — `ForeignKey(Category)`, `on_delete=SET_NULL`, null allowed
- `tags` — `ManyToManyField(Tag)`, blank allowed
- `status` — `CharField`, use `TextChoices`: `draft`, `published`
- `created_at` — `DateTimeField`, auto-set on creation
- `updated_at` — `DateTimeField`, auto-set on save

**Comment:**

- `post` — `ForeignKey(Post)`, `on_delete=CASCADE`
- `author` — `ForeignKey(User)`, `on_delete=CASCADE`
- `body` — `TextField`
- `created_at` — `DateTimeField`, auto-set on creation
