#! /usr/bin/env python
import os
import sys
from pathlib import Path
from django.conf import settings
from django.core.wsgi import get_wsgi_application


DEBUG = os.environ.get("DEBUG", "on") == "on"
SECRET_KEY = os.environ.get("SECRET_KEY", os.urandom(32))
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,testserver").split(",")

BASE_DIR = Path(__file__).resolve().parent
VAR_DIR = BASE_DIR.joinpath("var")
VAR_DIR.mkdir(exist_ok=True, parents=True)

settings.configure(
    BASE_DIR=BASE_DIR,
    DEBUG=DEBUG,
    SECRET_KEY=SECRET_KEY,
    ALLOWED_HOSTS=ALLOWED_HOSTS,
    SITE_ID=1,
    ROOT_URLCONF="test_urls",  # or __name__ to use local ones ...
    MIDDLEWARE=(
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
    ),
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": VAR_DIR / "db.sqlite3",
        }
    },
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [BASE_DIR / "test_templates"],
            "APP_DIRS": True,
            "OPTIONS": {
                "context_processors": [
                    "django.contrib.messages.context_processors.messages",
                    "django.contrib.auth.context_processors.auth",
                    "django.template.context_processors.request",
                ]
            },
        }
    ],
    INSTALLED_APPS=(
        "django.contrib.contenttypes",
        "django.contrib.messages",
        "django.contrib.sites",
        "django.contrib.sitemaps",
        "django.contrib.auth",
        "django.contrib.staticfiles",
        "django.contrib.admin",
        "staticpub",
    ),
    STATIC_ROOT=VAR_DIR / "test_collectstatic",
    STATICFILES_DIRS=[VAR_DIR / "staticpub"],
    STATIC_URL="/__static__/",
    STATICPUB_PRODUCERS=("test_urls.UserListProducer",),
    MESSAGE_STORAGE="django.contrib.messages.storage.cookie.CookieStorage",
    SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies",
    SESSION_COOKIE_HTTPONLY=True,
    STORAGES={
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
            "LOCATION": VAR_DIR / "demo_project",
        },
        "staticpub": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
            "LOCATION": VAR_DIR / "staticpub",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
            "LOCATION": VAR_DIR / "test_collectstatic",
        },
    },
)

application = get_wsgi_application()


if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
