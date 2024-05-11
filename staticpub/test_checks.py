from django.test.utils import override_settings


@override_settings()
def test_missing_setting():
    from django.apps import apps
    from django.core.checks import WARNING
    from django.conf import settings

    del settings.STATICPUB_PRODUCERS
    from staticpub.checks import check_producers_setting

    appconfigs = apps.get_app_configs()
    output = check_producers_setting(appconfigs)[0]
    assert output.id == "staticpub.W001"
    assert output.level == WARNING


@override_settings(STATICPUB_PRODUCERS="test.path")
def test_setting_is_string():
    """
    This is bad: ('test.test.test')
    this is good: ('test.test.test',)
    """
    from django.apps import apps
    from django.core.checks import ERROR
    from staticpub.checks import check_producers_setting

    appconfigs = apps.get_app_configs()
    output = check_producers_setting(appconfigs)[0]
    assert output.id == "staticpub.E001"
    assert output.level == ERROR


@override_settings(STATICPUB_PRODUCERS=["test.path"])
def test_setting_is_invalid_path():
    from django.apps import apps
    from django.core.checks import ERROR
    from staticpub.checks import check_producers_setting

    appconfigs = apps.get_app_configs()
    output = check_producers_setting(appconfigs)[0]
    assert output.id == "staticpub.E002"
    assert output.level == ERROR
    assert output.msg == "Unable to import test.path"


@override_settings(STATICPUB_PRODUCERS=[1])
def test_setting_is_not_a_string_to_import():
    from django.apps import apps
    from staticpub.checks import check_producers_setting

    appconfigs = apps.get_app_configs()
    output = check_producers_setting(appconfigs)
    assert output == []
