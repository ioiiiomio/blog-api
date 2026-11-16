# Blog API — Homework 4

Topic: **REST API**. Your blog gets an API: a mobile app or a frontend can register, log in, read posts and write comments.

Four parts:

1. **Users and JWT.** Register, log in, get tokens, see and change your own profile.
2. **Blog endpoints.** Categories, tags, posts and comments, with serializers and permissions.
3. **Redis.** Cache the lists of categories and tags.
4. **Celery.** Send an email to the author of a post when someone comments on it.

Read everything before you start. Parts 1 and 2 use what we did in the lecture. Pagination, nested serializers, Redis and Celery go further than the lecture. Every step tells you what to look up.

## Git

1. Make sure `hw3` is merged into `main`.
2. Create a branch `hw4` **from `main`** and do all your work there.
3. When done, **merge** `hw4` into `main` (do **not** delete the branch).

## Dependencies

| File                    | Add                                                                            |
|-------------------------|--------------------------------------------------------------------------------|
| `requirements/base.txt` | `djangorestframework`, `djangorestframework-simplejwt`, `redis`, `celery[redis]` |

Write `celery[redis]`, not just `celery`. The `[redis]` part installs what Celery needs to work with Redis. Without it the worker fails with an import error.

---

## API Rules

These rules apply to every endpoint in this homework.

- URLs start with `/api/auths/v1/` or `/api/blog/v1/` and have no `/` at the end.
- Use `ViewSet` and a router, like in the lecture. Write the methods (`list`, `retrieve`, …) yourself. Don't use `ModelViewSet` or `GenericViewSet`: they do this work for you, and the goal is to see how it works.
- The client sends the token in the header `Authorization: Bearer <access token>`.
- `DEFAULT_PERMISSION_CLASSES` is `IsAuthenticated`. Endpoints for everyone set their own permission classes. Then an endpoint that you forget about is closed, not open to everyone.
- Status codes:

