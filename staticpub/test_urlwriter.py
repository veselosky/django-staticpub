import os
from shutil import rmtree
from unittest.mock import patch
from django.conf import settings
from django.urls import reverse, clear_script_prefix
from django.test.utils import override_settings
from staticpub.defaults import StaticpubFilesStorage
from staticpub.models import URLReader
from staticpub.models import ReadResult
from staticpub.models import URLWriter


def test_repr_short():
    reads = [
        ReadResult(url="/%d/" % x, filename=None, status=None, content=None)
        for x in range(2)
    ]
    reader = URLWriter(data=reads)
    assert repr(reader) == '<staticpub.models.URLWriter data=("/0/", "/1/")>'


def test_repr_long():
    reads = [
        ReadResult(url="/%d/" % x, filename=None, status=None, content=None)
        for x in range(4)
    ]
    reader = URLWriter(data=reads)
    assert (
        repr(reader)
        == '<staticpub.models.URLWriter data=("/0/", "/1/", "/2/" ... 1 remaining)>'
    )  # noqa


def test_get_storage():
    writer = URLWriter(data=None)
    assert isinstance(writer.storage, StaticpubFilesStorage) is True
    assert writer.storage.location == os.path.join(
        settings.BASE_DIR, "var", "staticpub"
    )


def test_build():
    reader = URLReader(
        urls=(
            reverse("content_a"),
            reverse("content_b"),
        )
    )
    read_results = tuple(reader())
    NEW_STATIC_ROOT = os.path.join(
        settings.BASE_DIR, "var", "test_collectstatic", "urlwriter", "build"
    )
    rmtree(path=NEW_STATIC_ROOT, ignore_errors=True)
    writer = URLWriter(data=read_results)
    with patch.object(writer.storage, "location", NEW_STATIC_ROOT):
        storage = writer.storage
        output = writer()

    files_saved = []
    for built in output:
        files_saved.append(built.storage_result)
    sorted_files_saved = sorted(files_saved)
    assert sorted_files_saved == ["content/a/b/index.html", "content/a/index.html"]
    assert storage.open(sorted_files_saved[-2]).readlines() == [b"content_b"]
    assert storage.open(sorted_files_saved[-1]).readlines() == [b"content_a"]
    # remove(storage)


def test_build_with_force_script_name():
    NEW_STATIC_ROOT = os.path.join(
        settings.BASE_DIR,
        "var",
        "test_collectstatic",
        "urlwriter",
        "build_with_force_script_name",
    )
    rmtree(path=NEW_STATIC_ROOT, ignore_errors=True)
    with override_settings(FORCE_SCRIPT_NAME="test.php", BASE_DIR=NEW_STATIC_ROOT):
        reader = URLReader(
            urls=(
                reverse("content_a"),
                reverse("content_b"),
            )
        )
        read_results = tuple(reader())
        writer = URLWriter(data=read_results)
        with patch.object(writer.storage, "location", NEW_STATIC_ROOT):
            output = writer()
        storage = writer.storage
        files_saved = []
        for built in output:
            files_saved.append(built.storage_result)
        sorted_files_saved = sorted(files_saved)
        assert sorted_files_saved == ["content/a/b/index.html", "content/a/index.html"]
        try:
            assert storage.open(sorted_files_saved[-2]).readlines() == [b"content_b"]
            assert storage.open(sorted_files_saved[-1]).readlines() == [b"content_a"]
        finally:
            # failure to do this will bleed the value of FORCE_SCRIPT_NAME
            # into other tests ...
            clear_script_prefix()


def test_write_single_item():
    reader = URLReader(urls=[reverse("content_b")])
    read_results = tuple(reader())
    writer = URLWriter(data=read_results)

    NEW_STATIC_ROOT = os.path.join(
        settings.BASE_DIR, "var", "test_collectstatic", "urlwriter", "write_single_item"
    )
    rmtree(path=NEW_STATIC_ROOT, ignore_errors=True)
    with patch.object(writer.storage, "location", NEW_STATIC_ROOT):
        output = writer.write(read_results[0])
        storage = writer.storage

    assert output.md5 == "f8ee7c48dfd7f776b3d011950a5c02d1"
    assert output.created is True
    assert output.modified is True
    assert output.name == "content/a/b/index.html"
    assert storage.open(output.name).readlines() == [b"content_b"]
