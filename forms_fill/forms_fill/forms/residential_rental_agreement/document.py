"""GEA lease document: cover + Form 1 (RT Regs 2021 v009, Sch 1) as HTML (U3, KTD3).

Pure: context dict -> ``HtmlDocument``. Every prescribed line of Form 1 is
printed verbatim and in order (guarded by tests/test_lease_form1_compliance.py).
Values come only from the context; a blank value prints as an empty labelled
field, never a placeholder (R3). The renter signature rows keep the literal
"Signature of renter N" text with a "Dated" label below (KTD6, sign_pdf.py).
"""

from __future__ import annotations

import re
from html import escape

from ...agency import load_agency_config
from ...formspec import HtmlDocument

TITLE = "Residential Rental Agreement"
TERM_TYPES = ("fixed", "periodic")
RENT_PERIODS = ("week", "fortnight", "calendar month")
ON, OFF = "■", "□"  # Inter has these; ☐/☒ are missing from the font

CSS = """
<style>
h1 {font-size: 20pt; font-weight: 600; margin: 0 0 6pt 0;}
h2 {font-size: 11pt; font-weight: 700; margin: 14pt 0 2pt 0; padding-top: 4pt;
    border-top: 0.5pt solid #1a1c1c;}
h3 {font-size: 10pt; font-weight: 600; margin: 8pt 0 2pt 0;}
p {margin: 0 0 4pt 0;}
ul {margin: 0 0 4pt 0; padding-left: 12pt;}
li {margin: 0 0 2pt 0;}
td {font-size: 10pt;}
td.l {width: 170pt; font-size: 9pt; color: #5e5e5e;}
td.sig {padding-top: 16pt; padding-bottom: 16pt;}
.s {color: #5e5e5e; font-size: 9pt;}
.part {font-size: 13pt; font-weight: 700; margin: 20pt 0 4pt 0;}
.tick {margin: 2pt 0;}
td.keep {border: none; padding: 0;}
.cover {text-align: right;}
.cover p {margin: 0;}
</style>
"""


# Story has no break-after: avoid, but never splits a table row, so a heading
# and the block after it are wrapped in one borderless row to stay together.
_KEEP = re.compile(
    r'((?:<p class="part">[^<]*</p>)?(?:<h2>.*?</h2>)?(?:<h3>.*?</h3>)?)'
    r"(<table>.*?</table>|<p[^>]*>.*?</p>|<ul>.*?</ul>)",
    re.S,
)


def _keep_with_next(html: str) -> str:
    return _KEEP.sub(
        lambda m: f'<table class="keep"><tr><td class="keep">{m[1]}{m[2]}</td></tr></table>' if m[1] else m[0],
        html,
    )


def _v(ctx: dict, key: str) -> str:
    return escape(str(ctx.get(key) or "").strip())


def _d(ctx: dict, key: str) -> str:
    """A date as Australians read it: ISO YYYY-MM-DD prints DD/MM/YYYY; any
    other value prints exactly as given (never guessed or reformatted)."""

    value = str(ctx.get(key) or "").strip()
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", value)
    return escape(f"{m[3]}/{m[2]}/{m[1]}" if m else value)


def _row(label: str, value: str = "", cls: str = "l") -> str:
    return f'<tr><td class="{cls}">{label}</td><td>{value}</td></tr>'


def _rows(*rows: str) -> str:
    return "<table>" + "".join(rows) + "</table>"


def _tick(on: bool, label: str) -> str:
    return f'<p class="tick">{ON if on else OFF} {label}</p>'


def _addr(ctx: dict, addr: str, pc: str) -> str:
    a, p = _v(ctx, addr), _v(ctx, pc)
    return a if p and a.endswith(p) else " ".join(x for x in (a, p) if x)


def _paras(*lines: str) -> str:
    return "".join(f"<p>{ln}</p>" for ln in lines)


def _bullets(*lines: str) -> str:
    return "<ul>" + "".join(f"<li>{ln}</li>" for ln in lines) + "</ul>"


