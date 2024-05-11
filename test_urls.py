from random import randint
from django.urls import re_path as url, reverse
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from django.contrib.sitemaps import Sitemap
from django.core.paginator import Paginator
from django.core.paginator import InvalidPage
from django.http.response import HttpResponse
from django.http.response import Http404
from django.http.response import StreamingHttpResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import render

from django.utils.encoding import force_str
from django.views.decorators.http import require_http_methods
from django.contrib.sitemaps.views import sitemap
from staticpub.actions import build_selected
from staticpub.models import ModelProducer


User.get_absolute_url = lambda x: reverse("show_user", kwargs={"pk": x.pk})
UserAdmin.actions = [build_selected]


class UserSitemap(Sitemap):
    changefreq = "never"

    def items(self):
        return get_user_model().objects.all().order_by("id")


class UserListProducer(ModelProducer):
    def get_urls(self):
        for obj in get_user_model().objects.all():
            yield reverse("show_user", kwargs={"pk": obj.pk})
        paginator = Paginator(get_user_model().objects.all().order_by("id"), 5)
        for page in paginator.page_range:
            yield reverse("users", kwargs={"page": page})
        yield reverse("users")
        yield reverse("sitemap")
        yield reverse("sitemap_section", kwargs={"section": "users"})


@require_http_methods(["POST"])
def make_users(request):
    min = randint(1, 500)
    max = min + 5
    users = [
        get_user_model().objects.get_or_create(username="user%d" % x)
        for x in range(min, max)
    ]
    created = sum(1 for user in users if user[1])
    messages.success(request, "Created %d users" % created)
    return redirect("users")


@require_http_methods(["GET"])
def show_user(request, pk):
    get_object_or_404(get_user_model(), pk=pk)
    return HttpResponse(force_str(pk))


@require_http_methods(["GET"])
def users(request, page=1):
    paginator = Paginator(get_user_model().objects.all().order_by("id"), 5)
    try:
        page = paginator.page(page)
    except InvalidPage as e:
        raise Http404("Invalid page number")

    return render(
        request,
        "users.html",
        {
            "paginator": paginator,
            "page": page,
        },
    )


@require_http_methods(["GET"])
def streamer(request):
    return StreamingHttpResponse(["hello", "I'm", "a", "stream"])


@require_http_methods(["GET"])
def content_a(request):
    return HttpResponse("content_a")


@require_http_methods(["GET"])
def content_b(request):
    return HttpResponse("content_b")


@require_http_methods(["GET"])
def redirect_a(request):
    return HttpResponseRedirect(reverse("redirect_b"))


@require_http_methods(["GET"])
def redirect_b(request):
    return HttpResponseRedirect(reverse("content_b"))


sitemaps = {
    "users": UserSitemap,
}

urlpatterns = [
    url(r"^sitemap\.xml$", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    url(
        r"^sitemap-(?P<section>.+)/$",
        sitemap,
        {"sitemaps": sitemaps},
        name="sitemap_section",
    ),
    url(r"^admin/", admin.site.urls),
    url(r"^users/show/(?P<pk>\d+)/$", show_user, name="show_user"),
    url(r"^users/generate/$", make_users, name="make_users"),
    url(r"^users/(?P<page>\d+)/$", users, name="users"),
    url(r"^$", users, name="users"),
    url(r"^streamable/$", streamer, name="streamable"),
    url(r"^content/a/b/$", content_b, name="content_b"),
    url(r"^content/a/$", content_a, name="content_a"),
    url(r"^r/a/$", redirect_a, name="redirect_a"),
    url(r"^r/a_b/$", redirect_b, name="redirect_b"),
]