| Code  | When                                                    |
|-------|---------------------------------------------------------|
| `200` | read or changed                                         |
| `201` | created                                                 |
| `204` | deleted                                                 |
| `400` | wrong data (the serializer's errors)                    |
| `401` | no token, or a bad or old token                         |
| `403` | logged in, but not allowed                              |
| `404` | not found. Also another user's draft (see Part 2)       |

No endpoint may answer `500`. For example, `/api/blog/v1/posts/abc` → `400` or `404`.

---

## Part 1 — Users and JWT

| Method  | URL                              | Who       | What it does                                                        |
|---------|----------------------------------|-----------|---------------------------------------------------------------------|
| `POST`  | `/api/auths/v1/users/register`   | everyone  | Creates a user. Answer: `id`, `email`, `first_name`, `last_name`    |
| `POST`  | `/api/auths/v1/users/login`      | everyone  | Email + password → the user's data in the body, the tokens in the headers |
| `POST`  | `/api/auths/v1/token/refresh`    | everyone  | The refresh token in the body → a new access token in the header    |
| `GET`   | `/api/auths/v1/users/me`         | logged in | Your profile                                                        |
| `PATCH` | `/api/auths/v1/users/me`         | logged in | Changes your `first_name` and `last_name`                           |

The tokens come in the **response headers**, not in the body. Login answer:

```
HTTP 200 OK
X-Access-Token: eyJhbGciOiJIUzI1NiIs...
X-Refresh-Token: eyJhbGciOiJIUzI1NiIs...

{
    "id": 7,
    "email": "emily.johnson@example.com",
    "first_name": "Emily",
    "last_name": "Johnson"
}
```

**Do:**

- Set up Simple JWT. The access token lives **15 minutes**, the refresh token **1 day**. Both are constants.
- `register`, `login` and `me` are `@action`s of one `UserViewSet`.
- **Tokens in headers:**
  - Login puts the access token into the header `X-Access-Token` and the refresh token into `X-Refresh-Token`. The body has only the user's data.
  - `token/refresh`: the client sends `{"refresh": "..."}` in the body. The new access token comes in the header `X-Access-Token`, the body has no tokens.
  - The header names are constants.
- **Register:**
  - `password` goes **in**, but never comes **out**.
  - The email is saved in lower case. `Emily@Example.com` and `emily@example.com` are the same email: the second registration → `400`.
  - The password is checked with the validators from `AUTH_PASSWORD_VALIDATORS` in `base.py`. `"12345678"` → `400` with their messages.
  - The user is created with `create_user()` of your manager: one `INSERT`, the password is hashed.
- **Login:**
  - The email works in any case: `EMILY@example.com` is OK.
  - A wrong email, a wrong password, an inactive user → `400` with **one** message: `"Invalid email or password."`. The answer must not show if the email exists.
- **Me:** `PATCH` changes only `first_name` and `last_name`. If the client sends `email`, it is ignored.

**Look up:** `write_only` and `extra_kwargs`, `read_only_fields`, [`validate_password()`](https://docs.djangoproject.com/en/5.2/topics/auth/passwords/#integrating-validation), [Saving instances](https://www.django-rest-framework.org/api-guide/serializers/#saving-instances), `RefreshToken.for_user()`, the `headers` argument of DRF's [`Response`](https://www.django-rest-framework.org/api-guide/responses/), `TokenRefreshView`, `partial=True`.

**Good to know:**

- Log in as the users from your `seed`: their password is `SEED_PASSWORD`.
- `ModelSerializer` checks that the email is unique **before** `validate_email()` runs. So it checks the email as the client sent it. `Emily@Example.com` passes the check, then you make it lower case, and the `INSERT` fails with `IntegrityError` → `500`. Check that the email is unique yourself, after `.lower()`.
- Without your own `create()`, `save()` calls `User.objects.create()`. It saves the password as plain text, and nobody can log in.
- `validate_password()` raises Django's `ValidationError`, not DRF's. Inside `validate_<field>()` DRF turns it into a normal `400` answer.
- `check_password()` returns `True` for an inactive user too. Check `is_active` yourself.
- The ready `TokenRefreshView` of Simple JWT returns the new token in the body. Make your own class that extends it: call the parent `post()`, take the token out of `response.data` and put it into the header.
- The response headers only **give** the tokens to the client. In every request the client still sends the access token in `Authorization: Bearer <access token>`.
- In Postman the tokens are in the **Headers** tab of the answer, not in **Body**. To send one: the **Authorization** tab → *Bearer Token* → paste the access token. After 15 minutes it stops working (`401`). Get a new one from `token/refresh`.

---

## Part 2 — Blog Endpoints

| Method   | URL                                    | Who                  | What it does                                                    |
|----------|----------------------------------------|----------------------|-----------------------------------------------------------------|
| `GET`    | `/api/blog/v1/categories`              | everyone             | All categories, A → Z                                           |
| `GET`    | `/api/blog/v1/tags`                    | everyone             | All tags, A → Z                                                 |
| `GET`    | `/api/blog/v1/posts`                   | everyone             | Published posts, newest first, 10 per page. `?category=<slug>`: only this category |
| `POST`   | `/api/blog/v1/posts`                   | logged in            | Creates a post. The author is the current user                  |
| `GET`    | `/api/blog/v1/posts/<id>`              | everyone             | One post. A draft: only for its author                          |
| `PATCH`  | `/api/blog/v1/posts/<id>`              | the author           | Changes the post                                                |
| `DELETE` | `/api/blog/v1/posts/<id>`              | the author or staff  | Deletes the post                                                |
| `GET`    | `/api/blog/v1/posts/<id>/comments`     | everyone             | Comments of a published post, oldest first                      |
| `POST`   | `/api/blog/v1/posts/<id>/comments`     | logged in            | Adds a comment to a published post                              |

Go in this order, from easy to hard:

1. Categories and tags
2. Reading posts
3. Writing posts
4. Comments

### 1. Categories and Tags

**Do:** two ViewSets with only `list()`. Fields: `id`, `name`, `slug`.

**Good to know:**

- The router makes URLs only for the methods that exist. With only `list()` there is no `/categories/<id>`: it answers `404`.

### 2. Reading Posts

List answer:

```json
{
    "count": 70,
    "next": "http://127.0.0.1:8000/api/blog/v1/posts?page=2",
    "previous": null,
    "results": [
        {
            "id": 25,
            "title": "Why Django signals are tricky",
            "slug": "why-django-signals-are-tricky",
            "author": {"id": 3, "first_name": "Emily", "last_name": "Johnson"},
            "category": {"id": 2, "name": "Django", "slug": "django"},
            "tags": [{"id": 5, "name": "ORM", "slug": "orm"}],
            "comments_count": 4,
            "created_at": "2026-05-14T09:31:00Z"
        }
    ]
}
```

One post: the same fields + `body` and `updated_at`.

**Do:**

- **List:**
  - Only published posts, newest first.
  - 10 posts per page (a constant). `?page=2` gives the next page.
  - `?category=django` → only the posts of this category. A slug that doesn't exist → an empty list, not an error.
  - `author`, `category` and `tags` are objects, like in the example, not ids. A post without a category has `"category": null`.
  - `comments_count` is counted by the database.
  - No N+1.
- **One post:**
  - A published post: for everyone.
  - A draft: only for its author. For everyone else it doesn't exist: `404`.

**Look up:** [nested serializers](https://www.django-rest-framework.org/api-guide/relations/#nested-relationships), [`PageNumberPagination`](https://www.django-rest-framework.org/api-guide/pagination/#pagenumberpagination) (`paginate_queryset()`, `get_paginated_response()`), `request.query_params`, `select_related()`, `prefetch_related()`, `annotate()` + `Count` and `Q` (Homework 3).

**Good to know:**

- A plain `ViewSet` doesn't paginate by itself. Create the paginator in `list()`. `paginate_queryset(queryset, request, view=self)` gives one page, and `get_paginated_response(data)` adds `count`, `next` and `previous`.
- Pagination needs a sorted QuerySet. Without `order_by()` Django shows a warning, and the same post can be on two pages.
- A value from `annotate()` is not a model field. Declare it in the serializer yourself: `comments_count = IntegerField(read_only=True)`.
- For a user without a token, `request.user` is an `AnonymousUser`. `filter(author=request.user)` with it fails with `TypeError` → `500`. Check `request.user.is_authenticated` first.
- How to check N+1: turn on SQL logging (Homework 2) and count the queries of one request. Change the page size from 10 to 2: the number of queries must stay the same.

### 3. Writing Posts

Request body for `POST` (for `PATCH`, any of these fields):

```json
{
    "title": "My first API post",
    "body": "Text of the post.",
    "category": 2,
    "tags": [1, 5],
    "status": "draft"
}
```

**Do:**

- **Create:**
  - The author is `request.user`. The client can't choose another author.
  - The slug is made from the title and is unique, with the same rule as in `seed`: `my-post`, `my-post-2`. The client doesn't send it.
  - The answer is `201` with the post in the format of "one post" (objects, not ids).
- **Change** (`PATCH`): only the author. The slug doesn't change.
- **Delete:** the author or a staff user. The answer is `204`.
- Another user's post: `PATCH` → `403`, `DELETE` → `403` (if they are not staff). Another user's **draft** → `404`, like in "one post".
- Wrong data → `400`: an empty title, a category or tag id that doesn't exist, a status that is not `draft` or `published`.

**Look up:** [Passing additional attributes to `.save()`](https://www.django-rest-framework.org/api-guide/serializers/#passing-additional-attributes-to-save), [custom permissions](https://www.django-rest-framework.org/api-guide/permissions/#custom-permissions), `has_object_permission()`, `SAFE_METHODS`.

**Good to know:**

- `ModelSerializer` checks `category`, `tags` and `status` by itself: an id that doesn't exist or a wrong status → `400`. You don't need to write these checks.
- The client sends ids, but gets objects back. So you need one serializer for the input and another one for the answer.
- Write your permission class in `apps/blog/permissions.py`.
- A plain `ViewSet` doesn't call `has_object_permission()` by itself. Call `self.check_object_permissions(request, post)` after you find the post (lecture, §11). Without it your permission class does nothing.

### 4. Comments

A comment:

```json
{
    "id": 81,
    "author": {"id": 7, "first_name": "Emily", "last_name": "Johnson"},
    "body": "Great post!",
    "created_at": "2026-11-20T10:15:02Z"
}
```

**Do:**

- Both endpoints are **one** `@action` of the posts ViewSet: `detail=True`, `url_path="comments"`, two methods.
- `GET`: all comments of the post, oldest first. No N+1.
- `POST`: the client sends only `body`. The author is `request.user`. The answer is `201` with the comment.
- Only published posts have comments. A draft → `404` for both methods.
- An empty `body` → `400`.

**Look up:** `@action` (`methods`, `detail`, `url_path`), `request.method`.

**Good to know:**

- Any logged-in user may comment on any published post. If you call `check_object_permissions()` with the post here, only its author can comment.
- One `@action` with two methods: check `request.method` to know what to do.

---

## Part 3 — Redis

**Redis** is a database that keeps data in memory. It is very fast, so it is often used as a **cache**: a place to keep answers that take time to make and don't change often. In this homework Redis does two jobs: the cache (this part) and the queue for Celery (Part 4).

### 1. Run Redis

**Do:** start Redis on your computer. `redis-cli ping` must answer `PONG`.

| Your system         | How                                                        |
|---------------------|------------------------------------------------------------|
| Docker (any system) | `docker run -d --name blog-redis -p 6379:6379 redis:7`     |
| macOS               | `brew install redis`, then `brew services start redis`     |
| Windows             | Docker, or Redis inside WSL                                |

Add `BLOG_REDIS_URL=redis://localhost:6379/0` to `settings/.env` and read it in `conf.py`.

**Good to know:**

- Redis is a server, like a database. `pip install redis` installs only the Python library that talks to it.
- With Docker, `redis-cli` is inside the container: `docker exec -it blog-redis redis-cli ping`.

### 2. Cache Categories and Tags

**Do:**

- Set `CACHES` to Django's built-in Redis backend. The address is `BLOG_REDIS_URL`.
- In `list()` of categories and tags, look in the cache first:
  - the data is there → answer with it. No SQL queries;
  - the data is not there → read it from the database, put it into the cache, answer.
- The cache time (10 minutes) and the key names are constants.

**Look up:** [Redis in the Django cache docs](https://docs.djangoproject.com/en/5.2/topics/cache/#redis), [the low-level cache API](https://docs.djangoproject.com/en/5.2/topics/cache/#the-low-level-cache-api) (`cache.get()`, `cache.set()`).

**Good to know:**

- Put `serializer.data` into the cache (a list of dicts), not a QuerySet.
- How to check:
  - SQL logging: the first request makes 1 query, the second one makes 0.
  - `redis-cli KEYS "*"` shows your keys. Django adds a prefix: the key `categories` is saved as `:1:categories`.
  - `redis-cli TTL ":1:categories"` shows how many seconds are left.
- Add a category in the admin: the API shows it only when the cache time is over. This is normal for a cache. To see it at once, delete the key: `redis-cli DEL ":1:categories"`.
- If Redis is not running, these endpoints answer `500`. Start Redis first.

---

## Part 4 — Celery

**Celery** runs tasks **in the background**, in a separate process called a **worker**. The view puts a task into a queue and answers at once. The worker takes the task from the queue and does it. This is good for slow work, like sending emails. Our queue is in Redis. Celery calls the queue a **broker**.

```
POST /posts/5/comments
   │
   ▼
view: save the comment → send_new_comment_email.delay(comment.id) → 201 at once
                                 │
                                 ▼
                         Redis (the queue)
                                 │
                                 ▼
               worker: send the email to the author of the post
```

### 1. Setup

**Do:**

- `settings/celery.py` creates the Celery app. `settings/__init__.py` imports it.
- Celery reads its settings from Django settings with the prefix `CELERY_`. `CELERY_BROKER_URL` is your `BLOG_REDIS_URL`.
- Emails are **only printed** to the terminal, not sent: the console email backend in `local.py`. Don't connect a real email service (SMTP) and don't put a real email or email password anywhere. The sender `DEFAULT_FROM_EMAIL` is a fake address, e.g. `noreply@blog.local`.
- Start the worker in a second terminal: `celery -A settings worker --loglevel=info`. At the start it shows your task in the `[tasks]` list.

**Look up:** [First steps with Django](https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html) in the Celery docs, `autodiscover_tasks()`, [the console email backend](https://docs.djangoproject.com/en/5.2/topics/email/#console-backend).

**Good to know:**

- You record a video of your work. A real password on the screen can be stolen. So use only fake emails (like the ones from `seed`, or `...@example.com`), and don't open `settings/.env` on the video.
- In the Celery docs the project package is called `proj`. Ours is `settings`, so the file is `settings/celery.py` and the command is `-A settings`.
- `celery.py` must choose `DJANGO_SETTINGS_MODULE` the same way as `manage.py`: from `BLOG_ENV_ID`. Otherwise the worker can run with other settings than `runserver`.
- `autodiscover_tasks()` finds `tasks.py` in every app from `INSTALLED_APPS`.
- On Windows add `--pool=solo` to the worker command.
- The worker doesn't reload your code like `runserver` does. After you change `tasks.py`, stop it with `Ctrl+C` and start it again.

### 2. Email About a New Comment

**Do:**

- A task `send_new_comment_email(comment_id: int) -> None` in `apps/blog/tasks.py`. It sends one email to the author of the post:
  - subject: `New comment on "<post title>"`;
  - text: the first and last name of the comment's author, and the comment.
- The comment endpoint saves the comment and calls the task with `.delay()`. The `201` answer doesn't wait for the email.
- A comment on your own post → no email.

**Look up:** `@shared_task`, `.delay()`, [`send_mail()`](https://docs.djangoproject.com/en/5.2/topics/email/#send-mail).

**Good to know:**

- Pass the **id**, not the object: `.delay(comment.id)`. Task arguments go to Redis as JSON. `.delay(comment)` fails with `EncodeError: Object of type Comment is not JSON serializable`.
- The task loads the comment from the database by its id. Load the post and its author in the same query.
- The email appears in the **worker** terminal, not in the `runserver` terminal.
- If the worker is not running, the tasks wait in Redis. When you start the worker, it does them.

---

## Code Standards

Same as Homework 1: PEP 8 + linter, constants, import order, naming, type hints. Also:

- Status codes are DRF constants (`HTTP_201_CREATED`), not numbers.
- No repeated code in the views. "Find the post or answer `404`" and "check the data or answer `400`" are written once: in a mixin or a decorator, like in the lecture.
- Page size, cache time, cache keys and token lifetimes are constants.

## Submission

Update `README.md`:

- **API** — the table of endpoints and how to get a token.
- **Redis and Celery** — how to start Redis and the worker.

Export your Postman collection with all endpoints to `docs/blog-api.postman_collection.json`.

With Redis running, on an empty database this must work:

```
python manage.py migrate
python manage.py seed
python manage.py runserver
celery -A settings worker --loglevel=info    # in a second terminal
```
