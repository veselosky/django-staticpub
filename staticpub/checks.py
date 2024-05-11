from django.core.checks import Warning
from django.core.checks import Error

try:
    from django.utils.module_loading import import_string
except ImportError:  # pragma: no cover
    from django.utils.module_loading import import_by_path as import_string


def check_producers_setting(app_configs, **kwargs):
    from django.conf import settings

    errors = []
    if not hasattr(settings, "STATICPUB_PRODUCERS"):
        errors.append(
            Warning(
                msg="You don't have any producers defined",
                hint="Set STATICPUB_PRODUCERS to a tuple of producers",
                id="staticpub.W001",
            )
        )
    elif isinstance(settings.STATICPUB_PRODUCERS, str):
        errors.append(
            Error(
                msg="STATICPUB_PRODUCERS is a string, not an iterable",
                hint="You may have missed the trailing comma from a tuple...",
                id="staticpub.E001",
            )
        )
    else:
        for producer in settings.STATICPUB_PRODUCERS:
            if isinstance(producer, str):
                try:
                    import_string(producer)
                except ImportError:
                    errors.append(
                        Error(
                            msg="Unable to import %s" % producer,
                            hint="Double check this is the dotted path to a "
                            "producer instance",
                            id="staticpub.E002",
                        )
                    )
    return errors


def check_staticpub_storage_setting(app_configs, **kwargs):
    from django.conf import settings

    errors = []
    if "staticpub" not in settings.STORAGES:
        errors.append(
            Warning(
                msg="The STORAGES setting does not include 'staticpub'",
                hint="Set STORAGES['staticpub'] to a dotted path to a storage class",
                id="staticpub.E003",
            )
        )
    else:
        try:
            import_string(settings.STORAGES["staticpub"]["BACKEND"])
        except ImportError:
            errors.append(
                Error(
                    msg="Unable to import %s" % settings.STORAGES["staticpub"],
                    hint="Double check this is the dotted path to a storage class",
                    id="staticpub.E004",
                )
            )
    return errors
