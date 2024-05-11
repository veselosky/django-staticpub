from django.contrib.auth import get_user_model
from staticpub.models import URLCollector, MedusaProducer
import pytest


def test_medusa_producer_repr():
    assert (
        repr(MedusaProducer(cls=1)) == "<staticpub.models.MedusaProducer medusa_cls=1>"
    )


@pytest.mark.django_db
def test_medusa_producer_support():
    class UserMedusaProxy(get_user_model()):
        def get_absolute_url(self):
            return "/test/medusa/{}/".format(self.pk)

        class Meta:
            proxy = True

    class MedusaLikeProducer(object):
        def generate(self):
            return True

        def get_paths(self):
            return [x.get_absolute_url() for x in UserMedusaProxy.objects.all()]

    users = [
        get_user_model().objects.create(username="medusa{}".format(x))
        for x in range(1, 5)
    ]
    user_pks = [u.pk for u in users]
    users_urls = [
        up.get_absolute_url() for up in UserMedusaProxy.objects.filter(pk__in=user_pks)
    ]
    collector = URLCollector(producers=(MedusaLikeProducer,))
    assert frozenset(collector()) == frozenset(users_urls)
