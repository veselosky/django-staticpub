# Staticpub

This package represents the [Django](https://docs.djangoproject.com/en/stable/)
application which should be in your `INSTALLED_APPS`

## Implementation information

The building happens in discrete phases:

- A `URLProducer` exposes an iterable of URLs (either by returning a
  `list`/`tuple`/`set` or by yielding individual values). Producers may be functions or
  classes.
- A `URLCollector` instance calls a set of _producers_ and reads their results into a
  single collection of URLs. By default, the list of producers is taken from
  `settings.STATICPUB_PRODUCERS`
- A `URLReader` takes a set of URLs, and reads each URL to get it's content, which it
  keeps in memory to provide to the `URLWriter`
- A `URLWriter` takes a set of URLs and their content, and writes each to a storage
  backend. You configure the storage in the `STORAGES['staticpub']` setting. It does not
  need to be the same backend as either `DEFAULT_FILE_STORAGE` or `STATICFILES_STORAGE`,
  but it can be, and that is convenient if your Django project is a single website.

## Package layout

### models

Provides `ModelRenderer`, `URLCollector`, `URLReader` and `URLWriter`. Also provides
compatibility shims `SitemapRenderer`, `FeedRenderer` and `MedusaRenderer`.

### signals

Provides `build_started`, `build_finished`, `reader_started`, `reader_finished`,
`writer_started`, `writer_finished`, `write_page` and `read_page` which are fired at
various, hopefully obvious, points.

### receivers

Provides the `build_page_for_obj` function, suitable for wiring up to `pre_save` or
`post_save` signals.

Also provides `eventlog_write`, which can be used as a receiver for the `write_page`
signal to use `pinax.eventlog` to keep a history of build data. You need to have
`pinax.eventlog` in your `INSTALLED_APPS` to use it, and you must wire the signal and
reciever together yourself, preferably in an `AppConfig.ready()`

### utils

Provides `is_url_usable` which does path-ending validity checks.
