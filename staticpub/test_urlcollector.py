from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings
from staticpub.models import URLCollector
import pytest


class DummyProducer:
    def __call__(self):
        yield "/a/"
        yield "/b/"
        yield "/c/"


class DummyProducer2:
    def __call__(self):
        yield "/x/"
        yield "/y/"
        yield "/z/"


def dummy_producer_3():
    return ["/fromfunc/"]


def test_settings_error_if_not_set():
    with pytest.raises(ImproperlyConfigured):
        URLCollector(producers=None)


def test_settings_ok_when_set():
    with override_settings(STATICPUB_PRODUCERS=()):
        URLCollector(producers=None)


def test_producers_override_defaults():
    with override_settings(
        STATICPUB_PRODUCERS=("staticpub.test_urlcollector.DummyProducer",)
    ):  # noqa
        collector = URLCollector(producers=None)
    assert collector.producers == frozenset([DummyProducer])


def test_producers_override_defaults_with_class():
    with override_settings(STATICPUB_PRODUCERS=(DummyProducer,)):
        collector = URLCollector(producers=None)
    assert collector.producers == frozenset([DummyProducer])


def test_producers_provided_directly():
    collector = URLCollector(producers=(DummyProducer,))
    assert collector.producers == frozenset([DummyProducer])


def test_producers_provided_directly_as_string():
    collector = URLCollector(producers=("staticpub.test_urlcollector.DummyProducer",))  # noqa
    assert collector.producers == frozenset([DummyProducer])


def test_get_urls():
    collector = URLCollector(
        producers=(DummyProducer, DummyProducer2, dummy_producer_3)
    )
    assert frozenset(collector.get_urls()) == frozenset(
        ["/a/", "/b/", "/c/", "/fromfunc/", "/x/", "/y/", "/z/"]
    )


def test_call_calls_get_urls():
    collector = URLCollector(
        producers=(DummyProducer, DummyProducer2, dummy_producer_3)
    )
    assert frozenset(collector()) == frozenset(
        ["/a/", "/b/", "/c/", "/fromfunc/", "/x/", "/y/", "/z/"]
    )
