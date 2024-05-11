import os
from pathlib import Path
import django
from django.conf import settings

BASE_DIR = Path(__file__).resolve().parent
VAR_DIR = BASE_DIR.joinpath("var")
VAR_DIR.mkdir(exist_ok=True, parents=True)
VAR_DIR.joinpath("staticpub").mkdir(exist_ok=True, parents=True)
VAR_DIR.joinpath("test_collectstatic").mkdir(exist_ok=True, parents=True)


def pytest_configure():
    if not settings.configured:
        settings.configure(
            DATABASES={
                "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
            },
            INSTALLED_APPS=(
                "django.contrib.sites",
                "django.contrib.sitemaps",
                "django.contrib.auth",
                "django.contrib.admin",
                "django.contrib.contenttypes",
                "django.contrib.messages",
                "staticpub",
                "pinax.eventlog",
            ),
            # these are the default in 1.8, so we should make sure we
            # work with those.
            MIDDLEWARE=(
                "django.contrib.sessions.middleware.SessionMiddleware",
                "django.middleware.common.CommonMiddleware",
                "django.middleware.csrf.CsrfViewMiddleware",
                "django.contrib.auth.middleware.AuthenticationMiddleware",
                # 'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
                "django.contrib.messages.middleware.MessageMiddleware",
                "django.middleware.clickjacking.XFrameOptionsMiddleware",
            ),
            BASE_DIR=BASE_DIR,
            SECRET_KEY="testing_only",
            SITE_ID=1,
            STATIC_URL="/__s__/",
            STATIC_ROOT=VAR_DIR / "test_collectstatic",
            ROOT_URLCONF="test_urls",
            TEMPLATES=[
                {
                    "BACKEND": "django.template.backends.django.DjangoTemplates",
                    "APP_DIRS": True,
                    "DIRS": [BASE_DIR / "test_templates"],
                },
            ],
            PASSWORD_HASHERS=("django.contrib.auth.hashers.MD5PasswordHasher",),
            CELERY_TASK_ALWAYS_EAGER=True,
            CELERY_TASK_EAGER_PROPAGATES=True,
            STORAGES={
                "default": {
                    "BACKEND": "django.core.files.storage.FileSystemStorage",
                    "LOCATION": VAR_DIR / "demo_project",
                },
                "staticpub": {
                    "BACKEND": "staticpub.defaults.StaticpubFilesStorage",
                    "LOCATION": VAR_DIR / "staticpub",
                },
                "staticfiles": {
                    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
                    "LOCATION": VAR_DIR / "test_collectstatic",
                },
            },
        )
    if hasattr(django, "setup"):
        django.setup()
