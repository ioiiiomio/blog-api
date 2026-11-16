# Blog API — Homework 3

Topic: **Django ORM**. You will write **50 queries** to the database of your blog. They start easy and get harder step by step.

Three parts:

1. **Realistic dates.** Make the seed command spread posts and comments over one year.
2. **The `queries` command.** It runs your queries and shows the result and the number of SQL queries.
3. **50 queries.** These are the main part of the homework.

Read everything before you start. Some topics here go further than the lecture. Every level tells you what to look up.

## Git

1. Make sure `hw2` is merged into `main`.
2. Create a branch `hw3` **from `main`** and do all your work there.
3. When done, **merge** `hw3` into `main` (do **not** delete the branch).

## Dependencies

No new packages.

## Data

All 50 queries run on the data from your `seed` command (Homework 2). Without data you can't check them, and neither can we. If your `seed` is not finished yet, finish it first.

The queries need the same kinds of data that Homework 2 asked for:

| Data                                  | Used in        |
|---------------------------------------|----------------|
| Published posts and drafts            | most queries   |
| Posts without a category              | 10, 23, 28, 45 |
| Posts without tags                    | 19, 23         |
| Inactive users                        | 5, 44          |
| Staff users                           | 5, 49          |
| Comments (only on published posts)    | 17, 25, 30, 36, 48, 49 |

Before you start, fill the database:

```
python manage.py seed --clear
```

---

## Part 1 — Realistic Dates

Right now the seed command creates every post and comment with the same date: the moment you ran it. Queries like "posts of the last 30 days" or "posts per month" are useless on such data.

**Do:** change `seed` so that:

- every post has a random `created_at` in the last 365 days;
- about **30%** of posts have `updated_at` 1–30 days after `created_at`, but not later than now. The other posts have `updated_at` **equal** to `created_at`;
- every comment has a random `created_at` between its post's `created_at` and now.

All numbers (365, 30%, 1–30 days) are constants. The rules from Homework 2 still apply: `bulk_create`, no `.save()` in a loop, and running `seed` twice must not crash.

