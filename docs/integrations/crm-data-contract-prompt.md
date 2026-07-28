# Prompt: Data contract for the GEA forms-fill tool

> Paste this into a `GEA_crmAI` session (or hand to the CRM team). It specifies the
> read-only endpoint the forms-fill tool needs. The same contract is implemented
> first against **PropertyMe** and later against **GEA CRM** — so this response
> shape is the swappable interface both providers must satisfy.

---

## Context

We're building a headless **forms-fill tool** (separate service) that completes legal
property forms — first the CAV "Notice of proposed rent increase to renter of rented
premises" (RTA 1997 s44(1)). The tool is given **identifiers** and **caller-supplied
rent figures**, and it must **fetch the tenancy/property/people details** from our
system to fill the form.

The tool talks to a single `PropertyDataProvider` interface. We will wire **PropertyMe**
as the first provider now, then switch the default to **GEA CRM** later with **no change
to the forms tool** — only a new adapter. For that to work, GEA CRM must expose the data
in the shape below.

**What we need from you (GEA CRM):** a read-only, server-to-server endpoint that, given a
property/tenancy identifier, returns the renter(s), the rental provider (owner), and the
premises in one bundle.

---

## Endpoint

```
GET /api/forms/tenancy-bundle?lotId=<id>&tenancyId=<id>
```

- **Auth:** server-to-server only. Reuse the existing `x-sync-secret` / `SYNC_SECRET`
  pattern already used by `POST /api/admin/sync/propertyme`. No user session.
- **Lookup:** accept `tenancyId` (preferred) and/or `lotId`. If only `lotId` is given,
  resolve the **current active lease** for that property. Return `404` with a clear JSON
  error if no active tenancy is found.
- **Read-only.** No writes, no side effects.

We pass whatever identifiers PropertyMe/GEA CRM key on. Today that's PropertyMe
`lot_id` / `tenancy_id`; for GEA CRM map these to `ManagedProperty.id` / `Lease.id`
(or a stable external id if you prefer — just document which).

---

## Response shape (the contract)

Return exactly this JSON. **Every field below is required to be present**; use `null`
or `""` when the value is genuinely unknown — do **not** omit keys. The forms tool
reports which fields came back blank so the PM can be warned, so blanks are expected and
fine, but missing keys break the contract.

```jsonc
{
  "premises": {
    "address_line": "12 Example St, Richmond",   // street address of the rented premises
    "suburb": "Richmond",
    "state": "VIC",
    "postcode": "3121"
  },

  "renters": [
    {
      "full_name": "Jane Alice Smith",           // renter's full legal name
      "address_for_service": "PO Box 5, Richmond VIC 3121", // null/"" if same as premises
      "service_postcode": "3121",
      "phone_business_hours": "03 9000 0000",     // may be blank
      "phone_after_hours": "0400 000 000",        // may be blank
      "email": "jane@example.com"                 // may be blank
    }
    // 1..N renters. The form has slots for 4; the tool adds an overflow note if >4.
  ],

  "rental_provider": {
    // IMPORTANT: this MUST be the OWNER, not the managing agent/agency.
    // The form explicitly forbids an agent's name in this field.
    "full_name": "John Robert Owner",             // the owner's full legal name
    "service_address": "Level 2, 100 Agency Rd, Melbourne VIC 3000", // agency address IS allowed here
    "service_postcode": "3000",
    "phone_business_hours": "03 9111 1111",        // owner OR agent contact — agent is fine here
    "phone_after_hours": "",
    "email": "pm@agency.com"
  },

  "meta": {
    "tenancy_id": "<echoed>",
    "lot_id": "<echoed>",
    "source": "gea_crm",                          // or "propertyme"
    "as_at": "2026-06-17T00:00:00Z"               // when the data was read
  }

  // "lease" is OPTIONAL — see "Lease terms" section below. Omit the whole
  // key entirely until you're ready to populate it; the tool treats a
  // missing "lease" exactly like a missing "current_rent" today (blank
  // fields, not an error).
}
```

### Field mapping to your current Prisma models (for the GEA CRM adapter)

| Contract field | GEA CRM source |
|---|---|
| `premises.address_line` / `suburb` / `state` / `postcode` | `ManagedProperty.propertyAddress` / `suburb` / `state` / `postcode` |
| `renters[]` | `Lease.tenants[] → TenantLease → Tenant → Contact` (active lease resolved from `lotId`/`tenancyId`) |
| `renters[].full_name` | `Contact` name |
| `renters[].address_for_service` / `email` / phones | `Contact` address/email/phone (blank if unknown) |
| `rental_provider.full_name` | **`ManagedProperty.owner` (Contact)** — the owner, never the agent |
| `rental_provider.service_address` | agency address (allowed) or owner address |
| `rental_provider.phone_*` / `email` | owner or managing-agent contact |

---

## Hard requirements (please don't deviate)

1. **Owner, not agent**, in `rental_provider.full_name`. This is a legal constraint on the
   form. If your data can't distinguish owner from managing agent for this field, return
   the owner contact explicitly and flag any ambiguity in `meta`.
2. **Stable key set.** Never drop keys; blanks are `null`/`""`, not omitted.
3. **One active tenancy per call.** If a property has multiple/overlapping leases, return
   the current active one and note it; don't return an array of leases.
4. **Read-only + secret-protected**, matching the existing sync-route auth.
5. **Identical shape to the PropertyMe provider.** This JSON *is* the interface. When we
   flip the default from PropertyMe to GEA CRM, only the adapter changes — the forms tool
   does not.

