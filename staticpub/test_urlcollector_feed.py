from django.contrib.auth import get_user_model
from django.contrib.syndication.views import Feed
from staticpub.models import URLCollector, FeedProducer
import pytest


def test_feed_producer_repr():
    assert repr(FeedProducer(cls=1)) == "<staticpub.models.FeedProducer feed_cls=1>"


@pytest.mark.django_db
def test_feed_producer_support():
    class UserFeedProxy(get_user_model()):
        def get_absolute_url(self):
            return "/test/user/{}/".format(self.pk)

        class Meta:
            proxy = True

    class UserFeed(Feed):
        def items(self):
            return UserFeedProxy.objects.all()

    users = [
        get_user_model().objects.create(username="u{}".format(x)) for x in range(1, 5)
    ]
    user_pks = [u.pk for u in users]
    users_urls = [
        up.get_absolute_url() for up in UserFeedProxy.objects.filter(pk__in=user_pks)
    ]

    collector = URLCollector(producers=(UserFeed,))
    assert frozenset(collector()) == frozenset(users_urls)
