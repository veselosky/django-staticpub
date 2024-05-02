from collections import namedtuple
import hashlib
import logging
from mimetypes import guess_extension

from django.urls import re_path as url
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.http import HttpResponse, StreamingHttpResponse
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.encoding import force_str
from django.utils.http import url_has_allowed_host_and_scheme as is_safe_url

# noinspection PyUnresolvedReferences
from urllib.parse import urlparse
from jackfrost.signals import reader_started
from jackfrost.signals import read_page
from jackfrost.signals import reader_finished
from jackfrost.signals import writer_started
from jackfrost.signals import write_page
from jackfrost.signals import writer_finished
from jackfrost.utils import is_url_usable
from os.path import splitext

try:
    from django.utils.module_loading import import_string
except ImportError:  # pragma: no cover
    from django.utils.module_loading import import_by_path as import_string
from django.conf import settings
from django.core.paginator import Paginator
from django.test.client import Client
from jackfrost import defaults
from posixpath import normpath


__all__ = [
    "URLCollector",
    "URLReader",
    "ErrorReader",
    "URLWriter",
    "ModelRenderer",
    "SitemapRenderer",
    "MedusaRenderer",
    "FeedRenderer",
]
logger = logging.getLogger(__name__)


class CollectionError(ValueError):
    pass


class ReaderError(ValueError):
    pass


class ReadResult(namedtuple("ReadResult", "url filename status content")):
    __slots__ = ()

    def as_response(self, request):
        return StreamingHttpResponse(streaming_content=self.content, status=self.status)

    def as_urls(self):
        yield url(
            regex=r"^{url}$".format(url=self.url[1:]), name=None, view=self.as_response
        )
        yield url(
            regex=r"^{url}$".format(url=self.filename), name=None, view=self.as_response
        )


# this is a class rather than a namedtuple instance itself because otherwise
# multiprocessint cannot handle cythonized versions:
# Reason: 'PicklingError("Can't pickle <class 'importlib.WriteResult'>",)'
class WriteResult(
    namedtuple("WriteResult", "name created modified md5 storage_result")
):
    __slots__ = ()