---

## What we do NOT need from you

- No rent figures, dates, or eligibility — the **caller supplies** `current_rent`,
  `new_rent`, `increase`, `rent_period`, `start_date`, and `method_basis`, and the tool
  renders them verbatim. Do not compute or validate any statutory logic.
- No delivery/serving, no signatures — handled by the PM at serve time.

---

## Address search endpoint (additive — needed for the property-lookup UI)

The forms tool's UI lets a user type a partial address and pick a match before
fetching the bundle above. PropertyMe already supports this by scanning its own
active-tenancy list; GEA CRM needs an equivalent endpoint so address search works
for GEA CRM too, instead of falling back to manual Lot ID / Tenancy ID entry.

```
GET /api/forms/tenancy-search?q=<free text>
```

- **Auth:** identical to `tenancy-bundle` — `x-sync-secret` / `SYNC_SECRET`, no user session.
- **Lookup:** case-insensitive substring match against the property address. No fuzzy
  matching or geocoding required — a simple `ILIKE '%q%'`-style scan is sufficient.
- **Read-only.** No writes, no side effects.
- **Empty/missing `q`:** return `400` with a clear JSON error.
- **No auth:** `401`, same as `tenancy-bundle`.

### Response shape

Return a JSON array (not wrapped in an object), one entry per matching property:

```jsonc
[
  {
    "lot_id": "<ManagedProperty id or stable external id>",
    "address_label": "12 Example St, Richmond VIC 3121",
    "tenancy_id": "<current active Lease id, or \"\" if the lot is vacant/owner-occupied>"
  }
  // as many matches as you have; the forms tool caps display at 10 client-side,
  // so no need to paginate — returning more than 10 is fine, we'll trim.
]
```

- `lot_id` / `tenancy_id` must be the **same identifiers** `tenancy-bundle` above
  accepts as `lotId`/`tenancyId` — a match the user picks is fed straight back into
  that endpoint.
- `tenancy_id` is `""` (not omitted, not null) when there's no current active lease —
  this mirrors how `tenancy-bundle` already handles vacant lots via its own 404 path;
  here it's just an empty string in a list entry rather than an error.
- Field mapping is the same as the table above: `address_label` from
  `ManagedProperty.propertyAddress` (+ suburb/state/postcode if you want to compose
  the full label), `lot_id` from `ManagedProperty.id`, `tenancy_id` from the current
  active `Lease.id` for that property (empty if none).

---

## Lease terms (additive, optional — needed for the rental agreement form)

We're now also filling the CAV "Residential rental agreement" (Form 1 / Form 2),
which needs the lease's own terms, not just who's on it. This is an **optional**
`lease` block on `tenancy-bundle`'s response, alongside the existing optional
`current_rent`/`rent_period` fields you may already return. Omit the whole
`lease` key until you're ready — the tool treats an absent block exactly like
an absent `current_rent` today: the corresponding form fields come back blank,
never an error. This is a **relaxation** of requirement 2 above ("never drop
keys") scoped to this one block only — every other key in the contract must
still always be present.

```jsonc
{
  // ...premises / renters / rental_provider / meta as above...

  "lease": {
    "term_type": "fixed",              // "fixed" or "periodic"; "" if unknown
    "fixed_start_date": "2026-01-15",  // "" if not a fixed term
    "fixed_end_date": "2027-01-14",    // "" if not a fixed term
    "periodic_start_date": null,       // "" / null if not periodic
    "rent_amount": "550",              // plain string, no currency symbol
    "rent_period": "week",             // "week" | "fortnight" | "calendar month"
    "rent_payment_day": "Friday",
    "first_rent_due_date": "2026-01-15",
    "bond_amount": "2200",
    "bond_due_date": "2026-01-08"
  }
}
```

Every key in `lease` follows the same blank convention as the rest of the
contract: `null` or `""` for unknown, never omitted **once you include the
`lease` key at all**. If a field genuinely has no source in your schema yet,
return it blank rather than leaving it out — a dropped key inside a present
`lease` block is a contract violation the same way a dropped key in `premises`
would be; only the *whole block* is allowed to be absent.

Field mapping guess (confirm against your schema): `term_type`/`fixed_start_date`/
`fixed_end_date`/`periodic_start_date` from `Lease.termType`/`startDate`/`endDate`;
`rent_amount`/`rent_period` from wherever you already source the top-level
`current_rent`/`rent_period`; `rent_payment_day`/`first_rent_due_date` from the
lease's payment schedule if you track one; `bond_amount`/`bond_due_date` from
`Lease.bond` or your bond-lodgement record.

---

## Please confirm back

1. The exact **endpoint path + auth header** you'll expose (for both `tenancy-bundle`
   and, once built, `tenancy-search`).
2. Which **identifier(s)** you key on and how `lotId`/`tenancyId` map to your models.
3. Any field above you **can't** populate yet (so we mark it blank-by-design).
4. How you distinguish **owner vs managing agent** for the `rental_provider` field.
5. Whether `tenancy-search` is feasible against your current schema/indexes, and
   roughly how large the property list is (affects whether you need to paginate —
   today's PropertyMe adapter assumes a single-page scan at GEA's scale, ~300 active).
6. Whether/when you can add the optional `lease` block, and which of its fields
   your schema already tracks vs. would need new columns for.