def _cover(ctx: dict, agency: str) -> str:
    renters = [_v(ctx, f"renter{i}_name") for i in range(1, 5)]
    pm = [
        _v(ctx, "agent_name"),
        f"mobile: {_v(ctx, 'agent_phone')}" if _v(ctx, "agent_phone") else "",
        f"email: {_v(ctx, 'agent_email')}" if _v(ctx, "agent_email") else "",
    ]
    block = lambda lines: "".join(f"<p>{x}</p>" for x in lines if x)  # noqa: E731
    return (
        '<div style="margin-top: 110pt;"><img src="grants-logo-bw.png" width="190"/></div>'
        '<div class="cover" style="margin-top: 110pt;">'
        f"<h1>{TITLE}</h1>"
        f'<p style="font-weight: 700; margin-top: 10pt;">{_addr(ctx, "premises_address", "premises_postcode")}</p>'
        f'<p style="font-weight: 700; margin-top: 12pt;">{escape(agency)}</p>'
        f'<div style="margin-top: 12pt;">{block(pm)}</div>'
        f'<div style="margin-top: 12pt;">{block(renters)}</div>'
        "</div>"
    )


def _part_a(ctx: dict, agency: str) -> str:
    fixed = ctx.get("term_type") == "fixed"
    periodic = ctx.get("term_type") == "periodic"
    period = ctx.get("rent_period", "")
    renters = "".join(
        f"<h3>Renter {i}</h3>"
        + _rows(
            _row("Full name of renter", _v(ctx, f"renter{i}_name")),
            _row("Current address", _addr(ctx, f"renter{i}_current_address", f"renter{i}_current_postcode")),
            _row("Phone number", _v(ctx, f"renter{i}_phone")),
            _row("Email address", _v(ctx, f"renter{i}_email")),
        )
        for i in range(1, 5)
    )
    provider_name = " / ".join(x for x in (_v(ctx, "provider_name"), _v(ctx, "provider_company_name")) if x)
    ticks = "<br/>".join(
        f"{ON if period == p else OFF} {p}" for p in RENT_PERIODS
    )
    return (
        '<p class="part">PART A—GENERAL</p>'
        "<h2>1. Date of agreement</h2>"
        + _rows(_row('This is the date the agreement is signed', _d(ctx, "agreement_date")))
        + _paras('<span class="s">If the agreement is signed by the parties on different days, the date of the agreement is the date the last person signs the agreement.</span>')
        + "<h2>2. Premises let by the rental provider</h2>"
        + _rows(_row("Address of premises", _addr(ctx, "premises_address", "premises_postcode")))
        + "<h2>3. Rental provider's details</h2>"
        + _rows(
            _row("Full name or company name of rental provider", provider_name),
            _row("Address", _addr(ctx, "provider_address", "provider_postcode")),
            _row("Phone number", _v(ctx, "provider_phone")),
            _row("ACN", _v(ctx, "provider_acn")),
            _row("Email address", _v(ctx, "provider_email")),
        )
        + "<h3>Rental provider's agent's details</h3>"
        + _rows(
            _row("Full name", escape(agency)),
            _row("Address", _v(ctx, "agent_address")),
            _row("Phone number", _v(ctx, "agent_phone")),
            _row("ACN", _v(ctx, "agent_acn")),
            _row("Email address", _v(ctx, "agent_email")),
        )
        + _paras('<span class="s">Note: The rental provider must notify the renter within 7 days if any of this information changes.</span>')
        + "<h2>4. Renter's details</h2>"
        + _paras("Each renter that is a party to the agreement must provide their details here.")
        + renters
        + "<h2>5. Length of the agreement (tick one box only)</h2>"
        + _tick(fixed, "Fixed term agreement")
        + _rows(
            _row('Start date<br/>(this is the date the agreement starts and you may move in)', _d(ctx, "fixed_start_date") if fixed else ""),
            _row("End date", _d(ctx, "fixed_end_date") if fixed else ""),
        )
        + _tick(periodic, "Periodic agreement (monthly)")
        + _rows(_row("Start date", _d(ctx, "periodic_start_date") if periodic else ""))
        + _paras('<span class="s">Note: If a fixed term agreement ends and the renter and rental provider do not enter into a new fixed term agreement, and the renter continues to occupy the premises, a periodic (e.g. month by month) residential rental agreement will be formed.</span>')
        + "<h2>6. Rent</h2>"
        + "<table><tr>"
        '<td class="s">Rent amount ($)<br/>(payable in advance)</td>'
        '<td class="s">To be paid per<br/>(tick one box only)</td>'
        '<td class="s">Day rent is to be paid<br/>(e.g. each Thursday or the 11th of each month)</td>'
        "</tr><tr>"
        f'<td>{_v(ctx, "rent_amount")}</td><td>{ticks}</td><td>{_v(ctx, "rent_payment_day")}</td>'
        "</tr></table>"
        + _rows(_row("Date first rent payment due", _d(ctx, "first_rent_due_date")))
        + "<h2>7. Bond</h2>"
        + _paras(
            "The renter has been asked to pay the bond specified below.",
            "Unless the rent is greater than $900 (per week), the maximum bond is one month's rent.",
            "In some cases, the rental provider may ask the Victorian Civil and Administrative Tribunal (VCAT) to increase this limit.",
            "The rental provider or their agent must lodge the bond with the Residential Tenancies Bond Authority (RTBA).",
            "The bond must be lodged within 10 business days after receiving payment.",
            "The RTBA will send the renter a receipt for the bond.",
            "If the renter does not receive a receipt within 15 business days from when they paid the bond, they may—",
        )
        + _bullets("email the RTBA at rtba@justice.vic.gov.au; or", "call the RTBA on 1300 137 164.")
        + _rows(
            _row("Bond amount ($)", _v(ctx, "bond_amount")),
            _row("Date bond payment due", _d(ctx, "bond_due_date")),
        )
    )