class URLReader(object):
    """
    Given a list of URLs, presumably from a URLCollector, build them to files
    """

    __slots__ = ("urls", "_client", "_content_types")

    def __init__(self, urls):
        self.urls = tuple(urls)
        self._client = None
        self._content_types = None

    def __repr__(self):
        num = len(self.urls)
        top3 = self.urls[0:3]
        urls_themselves = ", ".join('"%s"' % x for x in top3)
        remaining = num - len(top3)
        urls = "[%(top3)s"
        if remaining > 0:
            urls += " ... %(more)d remaining"
        urls += "]"
        return "<%(mod)s.%(cls)s urls=%(urls)s>" % {
            "mod": self.__module__,
            "cls": self.__class__.__name__,
            "urls": urls % {"top3": urls_themselves, "more": remaining},
        }

    def get_target_filename(self, url, response):
        if not is_url_usable(url):
            raise ReaderError(
                "the URL '%(url)s' does not end in a forward-slash ('/'), nor "
                "does it have a file extension." % {"url": url}
            )
        path_part, extension = splitext(url)
        if extension == "":
            content_type = response["Content-Type"]
            major = content_type.split(";", 1)[0]
            extension = self.content_types.get(
                major, guess_extension(major, strict=False)
            )
            filename = "{path}/{file}{ext}".format(
                path=url, file="index", ext=extension
            )
        else:
            filename = url
        filename = filename.lstrip("/")
        return normpath(filename)

    @property
    def client(self):
        if self._client is None:
            self._client = Client()
        return self._client

    @property
    def content_types(self):
        if self._content_types is None:
            self._content_types = getattr(
                settings, "JACKFROST_CONTENT_TYPES", defaults.JACKFROST_CONTENT_TYPES
            )
        return self._content_types

    def build_redirect_page(self, url, final_url):
        urlparts = urlparse(url)
        url = urlparts.path

        if not is_safe_url(url, settings.ALLOWED_HOSTS):
            logger.error(
                "Unable to generate a redirecting page for {url} "
                "because Django says it's not safe".format(url=url)
            )
            return None

        try:
            result = render_to_string(
                [
                    normpath("{}/301.html".format(final_url)),
                    normpath("{}/301.html".format(url)),
                    "301.html",
                ],
                {"this_url": url, "next_url": final_url},
            )
        except TemplateDoesNotExist:
            logger.error(
                "Unable to generate a redirecting page for {url} "
                "because there is no 301 template".format(url=url),
                exc_info=1,
            )
            return None

        response = HttpResponse(content=result, content_type="text/html")
        filename = self.get_target_filename(url=url, response=response)
        return ReadResult(
            url=url, filename=filename, status=None, content=force_bytes(result)
        )

    def build_page(self, url):
        resp = self.client.get(url, follow=True, **{"HTTP_USER_AGENT": "jackfrost"})
        assert resp.status_code == 200, "Got %(code)d response for %(url)s" % {
            "code": resp.status_code,
            "url": url,
        }

        # calculate changed URL and redirects if necessary
        if hasattr(resp, "redirect_chain") and resp.redirect_chain:
            previous_pages = resp.redirect_chain[:]
            previous_pages.insert(0, (url, 301))  # hack to put in *this* url.
            final_url = previous_pages.pop()[0]
            urlparts = urlparse(final_url)
            url = urlparts.path
            for previous_page, previous_status in previous_pages:
                yield self.build_redirect_page(url=previous_page, final_url=url)

        filename = self.get_target_filename(url=url, response=resp)
        if resp.streaming is True:
            response_content = b"".join(resp.streaming_content)
        else:
            response_content = resp.content
        read_page.send(
            sender=self.__class__,
            instance=self,
            url=url,
            response=resp,
            filename=filename,
        )
        yield ReadResult(
            url=url,
            filename=filename,
            status=resp.status_code,
            content=force_bytes(response_content),
        )

    def build(self):
        reader_started.send(sender=self.__class__, instance=self)
        for idx, url in enumerate(self.urls, start=0):
            for result in self.build_page(url=url):
                yield result
        reader_finished.send(sender=self.__class__, instance=self)

    def __call__(self):
        return self.build()


class ErrorReader(object):
    __slots__ = ("reader",)

    def __init__(self, reader_cls=None):
        if reader_cls is None:
            reader_cls = URLReader
        self.reader = reader_cls(urls=())

    def __call__(self):
        reader_started.send(sender=self.__class__, builder=self)
        for error in (401, 403, 404, 500):
            yield self.build_error_page(error=error)
        reader_finished.send(sender=self.__class__, builder=self)

    def build_error_page(self, error):
        try:
            result = render_to_string(
                [
                    "{error!s}.html".format(error=error),
                ],
                {"request_path": None},
            )
        except TemplateDoesNotExist:
            logger.error(
                "Unable to generate a {error!s} page".format(error=error),  # noqa
                exc_info=1,
            )
            return None

        response = HttpResponse(content=result, status=error)
        filename = self.reader.get_target_filename(
            url="{error!s}.html".format(error=error), response=response
        )
        read_page.send(
            sender=self.__class__,
            instance=self,
            url=None,
            response=response,
            filename=filename,
        )
        return ReadResult(url=None, filename=filename, status=error, content=result)


