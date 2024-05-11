import os
from django.contrib.staticfiles.storage import StaticFilesStorage


__all__ = [
    "StaticpubFilesStorage",
    "STATICPUB_CONTENT_TYPES",
]


class StaticpubFilesStorage(StaticFilesStorage):
    def __init__(self, location=None, *args, **kwargs):
        if location is None:
            from django.conf import settings

            location = os.path.join(settings.BASE_DIR, "var", "staticpub")
        super(StaticpubFilesStorage, self).__init__(location, *args, **kwargs)


STATICPUB_CONTENT_TYPES = {
    "text/plain": ".txt",
    "text/html": ".html",
    "text/javascript": ".js",
    "application/javascript": ".js",
    "text/json": ".json",
    "application/json": ".json",
    "text/css": ".css",
    "text/x-markdown": ".md",
    "text/markdown": ".md",
    "text/xml": ".xml",
    "application/xml": ".xml",
    "text/rss+xml": ".rss",
    "application/rss+xml": ".rss",
    "application/atom+xml": ".atom",
    "application/pdf": ".pdf",
    "text/tab-separated-values": ".tsv",
}
