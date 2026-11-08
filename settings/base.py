import os
from collections.abc import Callable

from django.http import HttpRequest
from django.urls import reverse_lazy
from django.utils.http import urlencode

from settings.conf import *  # noqa


# ----------------------------------------------
# Path
#
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_URLCONF = "settings.urls"
WSGI_APPLICATION = "settings.wsgi.application"
ASGI_APPLICATION = "settings.asgi.application"
AUTH_USER_MODEL = "auths.User"

# ----------------------------------------------
# Apps
#
UNFOLD_APPS = [
    "unfold",  # before django.contrib.admin
    "unfold.contrib.filters",  # optional, if special filters are needed
    "unfold.contrib.forms",  # optional, if special form elements are needed
]

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
]

PROJECT_APPS = [
    "apps.auths.apps.AuthsConfig",
    "apps.blog.apps.BlogConfig",
]
INSTALLED_APPS = UNFOLD_APPS + DJANGO_APPS + THIRD_PARTY_APPS + PROJECT_APPS

# ----------------------------------------------
# Middleware | Templates | Validators
#
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# ----------------------------------------------
# Internationalization
#
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Almaty"
USE_I18N = True
USE_TZ = True

# ----------------------------------------------
# Static | Media
#
STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ----------------------------------------------
# Unfold admin
#
GITHUB_REPO_URL = "https://github.com/ioiiiomio/blog-api"
UNFOLD_DOCS_URL = "https://unfoldadmin.com/docs/"
POST_CHANGELIST_URL = reverse_lazy("admin:blog_post_changelist")
POST_STATUS_PARAM = "status__exact"
# same values as Post.Status (models cannot be imported in settings)
POST_STATUS_PUBLISHED = "published"
POST_STATUS_DRAFT = "draft"

# Tailwind "pink" palette: https://tailwindcss.com/docs/colors
PRIMARY_COLORS = {
    "50": "oklch(97.1% 0.014 343.198)",
    "100": "oklch(94.8% 0.028 342.258)",
    "200": "oklch(89.9% 0.061 343.231)",
    "300": "oklch(82.3% 0.12 346.018)",
    "400": "oklch(71.8% 0.202 349.761)",
    "500": "oklch(65.6% 0.241 354.308)",
    "600": "oklch(59.2% 0.249 0.584)",
    "700": "oklch(52.5% 0.223 3.958)",
    "800": "oklch(45.9% 0.187 3.815)",
    "900": "oklch(40.8% 0.153 2.432)",
    "950": "oklch(28.4% 0.109 3.907)",
}


def post_list_link(status: str | None = None) -> Callable[[HttpRequest], str]:
    # link to the post list filtered by status
    # reverse_lazy(...) + "?..." crashes on startup, so the url is built later, per request
    def link(request: HttpRequest) -> str:
        if status is None:
            return str(POST_CHANGELIST_URL)
        return f"{POST_CHANGELIST_URL}?{urlencode({POST_STATUS_PARAM: status})}"

    return link


def is_post_list_without_status(request: HttpRequest) -> bool:
    # "All" tab is active only when no status filter is applied
    return POST_STATUS_PARAM not in request.GET


UNFOLD = {
    "SITE_TITLE": "Blog API",
    "SITE_HEADER": "Blog API",
    "SITE_SUBHEADER": "Content administration",
    "SITE_SYMBOL": "article",
    "COLORS": {
        "primary": PRIMARY_COLORS,
    },
    "ENVIRONMENT": "apps.blog.callbacks.environment_callback",
    "DASHBOARD_CALLBACK": "apps.blog.callbacks.dashboard_callback",
    "SITE_DROPDOWN": [
        {"icon": "code", "title": "GitHub repository", "link": GITHUB_REPO_URL},
        {"icon": "menu_book", "title": "Unfold docs", "link": UNFOLD_DOCS_URL},
    ],
    "COMMAND": {
        "search_models": True,
        "show_history": True,
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Overview",
                "items": [
                    {
                        "title": "Dashboard",
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": "Content",
                "separator": True,
                "items": [
                    {
                        "title": "Posts",
                        "icon": "article",
                        "link": POST_CHANGELIST_URL,
                        "badge": "apps.blog.callbacks.drafts_badge",
                    },
                    {
                        "title": "Comments",
                        "icon": "chat",
                        "link": reverse_lazy("admin:blog_comment_changelist"),
                    },
                    {
                        "title": "Categories",
                        "icon": "category",
                        "link": reverse_lazy("admin:blog_category_changelist"),
                    },
                    {
                        "title": "Tags",
                        "icon": "sell",
                        "link": reverse_lazy("admin:blog_tag_changelist"),
                    },
                ],
            },
            {
                "title": "Users & Access",
                "separator": True,
                "items": [
                    {
                        "title": "Users",
                        "icon": "person",
                        "link": reverse_lazy("admin:auths_user_changelist"),
                        "permission": "apps.blog.callbacks.is_superuser",
                    },
                    {
                        "title": "Groups",
                        "icon": "group",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                        "permission": "apps.blog.callbacks.is_superuser",
                    },
                ],
            },
        ],
    },
    "TABS": [
        {
            "models": ["blog.post"],
            "items": [
                {
                    "title": "All",
                    "link": post_list_link(),
                    "active": is_post_list_without_status,
                },
                {
                    "title": "Published",
                    "link": post_list_link(POST_STATUS_PUBLISHED),
                },
                {
                    "title": "Drafts",
                    "link": post_list_link(POST_STATUS_DRAFT),
                },
            ],
        },
    ],
}