class URLWriter(object):
    __slots__ = ("data", "_storage")

    def __init__(self, data):
        self.data = data
        self._storage = None

    def __repr__(self):
        num = len(self.data)
        top3 = self.data[0:3]
        remaining = num - len(top3)
        urls_themselves = ", ".join('"%s"' % x.url for x in top3)
        urls = "(%(top3)s"
        if remaining > 0:
            urls += " ... %(more)d remaining"
        urls += ")"
        return "<%(mod)s.%(cls)s data=%(urls)s>" % {
            "mod": self.__module__,
            "cls": self.__class__.__name__,
            "urls": urls % {"top3": urls_themselves, "more": remaining},
        }

    @property
    def storage(self):
        if self._storage is None:
            storage = getattr(settings, "JACKFROST_STORAGE", defaults.JACKFROST_STORAGE)
            kwargs = getattr(
                settings, "JACKFROST_STORAGE_KWARGS", defaults.JACKFROST_STORAGE_KWARGS
            )
            storage_cls = import_string(storage)
            self._storage = storage_cls(**kwargs)
        return self._storage

    def write(self, data):
        """
        :type data: jackfrost.models.ReadResult
        """
        name = data.filename
        content = force_bytes(data.content)
        content_hash = hashlib.md5(content).hexdigest()
        content_io = ContentFile(content)

        file_exists = self.storage.exists(name=name)
        if file_exists:
            self.storage.delete(name=name)
        result = self.storage.save(name=name, content=content_io)
        write_result = WriteResult(
            name=name,
            created=not file_exists,
            modified=True,
            md5=content_hash,
            storage_result=result,
        )
        write_page.send(
            sender=self.__class__,
            instance=self,
            read_result=data,
            write_result=write_result,
        )
        return write_result

    def build(self):
        writer_started.send(sender=self.__class__, instance=self)
        for idx, data in enumerate(self.data, start=0):
            write_result = self.write(data)
            yield write_result
        writer_finished.send(sender=self.__class__, instance=self)

    def __call__(self):
        return self.build()


class URLCollector(object):
    """
    >>> x = URLCollector(renderers=['a.b.C', DEF])
    >>> urls = x()
    ('/', '/a/b/', '/c/')
    """

    __slots__ = ("renderers",)

    def __init__(self, renderers=None):
        # TODO: figure out prefix necessities
        # url_prefix = getattr(settings, 'JACKFROST_SCRIPT_PREFIX', None)
        # if url_prefix is not None:
        #     set_script_prefix(url_prefix)
        self.renderers = frozenset(self.get_renderers(renderers=renderers))

    def __repr__(self):
        return "<%(mod)s.%(cls)s renderers=%(renderers)r>" % {
            "mod": self.__module__,
            "cls": self.__class__.__name__,
            "renderers": self.renderers,
        }

    def is_sitemap(self, cls):
        attrs = ("limit", "protocol", "items", "get_urls")
        return all(hasattr(cls, x) for x in attrs)

    def is_medusa_renderer(self, cls):
        attrs = ("get_paths", "generate")
        return all(hasattr(cls, x) for x in attrs)

    def is_feed(self, cls):
        attrs = ("get_feed", "feed_type")
        return all(hasattr(cls, x) for x in attrs)

    def get_renderers(self, renderers=None):
        if renderers is None:
            try:
                renderers = settings.JACKFROST_RENDERERS
            except AttributeError:
                raise ImproperlyConfigured(
                    "You have not set `JACKFROST_RENDERERS` in your "
                    "project's settings"
                )
        for renderer in renderers:
            if isinstance(renderer, str):
                renderer_cls = import_string(renderer)
            else:
                renderer_cls = renderer

            if self.is_sitemap(cls=renderer_cls):
                renderer_cls = SitemapRenderer(cls=renderer_cls)
            elif self.is_medusa_renderer(cls=renderer_cls):
                renderer_cls = MedusaRenderer(cls=renderer_cls)
            elif self.is_feed(cls=renderer_cls):
                renderer_cls = FeedRenderer(cls=renderer_cls)
            yield renderer_cls

    def get_urls(self):
        urls = set()
        for renderer in self.renderers:
            _cls_or_func_result = renderer()
            # if it was a class, we still need to call __call__
            if callable(_cls_or_func_result):
                _cls_or_func_result = _cls_or_func_result()
            # ensure it's evaluated, incase the renderer is a generator which
            # doesn't wrap itself ...
            for url in _cls_or_func_result:
                current_url = force_str(url)
                if not is_url_usable(url=current_url):
                    raise CollectionError(
                        "Renderer %(renderer)s provided the URL '%(url)s' "
                        "which does not end in a forward-slash ('/'), nor "
                        "does it have a file extension."
                        % {"renderer": renderer, "url": current_url}
                    )
                urls.add(current_url)
        return urls

    def __call__(self):
        return self.get_urls()


