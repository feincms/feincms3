import requests_mock
from django.forms.models import modelform_factory
from django.utils.translation import deactivate_all

from feincms3.plugins.external import NoembedValidationForm, oembed_json
from testapp.models import External


def test_noembed_validation():
    """Test external plugin validation a bit"""
    deactivate_all()

    form_class = modelform_factory(
        External, form=NoembedValidationForm, fields="__all__"
    )

    # Should not crash if URL not provided (765a6b6b53e)
    form = form_class({})
    assert not form.is_valid()

    # Provide an invalid URL
    form = form_class({"url": "http://192.168.250.1:65530"})
    assert not form.is_valid()
    assert "<li>Unable to fetch HTML for this URL, sorry!</li>" in str(form.errors)


def test_oembed_request():
    """The oEmbed request generation works as expected"""
    with requests_mock.Mocker() as m:
        m.get("https://noembed.com/embed", text="{}")

        assert oembed_json("https://www.youtube.com/watch?v=4zGnNmncJWg") == {}
        assert oembed_json("https://www.youtube.com/watch?v=4zGnNmncJWg") == {}
        assert (
            oembed_json(
                "https://www.youtube.com/watch?v=4zGnNmncJWg",
                params={"maxwidth": 4000, "maxheight": 3000},
            )
            == {}
        )

    assert len(m.request_history) == 2
    assert m.request_history[0].qs["maxwidth"] == ["1200"]
    assert m.request_history[1].qs["maxwidth"] == ["4000"]

    with requests_mock.Mocker() as m:
        m.get("https://noembed.com/embed", text='{"different": ""}')

        assert oembed_json("https://www.youtube.com/watch?v=4zGnNmncJWg") == {}
        assert oembed_json(
            "https://www.youtube.com/watch?v=4zGnNmncJWg", force_refresh=True
        ) == {"different": ""}