def _yes_no(label: str = "") -> str:
    lead = f"<h3>{label}</h3>" if label else ""
    return lead + _rows(
        _row(f"{OFF} Yes", '<span class="s">Email address, mobile phone number or other electronic contact details</span>'),
        _row(f"{OFF} No"),
    )


def _part_b(ctx: dict) -> str:
    methods = (
        "direct debit", "bank deposit", "cash", "cheque", "money order", "BPAY",
        "other electronic form of payment, including Centrepay",
    )
    renters = "".join(_yes_no(f"Renter {i}") for i in range(1, 5))
    return (
        '<p class="part">PART B—STANDARD TERMS</p>'
        "<h2>8. Rental provider's preferred methods of payment</h2>"
        + _paras(
            '<span class="s">Note: The rental provider must permit a fee-free (other than the renter\'s own bank fees) payment method and must allow the renter to use Centrepay or another form of electronic funds transfer.</span>',
            '<span class="s">Note: The renter is entitled to receive a receipt from the rental provider confirming payment of rent.</span>',
            '<span class="s">(rental provider to tick available methods of rent payment)</span>',
        )
        + "".join(_tick(False, m) for m in methods)
        + _rows(_row("Payment details"))
        + "<h2>9. Service of notices and other documents by electronic methods</h2>"
        + _paras(
            "Electronic service of documents must be in accordance with the requirements of the Electronic Transactions (Victoria) Act 2000.",
            "Just because someone responds to an email or other electronic communications does not mean they have consented to the service of notices and other documents by electronic methods.",
            "The rental provider and renter must notify the other party in writing if they no longer wish to receive notices or other documents by electronic methods.",
            "The rental provider and renter must immediately notify the other party in writing if their contact details change.",
        )
        + "<h3>9.1 Does the rental provider agree to the service of notices and other documents by electronic methods such as email?</h3>"
        + _paras(
            "The rental provider must complete this section before giving the agreement to the renter.",
            '<span class="s">(rental provider to tick as appropriate)</span>',
        )
        + _yes_no()
        + "<h3>9.2 Does the renter agree to the service of notices and other documents by electronic methods such as email?</h3>"
        + _paras(
            '<span class="s">(renter to tick as appropriate)</span>',
            '<span class="s">(The option to consent should be provided to each renter who is a party to the agreement)</span>',
        )
        + renters
        + "<h2>10. Urgent repairs</h2>"
        + _paras(
            "The rental provider must ensure that the rental property is provided and maintained in good repair.",
            "If there is a need for an urgent repair, the renter should notify the rental provider in writing.",
            "For further information on seeking repairs see Part D (below).",
        )
        + "<h3>Details of person the renter should contact for an urgent repair</h3>"
        + _paras('<span class="s">(rental provider to insert details)</span>')
        + _rows(
            _row("Emergency contact name", _v(ctx, "emergency_contact_name")),
            _row("Emergency contact phone number", _v(ctx, "emergency_phone")),
            _row("Emergency contact email address", _v(ctx, "emergency_email")),
        )
        + "<h2>11. Professional cleaning</h2>"
        + _paras("The rental provider must not require the renter to arrange professional cleaning or cleaning to a professional standard at the end of the tenancy unless—")
        + _bullets(
            "professional cleaning or cleaning to a professional standard was carried out to the rented premises immediately before the start of the tenancy and the renter was advised that professional cleaning or cleaning to a professional standard had been carried out to those premises immediately before the start of the tenancy; or",
            "professional cleaning or cleaning to a professional standard is required to restore the rented premises to the same condition they were in immediately before the start of the tenancy, having regard to the condition report and taking into account fair wear and tear.",
        )
        + _paras("The renter must have all or part of the rented premises professionally cleaned, or pay the cost of having all or part of the rented premises professional cleaned, if professional cleaning becomes required to restore the premises to the condition they were in immediately before the start of the tenancy, having regard to the condition report and taking into account fair wear and tear.")
        + "<h2>12. Owners corporation</h2>"
        + _paras(
            "Do owners corporation rules apply to the premises?",
            '<span class="s">(rental provider to tick as appropriate)</span>',
        )
        + _tick(False, "No") + _tick(False, "Yes")
        + _paras("If yes, the rental provider must attach a copy of the rules to this agreement.")
        + "<h2>13. Condition report</h2>"
        + _paras(
            "The renter must be given 2 copies of the condition report (or one emailed copy) on or before the date the renter moves into the rented premises.",
            '<span class="s">(rental provider to tick as appropriate)</span>',
        )
        + _tick(False, "The condition report has been provided.")
        + _tick(False, "The condition report will be provided to the renter on or before the date the agreement starts.")
    )


