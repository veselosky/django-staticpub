from django.apps import AppConfig
from django.core.checks import registry


class StaticpubAppConfig(AppConfig):
    name = "staticpub"
    verbose_name = "StaticPub"

    def ready(self):
        from .checks import check_producers_setting, check_staticpub_storage_setting

        registry.register(check_producers_setting)
        registry.register(check_staticpub_storage_setting)
