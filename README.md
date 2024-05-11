# Django Staticpub

Staticpub is a Django app that allows you to publish your Django websites to a static
directory (or S3 bucket, or what have you). Staticpub is non-intrusive and should work
with any Django project, so long as the pages are cacheable (no user-specific content,
for example). It utilizes Django's `storages` system, and works similarly to Django's
`staticfiles` app.

## Theory of Operation (How It Works)

Django abstracts file systems via `storages`. A common production configuration is to
set up an S3 bucket or similar cloud storage as the backend for _media_ (files uploaded
by users). Likewise, a `storage` is also configured for `staticfiles`, usually CSS and
JavaScript files that ship as part of your application.

Staticpub takes this concept a step further, declaring a `storage` for HTML pages. Once
configured, Staticpub can write pages to the `storage` as their published, or can deploy
them all at once using the `collectstaticsite` management command.

If your Django project is a single website, you can declare all 3 storages to point to
the same bucket.

## History and Alternatives

- [django-freeze][] effectively just crawls your website using `requests` and saves the
  files, similar to `wget -m`.
- [django-bakery][] takes a very different approach whereby one must extend specific
  views or models. This makes it difficult to slot into an existing project, especially
  one that makes extensive use of 3rd party apps.
- [django-distill][] is integrated through the `urls.py`, making it much easier to
  integrate into an existing Django project. It uses a two-step process that first
  generates files locally (via management command) and then (optionally) deploys them to
  a bucket (several supported deploy targets).
- [django-jackfrost][] (long unmaintained) takes an even less intrusive approach,
  needing a function to produce a list of URLs similar to Distill, but also supporting
  building single pages or subsets, and leaving static files and media to Django to
  handle. Staticpub is a fork of Jackfrost.
- [django-medusa][], which predates and inspired Jackfrost, though it doesn't appear to
  be active anymore.

## Installing

As any other Django app, install with pip and then add to your `INSTALLED_APPS`:

    INSTALLED_APPS = (
        'django.contrib.auth',
        # ...
        'staticpub',
        # ...
    )

which will enable the management command::

    python manage.py collectstaticsite --processes=N

## Configuration & usage

Set the `staticpub` key in the `STORAGES` setting to whatever storage backend you'd like
to use. If your project represents a single site, this can be the same bucket or file
system as your static files and media.

    STORAGES={
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
            "LOCATION": VAR_DIR / "demo_project",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
            "LOCATION": VAR_DIR / "test_collectstatic",
        },
        "staticpub": {
            "BACKEND": "staticpub.defaults.StaticpubFilesStorage",
            "LOCATION": VAR_DIR / "staticpub",
        },
    }

Add a `STATICPUB_PRODUCERS` setting, which should be a list or tuple of dotted paths to
python callables, much like `MIDDLEWARE`, `TEMPLATE_CONTEXT_PROCESSORS` etc:

    STATICPUB_PRODUCERS = (
        'myapp.producers.MyModelProducer',
        'my_other_app.utils.SomeOtherProducer',
    )

In theory, I don't care whether your `STATICPUB_PRODUCERS` are functions or classes; if
it's a class it must implement `__call__`. Either way, it should, when called, return a
number of URL paths to be consumed.

If you have a model which has a `get_absolute_url` method, your producer can be as
simple as::

    from staticpub.models import ModelProducer

    class MyModelProducer(ModelProducer):
        def get_model(self):
            return MyModel

If you need to customise the queryset, there is a `get_queryset` method which can be
replaced. There is also a `get_urls` method, if you need to go totally custom.

Giving `staticpub` the dotted path to a standard [Django sitemap][] as one of the
`STATICPUB_PRODUCERS` should do the right thing, and get the URLs out of the sitemap
itself without you needing to do anything or write a new producer.

Giving `staticpub` the dotted path to a subclass of a [Feed][] should do the right
thing, and get the URLs out by asking the `Feed` for the `item_link` for everything in
`items`, without you doing anything.

## Writing a producer

The most basic producer would be::

    def myproducer_yielding():
        yield reverse('app:name')

or::

    def myproducer():
        return [reverse('app:name')]

Producers may also be classes::

    class MyProducer(object):
        __slots__ = ()

        def __init__(self):
            pass

        def __call__(self):
            yield reverse('app:name')

## Listening for renders using signals

There are 8 signals in total:

- `build_started` is fired when the management command is run.
- `reader_started` is fired when a `URLReader` instance begins working.
- `read_page` is fired when a `URLReader` successfully gets a URL's content.
- `reader_finished` is fired when a `URLReader` instance completes.
- `writer_started` is fired when a `URLWriter` instance begins working.
- `write_page` is fired just after the content is written to the storage backend.
- `writer_finished` is fired when the `URLWriter` completes
- `build_finished` fires at the end of the management command.

## Rendering on model change

Additionally, there is a listener, `staticpub.receivers.build_page_for_obj` which is
suitable for being used as a `pre_save` or `post_save` receiver for a `Model` instance,
and will attempt to build just the `get_absolute_url` for that object, or a defined set
of pages related to the object.

## Defining when a model may build

If a `Model` instance implements a `staticpub_can_build` method, this is checked before
building the static page. If `staticpub_can_build` returns `False`, the page won't get
built. Any other value will result in it being built.

## Defining different URLs

If a `Model` instance implements a `staticpub_urls` method, this is used instead of the
`get_absolute_url`, and should return an iterable of all the URLs to consider building.

If the `Model` instance has a `get_list_url` method, that page will also be built.
Useful for updating any `ListView` pages, etc.

## Redirects and Error Pages

Where possible, `staticpub` will attempt to compensate for redirects (301, 302 etc) by
writing an HTML page with a `<meta refresh>` tag pointing at the final endpoint. The
template used is called `301.html`.

Additionally, static pages for 401, 403, 404 and 500 errors will be built from their
respective templates, if they exist. Useful if you want to wire up Apache
`ErrorDocument` directives or whatever.

## Running the tests (87% coverage)

Staticpub uses [pytest][] and [tox][] for testing.

You can run tests in the current environment with just `pytest`, or test all supported
configurations with `tox run`.

[django-medusa]: https://github.com/mtigas/django-medusa
[django-distill]: https://django-distill.com/
[django-freeze]: https://pypi.org/project/django-freeze/
[django-bakery]: http://django-bakery.readthedocs.org/en/latest/
[staticfiles]: https://docs.djangoproject.com/en/stable/ref/contrib/staticfiles/
[Django]: https://docs.djangoproject.com/en/stable/
[django-storages]: https://django-storages.readthedocs.org/en/latest/
[pytest]: http://pytest.org/latest/
[tox]: https://tox.wiki/
[sitemaps]: https://docs.djangoproject.com/en/stable/ref/contrib/sitemaps/
[Django sitemap]: https://docs.djangoproject.com/en/stable/ref/contrib/sitemaps/
[Django RSS Feeds]: https://docs.djangoproject.com/en/stable/ref/contrib/syndication/
[Feed]:
  https://docs.djangoproject.com/en/stable/ref/contrib/syndication/#feed-class-reference