def _part_c() -> str:
    return (
        '<p class="part">PART C—SAFETY-RELATED ACTIVITIES</p>'
        "<h2>14. Electrical safety checks</h2>"
        + _paras(
            "(a) The rental provider must ensure an electrical safety check of all electrical installations, appliances and fittings provided by a rental provider in the rented premises is conducted every 2 years by a licensed or registered electrician and must provide the renter with the date of the most recent safety check, in writing, on request of the renter.",
            "(b) If an electrical safety check of the rented premises has not been conducted within the last 2 years at the time the renter occupies the premises, the rental provider must arrange an electrical safety check as soon as practicable.",
        )
        + "<h2>15. Gas safety activities</h2>"
        + _paras(
            '<span class="s">This safety-related activity only applies if the rented premises contains any appliances, fixtures or fittings which use or supply gas.</span>',
            "(a) The rental provider must ensure that a gas safety check of all gas installations and fittings in the rented premises is conducted every 2 years by a licensed or registered gasfitter and must provide the renter with the date of the most recent safety check, in writing, on request of the renter.",
            "(b) If a gas safety check has not been conducted within the last 2 years at the time the renter occupies the premises, the rental provider must arrange a gas safety check as soon as practicable.",
        )
        + "<h2>17. Swimming pool barrier safety activities</h2>"
        + _paras(
            '<span class="s">These safety-related activities only apply if the rented premises contains a swimming pool.</span>',
            "(a) The rental provider must ensure that the swimming pool barrier is maintained in good repair.",
            "(b) The renter must give written notice to the rental provider as soon as practicable after becoming aware that the swimming pool barrier is not in working order.",
            "(c) The rental provider must arrange for a swimming pool barrier to be immediately repaired or replaced as an urgent repair if they are notified by the renter that it is not in working order.",
            "(d) The rental provider must provide the renter with a copy of the most recent certificate of swimming pool barrier compliance issued under the Building Act 1993 on the request of the renter.",
        )
        + "<h2>18. Relocatable swimming pool safety activities</h2>"
        + _paras(
            '<span class="s">These safety-related activities only apply if a relocatable swimming pool is erected, or is intended to be erected, on the rented premises.</span>',
            "(a) The renter must not erect a relocatable swimming pool without giving written notice to the rental provider before erecting the pool.",
            "(b) The renter must obtain any necessary approvals before erecting a relocatable swimming pool.",
            '<span class="s">Note: Regulations made under Building Act 1993 apply to any person erecting a relocatable swimming pool.</span>',
            '<span class="s">This safety-related activity only applies to swimming pools or spas that hold water deeper than 300 mm.</span>',
        )
        + "<h2>19. Bushfire prone area activities</h2>"
        + _paras(
            '<span class="s">This safety-related activity only applies if the rented premises is in a bushfire prone area and is required to have a water tank for bushfire safety.</span>',
            "If the rented premises is in a designated bushfire prone area under section 192A of the Building Act 1993 and a water tank is required for firefighting purposes, the rental provider must ensure the water tank and any connected infrastructure is maintained in good repair as required.",
            "The water tank must be full and clean at the commencement of the agreement.",
        )
    )


