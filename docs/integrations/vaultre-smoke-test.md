# VaultRE live smoke test — run when VAULTRE_BEARER_TOKEN arrives

Blocking follow-up for the 2026-07-31 property-autopopulate plan. Every
VaultRE response shape in `forms_fill/forms_fill/providers/vaultre.py` is
stub-verified only — the swagger spec leaves the owners/landlords GET bodies
untyped, so the first live round-trip must confirm the parsing.

Set `VAULTRE_API_KEY` + `VAULTRE_BEARER_TOKEN`, then check each item. Do NOT
log raw response bodies — landlord/vendor contact details are personal data;
note status codes and field presence only.

## Sale mode (sales authority / letter of offer)

- [ ] `search_lots("<known sale address>")` returns the listing (endpoint `/properties/residential/sale`, bare-array vs `{"items": [...]}` — note which).
- [ ] Property detail (`/properties/residential/sale/{id}`) carries `saleLifeId` (note actual field name if different).
- [ ] `/properties/{id}/sale/{lifeid}/owners` returns owners — note shape: bare list vs items envelope; full contacts vs id references.
- [ ] Vendor name/address/phone/email map correctly into the form preview.

## Lease mode (PM exclusive leasing authority)

- [ ] `search_lots("<known rental address>", listing="lease")` returns the listing from `/properties/residential/lease`.
- [ ] Lease detail carries `leaseLifeId`.
- [ ] `/properties/{id}/lease/{lifeid}/landlords` returns landlords — note shape as above.
- [ ] Owner name/address populate on the leasing authority form end-to-end (search → pick → preview → prefill).

## On any mismatch

Fix the parsing in `vaultre.py`, update the stub fixtures in
`forms_fill/tests/test_vaultre.py` to the observed live shape, and update the
module docstring (remove the "unverified against a live response" caveat once
both modes have round-tripped).