def collect(renderers=None):
    return URLCollector(renderers=renderers)()


def read(urls):
    return URLReader(urls=urls)()


def write(data):
    return URLWriter(data=data)()


# Originally: https://gist.github.com/kezabelle/6683315
class ChunkingPaginator(Paginator):
    def chunked_objects(self):
        for page in self.page_range:
            for obj in self.page(page):
                yield obj


class ModelRenderer(object):
    """
    If you just want to render a queryset out, and the model has
    appropriate methods, just subclass this ...
    """

    __slots__ = ()

    def get_model(self):
        raise NotImplementedError("You need to override this ")

    def get_queryset(self):
        return self.get_model().objects.all()

    def get_paginated_queryset(self):
        """
        By default we avoid consuming too much of the database at once, even
        though it means more queries overall.
        You can just replace this with
        return self.get_queryset().iterator() or something if you want.
        """
        return ChunkingPaginator(self.get_queryset(), 50).chunked_objects()

    def _get_urls(self):
        for obj in self.get_paginated_queryset():
            # on the off-chance the app knows it may want to not build things...
            if hasattr(obj, "jackfrost_can_build"):
                if obj.jackfrost_can_build() is False:
                    continue

            if hasattr(obj, "jackfrost_urls"):
                for jf_url in obj.jackfrost_urls():
                    yield jf_url
            elif hasattr(obj, "get_absolute_url"):
                yield obj.get_absolute_url()
            else:
                logger.warning("{obj!r} has no `get_absolute_url` method")
            if hasattr(obj, "get_list_url"):
                yield obj.get_list_url()

    def get_urls(self):
        return self._get_urls()

    def __call__(self):
        return frozenset(self.get_urls())


class SitemapRenderer(object):
    """
    Given a standard Django Sitemap class, this exposes enough functionality
    to be a renderer of the URLs represented by the Sitemap's location() method.
    """

    __slots__ = ("sitemap_cls",)

    def __init__(self, cls):
        self.sitemap_cls = cls

    def __repr__(self):
        return "<%(mod)s.%(cls)s sitemap_cls=%(medusa)r>" % {
            "mod": self.__module__,
            "cls": self.__class__.__name__,
            "medusa": self.sitemap_cls,
        }

    def get_urls(self):
        sitemap = self.sitemap_cls()
        for page in sitemap.paginator.page_range:
            for result in sitemap.get_urls(page=page):
                if "location" in result:
                    urlparts = urlparse(result["location"])
                    url = urlparts.path
                    yield url

    def __call__(self):
        return frozenset(self.get_urls())


class MedusaRenderer(object):
    __slots__ = ("medusa_cls",)

    def __init__(self, cls):
        self.medusa_cls = cls

    def __repr__(self):
        return "<%(mod)s.%(cls)s medusa_cls=%(medusa)r>" % {
            "mod": self.__module__,
            "cls": self.__class__.__name__,
            "medusa": self.medusa_cls,
        }

    def get_urls(self):
        return self.medusa_cls().get_paths()

    def __call__(self):
        return frozenset(self.get_urls())


class FeedRenderer(object):
    __slots__ = ("feed_cls",)

    def __init__(self, cls):
        self.feed_cls = cls

    def __repr__(self):
        return "<%(mod)s.%(cls)s feed_cls=%(medusa)r>" % {
            "mod": self.__module__,
            "cls": self.__class__.__name__,
            "medusa": self.feed_cls,
        }

    def get_urls(self):
        feed = self.feed_cls()
        # I have *NO* understanding of why the attribute has been renamed
        # ... what magic is happening here?
        for item in feed._get_dynamic_attr("items", None):
            yield feed._get_dynamic_attr("item_link", item)

    def __call__(self):
        return frozenset(self.get_urls())