def _part_d() -> str:
    return (
        '<p class="part">PART D—RIGHTS AND OBLIGATIONS</p>'
        + _paras(
            "This is a summary of selected rights and obligations of renters and rental providers under the Act.",
            "Any reference to VCAT refers to the Victorian Civil and Administrative Tribunal.",
            "For more information, visit consumer.vic.gov.au/renting.",
        )
        + "<h2>20. Use of the premises</h2>"
        + _paras("The renter—")
        + _bullets(
            "is entitled to quiet enjoyment of the premises. The rental provider may only enter the premises in accordance with the Act; and",
            "must not use the premises for illegal purposes; and",
            "must not cause a nuisance or interfere with the reasonable peace, comfort or privacy of neighbours; and",
            "must avoid damaging the premises and common areas. Common areas include hallways, driveways, gardens and stairwells. Where damage occurs, the renter must notify the rental provider in writing; and",
            "must keep the premises reasonably clean.",
        )
        + "<h2>21. Condition of the premises</h2>"
        + _paras("The rental provider—")
        + _bullets(
            "must ensure that the premises comply with the rental minimum standards, and is vacant and reasonably clean when the renter moves in; and",
            "must maintain the premises in good repair and in a fit condition for occupation; and",
            "agrees to do all the safety-related maintenance and repair activities set out in Part C of the Agreement.",
        )
        + _paras("The renter must follow all safety-related activities set out in Part C of the agreement and not remove, deactivate or otherwise interfere with the operation of prescribed safety devices on the premises.")
        + "<h2>22. Modifications</h2>"
        + _paras("The renter—")
        + _bullets(
            "may make some modifications without seeking the rental provider's consent. These modifications are listed on the Consumer Affairs Victoria website; and",
            "must seek the rental provider's consent before installing any other fixtures or additions; and",
            "may apply to VCAT if they believe that the rental provider has unreasonably refused consent for a modification mentioned in the Act; and",
            "at the end of the agreement, must restore the premises to the condition it was in before they moved in (excluding fair wear and tear). This includes removing all modifications, unless the parties agree they do not need to be removed.",
        )
        + _paras(
            "The rental provider must not unreasonably refuse consent for certain modifications.",
            "A list of the modifications that the rental provider cannot unreasonably refuse consent for is available on the Consumer Affairs Victoria website consumer.vic.gov.au/renting.",
        )
        + "<h2>23. Locks</h2>"
        + _paras("The rental provider must ensure the premises—")
        + _bullets(
            "has locks to secure all windows capable of having a lock; and",
            "has deadlocks (a deadlock is a deadlatch with at least one cylinder) for external doors that are able to be secured with a functioning deadlock; and",
            "meets the rental minimum standards for locks and window locks.",
        )
        + _paras("External doors which are not able to be secured with a functioning deadlock must at least be fitted with a locking device that—")
        + _bullets(
            "is operated by a key from the outside; and",
            "may be unlocked from the inside with or without a key.",
        )
        + _paras(
            "The renter must obtain consent from the rental provider to change a lock in the master key system.",
            "The rental provider must not unreasonably refuse consent for a renter seeking to change a lock in the master key system.",
            "The rental provider must not give a key to a person excluded from the premises under—",
        )
        + _bullets(
            "a family violence intervention order; or",
            "a family violence safety notice; or",
            "a recognised non-local DVO; or",
            "a personal safety intervention order.",
        )
        + "<h2>24. Repairs</h2>"
        + _paras("Only a suitably qualified person may do repairs—both urgent and non-urgent.")
        + "<h2>25. Urgent repairs</h2>"
        + _paras(
            "Section 3(1) of the Act defines urgent repairs. Refer to the Consumer Affairs Victoria website for the full list of urgent repairs and for more information, visit consumer.vic.gov.au/urgentrepairs.",
            "Urgent repairs include failure or breakdown of any essential service or appliance provided for hot water, cooking, heating or laundering supplied by the rental provider.",
            "The rental provider must carry out urgent repairs after being notified.",
            "A renter may arrange for urgent repairs to be done if the renter has taken reasonable steps to arrange for the rental provider to immediately do the repairs and the rental provider has not carried out the repairs.",
            "If the renter has arranged for urgent repairs, the renter may be reimbursed directly by the rental provider for the reasonable cost of repairs up to $2500.",
            "The renter may apply to VCAT for an order requiring the rental provider to carry out urgent repairs if—",
            "(a) the renter cannot meet the cost of the repairs; or",
            "(b) the cost of repairs is more than $2500; or",
            "(c) the rental provider refuses to pay the cost of repairs if it is carried out by the renter.",
        )
        + "<h2>26. Non-urgent repairs</h2>"
        + _paras("The renter must notify the rental provider, in writing, as soon as practicable of—")
        + _bullets(
            "damage to the premises; and",
            "a breakdown of facilities, fixtures, furniture or equipment supplied by the rental provider.",
        )
        + _paras(
            "The rental provider must carry out non-urgent repairs in a reasonable time.",
            "The renter may apply to VCAT for an order requiring the rental provider to do the repairs if the rental provider has not carried out the repairs within 14 days of receiving notice of the need for repair.",
        )
        + "<h2>27. Assignment or sub-letting</h2>"
        + _paras(
            "The renter must not assign (transfer to another person) or sub-let the whole or any part of the premises without the written consent of the rental provider.",
            "The rental provider may give the renter notice to vacate if the renter assigns or sub-lets the premises without consent.",
            "The rental provider—",
        )
        + _bullets(
            "cannot unreasonably withhold consent to assign or sub-let the premises; and",
            "must not demand or receive a fee or payment for consent, other than any reasonable expenses incurred by the assignment.",
        )
        + "<h2>28. Rent</h2>"
        + _paras(
            "The rental provider must give the renter at least 90 days written notice of a proposed rent increase.",
            "The rent cannot be increased more than once every 12 months.",
            "The rental provider must not increase the rent under a fixed term agreement unless the agreement provides for an increase by specifying the amount of increase or the method of calculating the rent increase.",
        )
        + "<h2>29. Access and entry</h2>"
        + _paras("The rental provider may enter the premises—")
        + _bullets(
            "at any time, if the renter has agreed within the last 7 days; and",
            "to do an inspection, but not more than once every 6 months; and",
            "to comply with the rental provider's duties under the Act; and",
            "to show the premises or conduct an open inspection to sell, rent or value the premises; and",
            "to take images or video for advertising a property that is for sale or rent; and",
            "if they believe the renter has failed to follow their duties under the Act; and",
            "to do a pre-termination inspection where the renter has applied to have the agreement terminated because of family violence or personal violence.",
        )
        + _paras(
            "The renter must allow entry to the premises where the rental provider has followed proper procedure.",
            "The renter is entitled to a set amount of compensation for each sales inspection.",
        )
        + "<h2>30. Pets</h2>"
        + _paras(
            "The renter must seek consent from the rental provider before keeping a pet on the premises.",
            "The rental provider must not unreasonably refuse a request to keep a pet.",
        )
        + "<h2>30A. Smoke alarms</h2>"
        + _paras("(a) A residential rental provider must ensure that any smoke alarm installed in rented premises is—")
        + "".join(
            f'<p style="margin-left: 14pt;">{x}</p>'
            for x in (
                "(i) correctly installed and in working condition; and",
                "(ii) fitted with batteries or replacement batteries; and",
                "(iii) tested at least once every 12 months in accordance with any instructions by the manufacturer of the smoke alarm.",
            )
        )
        + _paras(
            "(b) If a smoke alarm installed in the rented premises does not meet the requirements set out in paragraph (a), the renter may issue a request to the residential rental provider for urgent repairs to the smoke alarm in accordance with section 72AA of the Act.",
            "(c) On receiving notice from the renter under paragraph (b), the residential rental provider or the provider's agent must immediately arrange for the repairs to be carried out.",
            "(d) Any testing, repair or replacement of a smoke alarm that is powered by a mains electricity supply must be undertaken by a suitably qualified person.",
        )
    )


