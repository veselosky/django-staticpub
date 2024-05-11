from staticpub.models import ModelProducer
from staticpub.models import URLReader
from staticpub.models import URLWriter

__all__ = ["build_page_for_obj"]


def build_page_for_obj(sender, instance, **kwargs):
    """
    This may be used as a receiver function for:
        - pre_save
        - post_save
    and will attempt to build the single obj's URL.
    """

    class PseudoModelProducer(ModelProducer):
        def get_paginated_queryset(self):
            return (instance,)

    instance_urls = PseudoModelProducer()()
    read = tuple(URLReader(urls=instance_urls)())
    written = tuple(URLWriter(data=read)())
    return (read, written)


def eventlog_write(sender, instance, read_result, write_result, **kwargs):
    """
    :type sender: staticpub.models.URLWriter
    :type instance: staticpub.models.URLWriter
    :type read_result: staticpub.models.ReadResult
    :type write_result: staticpub.models.WriteResult
    :type kwargs: dict
    """
    from pinax.eventlog.models import log

    # because `content` may be binary, and is thus a bytes object,
    # we need to remove it, because bytes aren't json encodable, at least
    # under python3.
    read = read_result._asdict()
    read.pop("content")
    return log(
        user=None,
        action='URL "{url!s}" written'.format(**read_result._asdict()),
        extra={
            "ReadResult": read,
            "WriteResult": write_result._asdict(),
        },
    )
