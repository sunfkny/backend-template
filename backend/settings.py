"""
Django settings for backend project.

Generated by 'django-admin startproject' using Django 3.2.16.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

import inspect
import logging
import re
import sys
import typing as t
from pathlib import Path
from typing import Protocol
from urllib.parse import urljoin

import loguru
import redis
from corsheaders.defaults import default_headers as corsheaders_default_headers
from corsheaders.defaults import default_methods as corsheaders_default_methods

loguru.logger.remove()


BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_FILE_PATH = LOG_DIR / "run.log"
DIST_ROOT = BASE_DIR / "dist"
STATIC_ROOT = DIST_ROOT / "static"
MEDIA_ROOT = BASE_DIR / "media"

for path in [LOG_DIR, STATIC_ROOT, MEDIA_ROOT]:
    if not path.exists():
        path.mkdir(parents=True)

DOMAIN_NAME = ""
BASE_URL = f"http://{DOMAIN_NAME}"

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True
CORS_URLS_REGEX = re.compile(r"^.*?")
# CORS_URLS_REGEX = re.compile(r"^/api/.*?")
# CORS_ALLOWED_ORIGINS = []
# CORS_ALLOWED_ORIGIN_REGEXES = [
#     re.compile(pattern)
#     for pattern in (
#         r"^https?://localhost(:[0-9]{2,5})?$",
#         r"^https?://(127|192)(\.[0-9]{1,3}){3}(:[0-9]{2,5})?$",
#     )
# ]
CORS_ALLOW_METHODS = (*corsheaders_default_methods,)
CORS_ALLOW_HEADERS = (*corsheaders_default_headers,)

DB_PREFIX = "t"
REDIS_PREFIX = "r"


redis_conn = redis.Redis(
    host="127.0.0.1",
    port=6379,
    db=0,
    decode_responses=True,
)


def get_redis_connection():
    return redis_conn


CONSTANCE_REDIS_CONNECTION = {
    "host": "127.0.0.1",
    "port": 6379,
    "db": 0,
}
CONSTANCE_REDIS_PREFIX = f"{REDIS_PREFIX}:constance:"
CONSTANCE_CONFIG = {
    "THE_ANSWER": (42, "Answer to the Ultimate Question of Life, The Universe, and Everything"),
}


class ConstanceConfigProtocol(Protocol):
    """Constance config protocol."""

    THE_ANSWER: int


def get_constance_config() -> ConstanceConfigProtocol:
    from constance import config

    return t.cast(ConstanceConfigProtocol, config)


# https://github.com/Delgan/loguru#entirely-compatible-with-standard-logging
class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists.
        level: str | int
        try:
            level = loguru.logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        loguru.logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


loguru.logger.add(
    LOG_DIR / "run.log",
    level=logging.INFO,
    filter=lambda record: record["extra"].get("name") is None,
    backtrace=False,
    watch=True,
)


LOGURU_LOGGERS_CACHE: dict[str, "loguru.Logger"] = {}


def get_logger(name: str | None = None):
    if name is None:
        return loguru.logger
    if name in LOGURU_LOGGERS_CACHE:
        return LOGURU_LOGGERS_CACHE[name]

    bind_logger = loguru.logger.bind(name=name)
    bind_logger.add(
        LOG_DIR / f"{name}.log",
        level=logging.INFO,
        filter=lambda record: record["extra"].get("name") == name,
        backtrace=False,
        watch=True,
    )

    LOGURU_LOGGERS_CACHE[name] = bind_logger
    return bind_logger


def redirect_default_logger(name: str, keep_default: bool):
    if not keep_default:
        loguru.logger.remove()

    loguru.logger.add(
        LOG_DIR / f"{name}.log",
        backtrace=False,
        watch=True,
    )
    return loguru.logger


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = [BASE_URL]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "constance",  # https://django-constance.readthedocs.io/
    "corsheaders",
    "ninja",  # https://github.com/vitalik/django-ninja/commit/5bdcc43
    "django_extensions",
    # "django_crontab",
    "backend.apps.back",
    "backend.apps.user",
]

MIDDLEWARE = [
    # "backend.utils.middlewares.ApiLoggingMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "backend.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.mysql",
#         "HOST": "127.0.0.1",
#         "PORT": 3306,
#         "USER": "root",
#         "PASSWORD": "password",
#         "NAME": "database",
#         "CONN_MAX_AGE": 600,
#         "OPTIONS": {
#             "charset": "utf8mb4",
#             "connect_timeout": 2,
#         },
#     },
# }


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "zh-Hans"

TIME_ZONE = "Asia/Shanghai"

DATETIME_FORMAT = "Y-m-d H:i:s"

USE_I18N = True


# 国际化翻译
# https://docs.djangoproject.com/zh-hans/4.2/topics/i18n/translation/
# 添加django.middleware.locale.LocaleMiddleware
# https://docs.djangoproject.com/zh-hans/4.2/topics/i18n/translation/#how-django-discovers-language-preference
# 创建语言文件
# https://docs.djangoproject.com/zh-hans/4.2/topics/i18n/translation/#localization-how-to-create-language-files
# python manage.py makemessages -l en -l es -l fr -l ko -l ja -l pt -l zh_Hans -l zh_Hant --ignore=venv/*
# python manage.py compilemessages --ignore=venv/*

# LOCALE_PATHS = [
#     BASE_DIR / "locale",
# ]

USE_L10N = True

USE_TZ = False


# 表达式生成
# https://crontab.guru/examples.html
# 添加定时任务
# python manage.py crontab add
# 清除定时任务
# python manage.py crontab remove
# 显示定时任务
# python manage.py crontab show

CRONTAB_COMMENT = ""  # django-crontab 注释, 区分不同项目
CRONJOBS = [
    # ("0 0 * * *", "backend.utils.mail.send_email"),
    # ("0 0 * * *", "backend.utils.mail.check_email", ">> logs/crontab.log"),
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = "static/"

MEDIA_URL_PATH = "media/"
MEDIA_BASE_URL = urljoin(BASE_URL, MEDIA_URL_PATH)
MEDIA_URL = MEDIA_BASE_URL

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
