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

## Please confirm back

1. The exact **endpoint path + auth header** you'll expose.
2. Which **identifier(s)** you key on and how `lotId`/`tenancyId` map to your models.
3. Any field above you **can't** populate yet (so we mark it blank-by-design).
4. How you distinguish **owner vs managing agent** for the `rental_provider` field.
