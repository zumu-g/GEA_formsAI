import docx
from docx.oxml.ns import qn

from forms_fill.forms.cav_rent_increase_notice.spec import SPEC, build_context
from forms_fill.models import TenancyBundle
from forms_fill.render import compute_blank_fields, render


def _ctx(sample_bundle_dict, caller_fields):
    return build_context(TenancyBundle.model_validate(sample_bundle_dict), caller_fields)


def _all_text(document) -> str:
    parts = []
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                parts.append(cell.text)
    return " ".join(parts)


def test_render_writes_docx_with_values(tmp_path, sample_bundle_dict, caller_fields):
    ctx = _ctx(sample_bundle_dict, caller_fields)
    docx_path, _pdf, _warn = render(SPEC, ctx, tmp_path)
    assert docx_path.exists()
    text = _all_text(docx.Document(str(docx_path)))
    assert "12 Example Street, Richmond" in text
    assert "Jane Alice Smith" in text
    assert "Robert James Owner" in text
    assert "market comparison (rental CMA)" in text


def test_blank_fields_reported(tmp_path, sample_bundle_dict, caller_fields):
    # renter has no after-hours? it does in fixture; blank the provider after-hours
    sample_bundle_dict["rental_provider"]["phone_after_hours"] = ""
    ctx = _ctx(sample_bundle_dict, caller_fields)
    blanks = compute_blank_fields(SPEC, ctx)
    assert "provider_after_hours" in blanks
    # selector is never counted
    assert "rent_period" not in blanks


def test_correct_period_checkbox_ticked(tmp_path, sample_bundle_dict, caller_fields):
    caller_fields["rent_period"] = "fortnight"
    ctx = _ctx(sample_bundle_dict, caller_fields)
    docx_path, _pdf, _warn = render(SPEC, ctx, tmp_path)
    document = docx.Document(str(docx_path))
    # table 15 (current rent): boxes are week(0), fortnight(1), calendar month(2)
    boxes = document.tables[15]._tbl.findall(".//" + qn("w:checkBox"))
    checked = [
        b.find(qn("w:checked")) is not None
        and b.find(qn("w:checked")).get(qn("w:val")) == "1"
        for b in boxes
    ]
    assert checked == [False, True, False]


def test_filled_and_blank_counts_consistent(tmp_path, sample_bundle_dict, caller_fields):
    ctx = _ctx(sample_bundle_dict, caller_fields)
    blanks = compute_blank_fields(SPEC, ctx)
    selectors = set(SPEC.selector_fields)
    declared_text = [f for f in SPEC.declared_fields if f not in selectors]
    # every declared text field is either filled or blank, no overlap
    filled = [f for f in declared_text if f not in blanks]
    assert len(filled) + len(blanks) == len(declared_text)
