from django.contrib.auth import get_user_model
from django.contrib.sitemaps import Sitemap
from staticpub.models import URLCollector, SitemapProducer
import pytest


def test_sitemap_producer_repr():
    assert (
        repr(SitemapProducer(cls=1))
        == "<staticpub.models.SitemapProducer sitemap_cls=1>"
    )


@pytest.mark.django_db
def test_sitemap_producer_support():
    class UserSitemapProxy(get_user_model()):
        def get_absolute_url(self):
            return "/test/user/{}/".format(self.pk)

        class Meta:
            proxy = True
            ordering = ("pk",)

    class UserSitemap(Sitemap):
        def items(self):
            return UserSitemapProxy.objects.all()

    users = [
        get_user_model().objects.create(username="u{}".format(x)) for x in range(1, 5)
    ]
    user_pks = [u.pk for u in users]
    users_urls = [
        up.get_absolute_url() for up in UserSitemapProxy.objects.filter(pk__in=user_pks)
    ]
    collector = URLCollector(producers=(UserSitemap,))
    assert frozenset(collector()) == frozenset(users_urls)
