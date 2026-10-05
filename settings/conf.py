from pathlib import Path

from decouple import Config, Csv, RepositoryEnv

SETTINGS_DIR: Path = Path(__file__).resolve().parent
ENV_FILE: Path = SETTINGS_DIR / ".env"

ENV_LOCAL: str = "local"
ENV_PROD: str = "prod"
ENV_CHOICES: tuple[str, ...] = (ENV_LOCAL, ENV_PROD)

_config = Config(RepositoryEnv(str(ENV_FILE)))

BLOG_ENV_ID: str = _config("BLOG_ENV_ID", default=ENV_LOCAL)
if BLOG_ENV_ID not in ENV_CHOICES:
    raise ValueError(f"BLOG_ENV_ID must be one of {ENV_CHOICES}, got {BLOG_ENV_ID!r}")

SETTINGS_MODULE: str = f"settings.env.{BLOG_ENV_ID}"

BLOG_SECRET_KEY: str = _config("BLOG_SECRET_KEY")
BLOG_ALLOWED_HOSTS: list[str] = _config(
    "BLOG_ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv()
)

# PostgreSQL (used by settings.env.prod)
BLOG_DB_NAME: str = _config("BLOG_DB_NAME", default="")
BLOG_DB_USER: str = _config("BLOG_DB_USER", default="")
BLOG_DB_PASSWORD: str = _config("BLOG_DB_PASSWORD", default="")
BLOG_DB_HOST: str = _config("BLOG_DB_HOST", default="localhost")
BLOG_DB_PORT: int = _config("BLOG_DB_PORT", default=5432, cast=int)
