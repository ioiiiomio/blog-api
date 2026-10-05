from decouple import Csv, config


ENV_ID = config("BLOG_ENV_ID", cast=str)
SECRET_KEY = config("BLOG_SECRET_KEY", cast=str)
ALLOWED_HOSTS = config("BLOG_ALLOWED_HOSTS", cast=Csv(), default="")

# Postgres (used only in prod)
DB_NAME = config("BLOG_DB_NAME", cast=str, default="")
DB_USER = config("BLOG_DB_USER", cast=str, default="")
DB_PASSWORD = config("BLOG_DB_PASSWORD", cast=str, default="")
DB_HOST = config("BLOG_DB_HOST", cast=str, default="localhost")
DB_PORT = config("BLOG_DB_PORT", cast=int, default=5432)
