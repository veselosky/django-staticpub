import os
from shutil import rmtree
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test.utils import override_settings
from django.conf import settings
from django.urls import reverse
from django.core.files.storage import storages
from staticpub.models import ReadResult
from staticpub.models import WriteResult
from staticpub.tasks import build_single
from staticpub.tasks import build_all
from celery import current_app
import pytest


def test_building_a_single_item():
    url = reverse("content_a")
    NEW_STATIC_ROOT = os.path.join(
        settings.BASE_DIR,
        "var",
        "test_collectstatic",
        "celery",
        "building_a_single_item",
    )
    rmtree(path=NEW_STATIC_ROOT, ignore_errors=True)
    current_app.conf.update(
        task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
        task_eager_propogates=settings.CELERY_TASK_EAGER_PROPAGATES,
    )
    with patch.object(storages["staticpub"], "location", NEW_STATIC_ROOT):
        result = build_single.delay(url=url).get()
    assert result == (
        (
            ReadResult(
                url="/content/a/",
                filename="content/a/index.html",
                status=200,
                content=b"content_a",
            ),
        ),
        (
            WriteResult(
                name="content/a/index.html",
                created=True,
                modified=True,
                md5="95792493d34debeaee4af352d18f1c76",
                storage_result="content/a/index.html",
            ),
        ),
    )


@pytest.mark.django_db
def test_building_all():
    NEW_STATIC_ROOT = os.path.join(
        settings.BASE_DIR, "var", "test_collectstatic", "celery", "building_all"
    )
    rmtree(path=NEW_STATIC_ROOT, ignore_errors=True)
    producers = ["test_urls.UserListProducer"]
    users = [get_user_model().objects.create(username="user%d" % x) for x in range(100)]
    current_app.conf.update(
        task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
        task_eager_propogates=settings.CELERY_TASK_EAGER_PROPAGATES,
    )
    with override_settings(BASE_DIR=NEW_STATIC_ROOT, STATICPUB_PRODUCERS=producers):  # noqa
        with patch.object(storages["staticpub"], "location", NEW_STATIC_ROOT):
            result = build_all.apply().get()

    assert len(result) == 123