def _part_e(ctx: dict) -> str:
    renters = "".join(
        f'<h3>Renter {i}</h3>'
        + _rows(
            _row("Name", _v(ctx, f"renter{i}_name")),
            _row(f"Signature of renter {i}", "", "l sig"),
            _row("Dated"),
        )
        for i in range(1, 5)
    )
    return (
        '<p class="part" style="page-break-before: always;">PART E—ADDITIONAL TERMS</p>'
        "<h2>31. Additional terms (if any)</h2>"
        + _paras(
            "List any additional terms to this agreement. The terms listed must not exclude, restrict or modify any of the rights and duties included in the Act.",
            "Additional terms must also comply with the Australian Consumer Law (Victoria). For example, they cannot be unfair terms, which will have no effect.",
            "Contact Consumer Affairs Victoria on 1300 558 181 for further information or visit consumer.vic.gov.au/products-and-services/business-practices/contracts/unfair-contract-terms.",
        )
        + '<table><tr><td style="height: 120pt;"></td></tr></table>'
        + _paras('<span class="s">Note: If you need extra space, attach a separate sheet. Both the rental provider and renter should sign and date all attachments.</span>')
        + '<h2 style="page-break-before: always;">32. Signatures</h2>'
        + _paras(
            "This agreement is made under the Act.",
            "Before signing you must read Part D—Rights and Obligations in this form which outlines your rights and obligations.",
        )
        + "<h3>Rental provider</h3>"
        + _rows(_row("Signature", "", "l sig"), _row("Dated"))
        + renters
        + _paras('<span class="s">Note: Each renter who is a party to the agreement must sign and date here. If there are more than 4 renters, include details on an extra page.</span>')
    )


def build_html(ctx: dict[str, str]) -> HtmlDocument:
    agency = str(load_agency_config().get("agency", {}).get("name") or "")
    head = (
        '<div style="page-break-before: always;">'
        '<p class="s">FORM 1</p>'
        '<p class="s">Residential Tenancies Act 1997</p>'
        '<p class="s">(Section 26(1))</p>'
        '<p class="s">(Regulation 10(1))</p>'
        "<h1>RESIDENTIAL RENTAL AGREEMENT OF NO MORE THAN 5 YEARS</h1>"
        + _paras(
            "This agreement is between the residential rental provider (rental provider) and the renter listed on this form.",
            "Rental providers must use this form for a fixed term residential rental agreement of no more than 5 years or a periodic residential rental agreement in writing.",
        )
        + "</div>"
    )
    html = (
        CSS
        + _cover(ctx, agency)
        + head
        + _keep_with_next(_part_a(ctx, agency) + _part_b(ctx) + _part_c() + _part_d() + _part_e(ctx))
    )
    return HtmlDocument(
        html=html,
        title=TITLE,
        footer_left=" ".join(
            x for x in (str(ctx.get("premises_address") or ""), str(ctx.get("premises_postcode") or "")) if x
        ),
    )
