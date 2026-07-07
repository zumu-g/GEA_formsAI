import pytest

from forms_fill.errors import UnknownFormError
from forms_fill.registry import available_forms, get_form_spec


def test_cav_form_registered():
    spec = get_form_spec("cav_rent_increase_notice")
    assert spec.key == "cav_rent_increase_notice"
    assert spec.template.exists()


def test_available_forms_lists_cav():
    assert "cav_rent_increase_notice" in available_forms()


def test_ntv_form_registered():
    spec = get_form_spec("notice_to_vacate")
    assert spec.key == "notice_to_vacate"
    assert spec.template.exists()


def test_available_forms_lists_ntv():
    assert "notice_to_vacate" in available_forms()


def test_unknown_form_raises_with_available_listed():
    with pytest.raises(UnknownFormError) as exc:
        get_form_spec("does_not_exist")
    assert "cav_rent_increase_notice" in str(exc.value)
