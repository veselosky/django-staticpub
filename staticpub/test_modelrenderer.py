from django.contrib.auth import get_user_model
from django.test.testcases import TransactionTestCase
from staticpub.models import ModelProducer
import pytest


def test_default_get_model_raises_error():
    class SubModelProducer(ModelProducer):
        pass

    with pytest.raises(NotImplementedError):
        SubModelProducer().get_model()


def test_get_model_defined_on_subclass_ok():
    class SubModelProducer(ModelProducer):
        def get_model(self):
            return get_user_model()

    assert SubModelProducer().get_model() == get_user_model()


@pytest.mark.django_db
def test_get_queryset():
    class SubModelProducer(ModelProducer):
        def get_model(self):
            return get_user_model()

    obj = get_user_model().objects.create()
    assert set(SubModelProducer().get_queryset()) == {obj}


class PaginatedQuerySetTestCase(TransactionTestCase):
    def test_does_minimum_2_queries(self):
        class SubModelProducer(ModelProducer):
            def get_model(self):
                return get_user_model()

        users = {
            get_user_model().objects.create(username="user_{}".format(x))
            for x in range(0, 5)
        }
        with self.assertNumQueries(2):
            result = set(SubModelProducer().get_paginated_queryset())
        assert users == result

    def test_does_n_queries(self):
        class SubModelProducer(ModelProducer):
            def get_model(self):
                return get_user_model()

        users = {
            get_user_model().objects.create(username="user_{}".format(x))
            for x in range(0, 100)
        }
        with self.assertNumQueries(3):
            result = set(SubModelProducer().get_paginated_queryset())
        assert users == result


@pytest.mark.django_db
def test_get_urls_skips_because_cannot_build():
    class UserProxy(get_user_model()):
        def staticpub_can_build(self):
            return False

        class Meta:
            proxy = True
            ordering = ["pk"]

    class SubModelProducer(ModelProducer):
        def get_model(self):
            return UserProxy

    get_user_model().objects.create()
    assert SubModelProducer()() == frozenset()


@pytest.mark.django_db
def test_get_urls_can_build():
    class UserProxy2(get_user_model()):
        def staticpub_can_build(self):
            return True

        class Meta:
            proxy = True

    class SubModelProducer(ModelProducer):
        def get_model(self):
            return UserProxy2

    x = get_user_model().objects.create()
    assert SubModelProducer()() == frozenset(["/users/show/%d/" % x.pk])


@pytest.mark.django_db
def test_get_urls_prefers_staticpub_variant():
    class UserProxy3(get_user_model()):
        def staticpub_urls(self):
            return ["/jf/"]

        def get_absolute_url(self):
            return "/not-jf/"

        class Meta:
            proxy = True

    class SubModelProducer(ModelProducer):
        def get_model(self):
            return UserProxy3

    get_user_model().objects.create()
    assert SubModelProducer()() == frozenset(["/jf/"])


@pytest.mark.django_db
def test_get_urls_uses_get_absolute_url_and_list_url():
    class UserListURLProxy(get_user_model()):
        def get_absolute_url(self):
            return "/not-jf/"

        def get_list_url(self):
            return "/woo/"

        class Meta:
            proxy = True

    class SubModelProducer(ModelProducer):
        def get_model(self):
            return UserListURLProxy

    get_user_model().objects.create()
    assert SubModelProducer()() == frozenset(["/not-jf/", "/woo/"])


@pytest.mark.django_db
def test_call_does_build():
    class SubModelProducer(ModelProducer):
        def get_model(self):
            return get_user_model()

    assert SubModelProducer()() == frozenset()
