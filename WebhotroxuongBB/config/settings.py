"""Django settings for Webtoolhotroxuongbb.

Các giá trị nhạy cảm (SECRET_KEY, mật khẩu DB, host…) được nạp từ biến môi
trường thông qua file ``.env`` ở thư mục gốc repo (xem ``.env.example``).
"""

from __future__ import annotations

import os
from pathlib import Path

# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent

# ----------------------------------------------------------------------
# .env loader tối giản (không phụ thuộc package ngoài)
# ----------------------------------------------------------------------
def _load_env_file() -> None:
    for path in (REPO_ROOT / ".env", BASE_DIR / ".env"):
        if not path.exists():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


_load_env_file()


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on", "y"}


def _env_list(name: str, default: str = "") -> list[str]:
    raw = _env(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# ----------------------------------------------------------------------
# Core Django settings
# ----------------------------------------------------------------------
SECRET_KEY = _env("DJANGO_SECRET_KEY", "django-insecure-local-dev-only-change-me")
DEBUG = _env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = _env_list("DJANGO_ALLOWED_HOSTS", "*") or ["*"]
CSRF_TRUSTED_ORIGINS = _env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "webhotroxuongBB",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "webhotroxuongBB" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# ----------------------------------------------------------------------
# Databases
# ----------------------------------------------------------------------
USE_SQLITE_FALLBACK = _env_bool("USE_SQLITE_FALLBACK", False)

MSSQL_USER = _env("MSSQL_USER", "kendakv2")
MSSQL_PASSWORD = _env("MSSQL_PASSWORD", "kenda123")
MSSQL_PORT = _env("MSSQL_PORT", "1433")
MSSQL_DRIVER = _env("MSSQL_DRIVER", "ODBC Driver 18 for SQL Server")
MSSQL_EXTRA = _env("MSSQL_EXTRA_PARAMS", "Encrypt=no;TrustServerCertificate=yes;")

PG_USER = _env("PG_USER", "postgres")
PG_PASSWORD = _env("PG_PASSWORD", "kenda")
PG_PORT = _env("PG_PORT", "5432")
PG_DB = _env("PG_DB", "kverp")
PG_SCHEMA = _env("PG_SCHEMA", "kvmes")


def _mssql(host: str, name: str, *, timeout: int | None = 2) -> dict:
    options = {
        "driver": MSSQL_DRIVER,
        "extra_params": MSSQL_EXTRA,
    }
    if timeout is not None:
        options["connection_timeout"] = timeout
    return {
        "ENGINE": "mssql",
        "NAME": name,
        "USER": MSSQL_USER,
        "PASSWORD": MSSQL_PASSWORD,
        "HOST": host,
        "PORT": MSSQL_PORT,
        "OPTIONS": options,
    }


def _pg(host: str) -> dict:
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": PG_DB,
        "USER": PG_USER,
        "PASSWORD": PG_PASSWORD,
        "HOST": host,
        "PORT": PG_PORT,
        "OPTIONS": {"options": f"-c search_path={PG_SCHEMA}"},
    }


_erp_host = _env("MSSQL_ERP_HOST", "198.1.10.33")
_erp_db = _env("MSSQL_ERP_DB", "erp")
_bb_host = _env("MSSQL_BB_HOST", "198.1.10.33")
_bb_db = _env("MSSQL_BB_DB", "BB")
_mfns_db = _env("MSSQL_BB_MFNS_DB", "mfns")
_mfns_share_db = _env("MSSQL_BB_MFNSSHARE_DB", "mfnsShareDB")

_default_bb_hosts = {
    "BB1": "198.1.8.21",
    "BB2": "198.1.8.22",
    "BB3": "198.1.8.23",
    "BB4": "198.1.8.24",
    "BB5": "198.1.8.35",
    "BB6": "198.1.8.36",
    "BB7": "198.1.8.37",
    "BB8": "198.1.8.38",
}
_bb_hosts = {
    key: _env(f"MSSQL_{key}_HOST", default)
    for key, default in _default_bb_hosts.items()
}

if USE_SQLITE_FALLBACK:
    def _sqlite_cfg(alias: str) -> dict:
        # Mỗi alias 1 file test riêng để Django test runner không
        # cố gắng xoá trùng cùng một file (gây FileNotFoundError khi teardown).
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(BASE_DIR / "db.sqlite3"),
            "TEST": {"NAME": str(BASE_DIR / f"test_{alias}.sqlite3")},
        }

    DATABASES = {"default": _sqlite_cfg("default"), "33BB": _sqlite_cfg("33BB")}
    for key in _default_bb_hosts:
        DATABASES[key] = _sqlite_cfg(key)
        DATABASES[f"{key}_mfnsshare"] = _sqlite_cfg(f"{key}_mfnsshare")
    DATABASES["KV2KD"] = _sqlite_cfg("KV2KD")
    DATABASES["KV1KD"] = _sqlite_cfg("KV1KD")
else:
    DATABASES = {
        "default": _mssql(_erp_host, _erp_db, timeout=None),
        "33BB": _mssql(_bb_host, _bb_db),
    }
    for key, host in _bb_hosts.items():
        DATABASES[key] = _mssql(host, _mfns_db)
        DATABASES[f"{key}_mfnsshare"] = _mssql(host, _mfns_share_db)
    DATABASES["KV2KD"] = _pg(_env("PG_KV2KD_HOST", "198.1.10.85"))
    DATABASES["KV1KD"] = _pg(_env("PG_KV1KD_HOST", "198.1.1.92"))


# ----------------------------------------------------------------------
# Auth
# ----------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ----------------------------------------------------------------------
# i18n / l10n
# ----------------------------------------------------------------------
LANGUAGE_CODE = "vi"
TIME_ZONE = "Asia/Ho_Chi_Minh"
USE_I18N = True
USE_TZ = True


# ----------------------------------------------------------------------
# Static files
# ----------------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "webhotroxuongBB" / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "[{asctime}] {levelname} {name}: {message}", "style": "{"}
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "webhotroxuongBB": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