**Look up:** [`bulk_update`](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#bulk-update), `timedelta`, `random.randint`, `random.random`.

**Good to know:**

- `auto_now_add` and `auto_now` set the date themselves in `save()` and in `bulk_create`. They **overwrite** any value you put there. `bulk_update` and `update()` do not call `save()`, so they keep your value. So the order is: `bulk_create` → set the dates on the objects → one `bulk_update`.
- After `bulk_create`, `updated_at` is a few microseconds later than `created_at` for **every** post. Django reads the clock separately for each field. That is why you must set `updated_at = created_at` yourself.
- You still have the post objects in memory from `bulk_create`. Read `comment.post.created_at` from them. Don't load posts from the database again.
- How to check: query **26** must return nothing. Query **24** must return about 30% of the posts.

---

## Part 2 — The `queries` Command

- **Queries:** `apps/blog/queries.py`. One function for each query.
- **Command:** `apps/blog/management/commands/queries.py`.

| Run                                       | What it does                                         |
|-------------------------------------------|------------------------------------------------------|
| `python manage.py queries`                | Runs all queries except 40–44 (they change the data) |
| `python manage.py queries --number 31`    | Runs only query 31. This works for 40–44 too         |
| `python manage.py queries --number 6 --sql` | Also prints the SQL that Django sent to the database |

Example:

```
$ python manage.py queries --number 31
#31 categories_with_post_count — 1 SQL query
  Python {'post_count': 16}
  Databases {'post_count': 13}
  Frontend {'post_count': 13}
  Career {'post_count': 12}
  Django {'post_count': 11}
  (8 rows)

$ python manage.py queries --number 6 --sql
#6 has_drafts — 1 SQL query
SELECT 1 AS "a" FROM "blog_post" WHERE "blog_post"."status" = 'draft' LIMIT 1
  True
```

**Do:**

- At the bottom of `queries.py`, add a dict `QUERIES` that maps a number to a function: `{1: categories_by_name, 2: published_posts, ...}`.
- For every query, print:
  - the number and the function name;
  - how many SQL queries it made;
  - the result. For a list or a QuerySet, print the first 5 rows (a constant) and the total number of rows. For model objects, also print the values you added with `annotate` (see Level 7).
- Some functions take arguments (`slug`, `email`, `days`, …). The command passes sample values. Keep them in one dict next to the command: `{number: {argument: value}}`. Choose values that give a non-empty result. Slugs can be constants from your seed lists. An email must come from the database, for example the email of a user who has posts.
- A number that does not exist → `CommandError`.

**Look up:** `CaptureQueriesContext` from `django.test.utils`, `connection` from `django.db`, `queryset.query.annotations`.

```python
with CaptureQueriesContext(connection) as context:
    result = function(**arguments)
    ...  # make the QuerySet run here, inside the "with" block

len(context.captured_queries)     # how many SQL queries ran
context.captured_queries[0]["sql"]  # the SQL text of the first one
```

**Good to know:**

- A **QuerySet** is a query that has not run yet. It is **lazy**: Django sends the SQL only when you use the rows (loop over them, call `list()`, `len()`, print them). If a function returns a QuerySet, call `list(result)` **inside** the `with` block, otherwise you count 0 queries.
- `CaptureQueriesContext` is a tool for tests, but it works in a command too.

---

## Part 3 — 50 Queries

### Before you start

- Try every query in the shell first: `python manage.py shell`. In Django 5.2 the shell imports all your models automatically ([docs](https://docs.djangoproject.com/en/5.2/ref/django-admin/#shell)).
- `print(queryset.query)` shows the SQL of a QuerySet. Read it. This is the fastest way to understand what the ORM does.

### Rules

These apply to all 50 queries:

- Use the function names and signatures from the tables.
- The **database** does the work: filtering, sorting, counting. No Python loops or `if` over the rows. The only exception is Level 10, where you build lines of text from rows that are already loaded.
- No raw SQL (`raw()`, `cursor()`).
- If the table says `QuerySet`, return a QuerySet. Don't turn it into a list.
- Every read query (1–39 and 48–50) makes **exactly 1** SQL query. Level 10 has its own limits.
- Use your `TextChoices` for statuses (`Post.Status.PUBLISHED`), not the string `"published"`.
- An empty result is OK if your data has no such rows. To check that the query works, add a matching row in the admin.

Each level starts with a short explanation. Then come the tasks, what to look up, and the traps.

### Level 1 — First Queries

`filter()` keeps the rows that match. `exclude()` removes them. `order_by("name")` sorts A → Z, and `order_by("-name")` sorts Z → A. Slicing `[a:b]` becomes `LIMIT` / `OFFSET` in SQL. Every one of these returns a new QuerySet, so you can add more: `published_posts()[:5]`.

| #   | Function                                             | Task                                                                                   |
|-----|------------------------------------------------------|----------------------------------------------------------------------------------------|
| 1   | `categories_by_name() -> QuerySet[Category]`         | All categories, sorted by name A → Z.                                                  |
| 2   | `published_posts() -> QuerySet[Post]`                | Published posts, newest first.                                                         |
| 3   | `newest_published_posts() -> QuerySet[Post]`        | The 5 newest published posts.                                                          |
| 4   | `post_by_slug(slug: str) -> Post \| None`            | The post with this slug, or `None` if there is no such post. No exceptions.            |
| 5   | `active_users_count() -> int`                        | Number of active users. Staff users are not counted.                                   |
| 6   | `has_drafts() -> bool`                               | `True` if there is at least one draft post.                                            |
| 7   | `published_posts_page(page: int) -> QuerySet[Post]`  | One page of published posts, newest first. 10 posts per page: page 1 is posts 1–10, page 2 is posts 11–20. |

**Look up:** [Retrieving objects](https://docs.djangoproject.com/en/5.2/topics/db/queries/#retrieving-objects), [Limiting QuerySets](https://docs.djangoproject.com/en/5.2/topics/db/queries/#limiting-querysets), `first()`, `count()`, `exists()`.

**Good to know:**

- `get()` raises `DoesNotExist` when there is no row, and `MultipleObjectsReturned` when there is more than one. For #4 there is a simpler method that returns `None`.
- `count()` and `exists()` ask the database. `len(queryset)` loads all the rows into Python just to count them.
- Negative indexes (`queryset[-1]`) are not supported.

### Level 2 — Field Lookups

A **lookup** is the part after a double underscore. `title__icontains="django"` means "the title contains `django`, letter case does not matter". All lookups: [Field lookups](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#field-lookups).

| #   | Function                                                     | Task                                                                                     |
|-----|--------------------------------------------------------------|------------------------------------------------------------------------------------------|
| 8   | `posts_with_word_in_title(word: str) -> QuerySet[Post]`      | Posts whose title contains `word`. Letter case does not matter.                          |
| 9   | `users_with_email_domain(domain: str) -> QuerySet[User]`     | Users whose email ends with `@` + `domain`, for example `domain="example.com"`.          |
| 10  | `posts_without_category() -> QuerySet[Post]`                 | Posts that have no category.                                                             |
| 11  | `categories_by_slugs(slugs: list[str]) -> QuerySet[Category]`| Categories whose slug is in the list `slugs`.                                            |
| 12  | `posts_in_month(year: int, month: int) -> QuerySet[Post]`    | Posts created in this month of this year.                                                |
| 13  | `posts_last_days(days: int) -> QuerySet[Post]`               | Posts created in the last `days` days.                                                   |
| 14  | `posts_between(start: date, end: date) -> QuerySet[Post]`    | Posts created from `start` to `end`. Posts from the `start` day and from the `end` day are both included. |

**Look up:** `icontains`, `iendswith`, `isnull`, `in`, `year`, `month`, `date`, `gte`, `range`; `timezone.now()` from `django.utils`.

**Good to know:**

- `i` at the start of a lookup means "ignore letter case": `contains` vs `icontains`, `exact` vs `iexact`.
- Use `timezone.now()`, not `datetime.now()`. With `USE_TZ = True` Django keeps time in UTC. It warns you about a **naive** datetime (a datetime without a time zone).
- #14 has a trap. `created_at__range=(start, end)` turns `end` into midnight at the **start** of that day. Posts written later on the `end` day are lost. Lookups can be chained: `created_at__date` takes only the date part of a datetime, and you can put one more lookup after it.

### Level 3 — Queries Across Relations

Double underscores also follow relations. `author__email` goes from a post to its author and reads the email. Django adds a **JOIN** (an SQL command that connects two tables) for you. It works backwards too: from a user to their posts with `post__...`.

| #   | Function                                                                     | Task                                                                   |
|-----|------------------------------------------------------------------------------|------------------------------------------------------------------------|
| 15  | `author_published_posts(email: str) -> QuerySet[Post]`                      | Published posts of the author with this email. Letter case of the email does not matter. |
| 16  | `posts_with_tag(tag_slug: str) -> QuerySet[Post]`                           | Posts that have the tag with this slug.                                |
| 17  | `comments_in_category(category_slug: str) -> QuerySet[Comment]`             | Comments on posts of the category with this slug.                      |
| 18  | `users_with_published_posts() -> QuerySet[User]`                            | Users who have at least one published post. Every user appears once.   |
| 19  | `posts_without_tags() -> QuerySet[Post]`                                    | Posts that have no tags.                                               |
| 20  | `users_without_comments() -> QuerySet[User]`                                | Users who have never written a comment.                                |
| 21  | `posts_with_both_tags(first_slug: str, second_slug: str) -> QuerySet[Post]` | Posts that have **both** tags. A post with only one of them is not included. |

**Look up:** [Lookups that span relationships](https://docs.djangoproject.com/en/5.2/topics/db/queries/#lookups-that-span-relationships), [Spanning multi-valued relationships](https://docs.djangoproject.com/en/5.2/topics/db/queries/#spanning-multi-valued-relationships), `distinct()`, `iexact`.

**Good to know:**

- From the "other" side of a relation, use the model name in lower case (`post`, `comment`). If you set `related_name` in Homework 1, use that name instead.
- A JOIN to the "many" side (a reverse `ForeignKey` or a `ManyToManyField`) repeats a row once for every match. In #18, a user with 7 published posts comes back 7 times. Compare `.count()` with and without your fix.
- #21 has a trap. `tags__slug__in=[...]` means "one tag **or** the other". Read "Spanning multi-valued relationships": conditions in one `filter()` call and in two `filter()` calls work differently.

### Level 4 — Q and F

All conditions inside one `filter()` are joined with AND. A **`Q` object** holds one condition, and you can join `Q` objects with `|` (OR), `&` (AND) and `~` (NOT). An **`F` object** points to a field of the same row. With it you compare one field with another field, not with a fixed value.

| #   | Function                                             | Task                                                                               |
|-----|------------------------------------------------------|------------------------------------------------------------------------------------|
| 22  | `search_posts(text: str) -> QuerySet[Post]`          | Posts that have `text` in the title **or** in the body. Letter case does not matter. |
| 23  | `published_posts_missing_info() -> QuerySet[Post]`   | Published posts that have no category **or** no tags. Every post appears once.     |
| 24  | `edited_posts() -> QuerySet[Post]`                   | Posts that were edited more than 1 hour after they were created.                   |
| 25  | `comments_by_post_author() -> QuerySet[Comment]`     | Comments that the author of the post wrote under their own post.                   |
| 26  | `comments_before_post() -> QuerySet[Comment]`        | Comments created **before** their post. Must be empty if Part 1 is correct.        |

**Look up:** [Complex lookups with Q objects](https://docs.djangoproject.com/en/5.2/topics/db/queries/#complex-lookups-with-q-objects), [Filters can reference fields on the model](https://docs.djangoproject.com/en/5.2/topics/db/queries/#filters-can-reference-fields-on-the-model).

**Good to know:**

- `F` works across relations (`F("post__created_at")`) and with math (`F("created_at") + timedelta(...)`).
- "1 hour" in #24 is a constant.
- #23 goes through a `ManyToManyField` again. Check for repeated rows.

### Level 5 — values and values_list

By default a QuerySet gives model objects with all their columns. `values()` gives dicts and `values_list()` gives tuples, with only the columns you ask for. Use them when you need data, not objects.

| #   | Function                                                | Task                                                                                         |
|-----|---------------------------------------------------------|----------------------------------------------------------------------------------------------|
| 27  | `published_authors_emails() -> list[str]`               | Emails of authors who have published posts. Unique, sorted A → Z. A plain list of strings.   |
| 28  | `published_posts_overview() -> list[dict[str, Any]]`    | One dict for each published post with exactly three keys: `title`, `author_email`, `category_name`. If a post has no category, `category_name` is `"Uncategorized"`. |

**Look up:** [`values()`](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#values), [`values_list()`](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#values-list) (`flat=True`), [`distinct()`](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#distinct), [`Coalesce`](https://docs.djangoproject.com/en/5.2/ref/models/database-functions/#coalesce), `Value`.

**Good to know:**

- `values()` also takes keyword arguments with expressions (`F(...)`, functions). This is how you give a column your own key name.
- `Coalesce(a, b)` returns the first of its arguments that is not `NULL`. A fixed text inside it is wrapped in `Value(...)`.
- `distinct()` together with `order_by()`: sort only by the columns you select. Otherwise the repeated rows come back. The `distinct()` docs explain why.

### Level 6 — aggregate

`aggregate()` calculates something over the whole QuerySet and returns **one dict**, for example `{"total": 100}`. The functions are `Count`, `Sum`, `Avg`, `Min`, `Max`.

| #   | Function                                  | Task                                                                                                    |
|-----|-------------------------------------------|---------------------------------------------------------------------------------------------------------|
| 29  | `posts_stats() -> dict[str, Any]`         | In **one** SQL query: the number of all posts, of published posts and of drafts, and the date of the first and of the last post. Keys: `total`, `published`, `drafts`, `first_post_at`, `last_post_at`. |
| 30  | `average_comments_per_post() -> float`    | The average number of comments on a published post, rounded to 2 digits after the point. Posts with 0 comments count too. If there are no posts, return `0.0`. |

**Look up:** [Aggregation](https://docs.djangoproject.com/en/5.2/topics/db/aggregation/), the `filter` argument of `Count`, the [`default`](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#default) argument of aggregate functions, [Aggregating annotations](https://docs.djangoproject.com/en/5.2/topics/db/aggregation/#aggregating-annotations).

**Good to know:**

- One `aggregate()` call can calculate many values. It is still one SQL query.
- `Count(..., filter=Q(...))` counts only the rows that match.
- When there are no rows, `Avg`, `Min` and `Max` return `None`.
- #30 has two steps: first count the comments of each post, then take the average of those numbers. Both steps run in the database. The first step uses `annotate()` from Level 7. Read its intro first.

### Level 7 — annotate

`annotate()` adds a calculated value to **every** row. `User.objects.annotate(comment_count=Count("comment"))` gives every user a new attribute `user.comment_count`. In SQL this is `GROUP BY` (put the rows into groups and calculate one value for each group). You can filter and sort by the new value.

| #   | Function                                                | Task                                                                                     |
|-----|---------------------------------------------------------|------------------------------------------------------------------------------------------|
| 31  | `categories_with_post_count() -> QuerySet[Category]`    | Every category with `post_count`. Most posts first. Same count → sort by name.           |
| 32  | `categories_with_published_count() -> QuerySet[Category]` | Every category with `published_count`, the number of its published posts. Categories with 0 published posts must be in the result too. |
| 33  | `top_authors() -> QuerySet[User]`                       | The top 5 users by number of published posts, with `published_count`.                   |
| 34  | `popular_tags(min_posts: int) -> QuerySet[Tag]`         | Tags used in at least `min_posts` posts, with `post_count`.                              |
| 35  | `posts_per_status() -> list[dict[str, Any]]`            | The number of posts for each status: `[{"status": "draft", "count": 30}, {"status": "published", "count": 70}]`. |
| 36  | `users_activity() -> QuerySet[User]`                    | Every user with `post_count` and `comment_count`. Both numbers must be correct.         |

**Look up:** [`annotate()`](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#annotate), [Filtering on annotations](https://docs.djangoproject.com/en/5.2/topics/db/aggregation/#filtering-on-annotations), [Order of annotate() and filter()](https://docs.djangoproject.com/en/5.2/topics/db/aggregation/#order-of-annotate-and-filter-clauses), [values() and GROUP BY](https://docs.djangoproject.com/en/5.2/topics/db/aggregation/#values), [Combining multiple aggregations](https://docs.djangoproject.com/en/5.2/topics/db/aggregation/#combining-multiple-aggregations).

**Good to know:**

- The order of `filter()` and `annotate()` matters:
  - `filter()` **before** `annotate()` decides which rows are counted. Groups with 0 rows disappear.
  - `filter()` **after** `annotate()` filters by the counted value. In SQL this is `HAVING`.
- #32 has a trap: "filter first, then count" loses the categories with 0 published posts.
- #35: `values("status")` **before** `annotate()` makes groups by status.
- #36 has a trap. Two `Count`s over two different "many" relations multiply each other. A user with 4 posts and 26 comments gets 104 and 104. Read "Combining multiple aggregations".

### Level 8 — Database Functions and Conditions

**Database functions** run inside SQL: join strings, cut a date to the month, measure text length. `Case` / `When` is an if/else that the database runs for every row.

| #   | Function                                                    | Task                                                                                   |
|-----|-------------------------------------------------------------|----------------------------------------------------------------------------------------|
| 37  | `search_users_by_full_name(text: str) -> QuerySet[User]`    | Users whose full name ("First Last") contains `text`. Letter case does not matter. A search for `"john smi"` finds John Smith. Every user has `full_name`. |
| 38  | `published_posts_per_month() -> list[dict[str, Any]]`       | The number of published posts in each month: `[{"month": ..., "count": 7}, ...]`, oldest month first. |
| 39  | `posts_with_popularity() -> QuerySet[Post]`                 | Every post with `comment_count` and `popularity`: `"hot"` for 10 comments or more, `"normal"` for 3 or more, `"quiet"` for less. |

**Look up:** [Database functions](https://docs.djangoproject.com/en/5.2/ref/models/database-functions/) (`Concat`, `TruncMonth`), `Value`, [Conditional expressions](https://docs.djangoproject.com/en/5.2/ref/models/conditional-expressions/) (`Case`, `When`).

**Good to know:**

- #37 can't be solved with `Q`: `"john smi"` is not inside any single column. Build the full name in the database first, then filter by it.
- A fixed text inside an expression is wrapped in `Value(" ")`.
- `When` conditions are checked from top to bottom. The first one that matches wins.
- 10 and 3 in #39 are constants.

### Level 9 — Changing Data

The ORM also changes data. `update()` and `delete()` on a QuerySet change many rows with **one** SQL query and tell you how many rows changed.

> ⚠️ These functions change your data. The command runs them only with `--number`. To get fresh data, run `python manage.py seed --clear`.

| #   | Function                                                          | Task                                                                                        |
|-----|-------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| 40  | `get_or_create_tag(name: str) -> tuple[Tag, bool]`               | Return the tag with this name. Create it (slug from the name) if it does not exist. The `bool` is `True` if the tag was created. Calling it twice must not create a second tag. |
| 41  | `publish_old_drafts(days: int) -> int`                           | All drafts older than `days` days become published, with **one** SQL query. Return how many posts changed. |
| 42  | `tag_category_posts(category_slug: str, tag_slug: str) -> int`   | Add the tag to every post of the category. A post that already has this tag must not get it twice. Return the number of posts in the category. |
| 43  | `merge_categories(source_slug: str, target_slug: str) -> int`    | Move all posts of the source category to the target category, then delete the source category. Return how many posts moved. |
| 44  | `delete_inactive_users_comments() -> int`                        | Delete all comments written by inactive users. Return how many were deleted.                |

No `.save()` in a loop in this level.

**Look up:** [`get_or_create()`](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#get-or-create) (`defaults`), [`update()`](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#update), [`delete()`](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#delete), [`add()` on related managers](https://docs.djangoproject.com/en/5.2/ref/models/relations/#django.db.models.fields.related.RelatedManager.add).

**Good to know:**

- `update()` does not call `save()`, so `auto_now` does not work and `updated_at` stays old. In #41, set it yourself.
- `get_or_create()` searches by the arguments you pass. It uses `defaults` only when it creates a new row. Think about which field to search by: `"Django ORM"` and `"django orm"` give the same slug, and the slug is unique.
- `delete()` returns a tuple: the total number of deleted rows and a dict with a number for each model.
- #43: `category` has `on_delete=SET_NULL`. If you delete the source category first, its posts lose their category.

### Level 10 — select_related and prefetch_related

A reminder from Homework 2: the **N+1 problem** is 1 query for a list + 1 more query for **every** row that reads a related object. 50 posts → 51 queries.

- `select_related()` is for a `ForeignKey` (one related object). Django adds a JOIN to the same query.
- `prefetch_related()` is for a `ManyToManyField` or a reverse `ForeignKey` (many related objects). Django makes one extra query for all rows and connects the results in Python.

In this level the function itself reads the related objects, so the command counts all the queries.

| #   | Function                                                       | Task                                                                                    |
|-----|----------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| 45  | `published_feed() -> list[str]`                                | The 50 newest published posts as lines `"title \| author email \| category name"` (`Uncategorized` if there is no category). **Exactly 1** SQL query. |
| 46  | `newest_posts_with_tags() -> list[str]`                        | The 20 newest posts as lines `"title: tag1, tag2"`. **At most 2** SQL queries.          |
| 47  | `categories_with_published_posts() -> dict[str, list[str]]`    | `{category name: [titles of its published posts, newest first]}` for every category. No drafts. **At most 2** SQL queries. |

**Look up:** [`select_related()`](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-related), [`prefetch_related()`](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#prefetch-related), [`Prefetch`](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#prefetch-objects) (`queryset`, `to_attr`).

**Good to know:**

- In this level you may build the lines in Python, but all the data must already be loaded.
- After `prefetch_related("tags")`, `post.tags.all()` and `post.tags.count()` use the loaded data. But `post.tags.filter(...)` and `post.tags.order_by(...)` send a **new** query for every post.
- So in #47 you can't take all posts and filter them later. Filter **inside** the prefetch: a `Prefetch` object can have its own `queryset`.
- Change 50 to 10 in #45: the number of SQL queries must stay the same.

### Level 11 — Subquery and Exists

A **subquery** is a query inside another query. `OuterRef("pk")` means "the id of the current row of the outer query".

- `Subquery` puts one value from the inner query into every row of the outer query.
- `Exists` checks that the inner query finds at least one row.

| #   | Function                                                  | Task                                                                                      |
|-----|-----------------------------------------------------------|-------------------------------------------------------------------------------------------|
| 48  | `posts_with_last_comment() -> QuerySet[Post]`             | Published posts. Each has `last_comment`: the body of its newest comment (`None` if there are no comments). |
| 49  | `posts_with_staff_comments() -> QuerySet[Post]`           | Posts with at least one comment from a staff user. Use `Exists`, not `distinct()`.        |
| 50  | `users_with_draft_as_latest_post() -> QuerySet[User]`     | Users whose **newest** post is a draft. Each user has `latest_post_status`.               |

**Look up:** [Subquery expressions](https://docs.djangoproject.com/en/5.2/ref/models/expressions/#subquery-expressions) (`Subquery`, `OuterRef`, `Exists`).

**Good to know:**

- A `Subquery` must return one column and one row: use `.values("field")` and `[:1]`.
- `Max("comment__created_at")` gives the date of the newest comment, but not its text. That is why #48 needs a subquery.
- You can pass `Exists(...)` straight into `filter()`.
- #50: first find the status of each user's newest post with a subquery, then filter by it.
- Each of these is still **1** SQL query. Look at it with `--sql`.

---

## Code Standards

Same as Homework 1: PEP 8 + linter, constants, import order, naming, type hints. Also:

- Every function in `queries.py` has type hints and a short docstring.
- No magic numbers or strings in queries: page size, "5 newest", "1 hour", the popularity limits, `"Uncategorized"` are constants.
- No `print` in the command. Use `self.stdout.write`.

## Submission

Update `README.md`:

- **Queries** — how to run the command (`queries`, `--number`, `--sql`) and an example of its output.

On an empty database this must work:

```
python manage.py migrate
python manage.py seed
python manage.py queries
python manage.py queries --number 41
```
