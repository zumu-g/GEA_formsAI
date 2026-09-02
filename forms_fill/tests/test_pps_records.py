"""Tests for PPS record lifecycle (U3)."""

import os
from datetime import datetime, timedelta, timezone
import tempfile
import pytest

from forms_fill import accounts


@pytest.fixture(autouse=True)
def temp_db():
    """Use a temp database for each test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["FORMS_DATA_DIR"] = tmpdir
        accounts.init_db()
        yield


def test_pps_record_create():
    """Create a new PPS record."""
    record_id = accounts.save_pps_record(
        agent_id=1,
        record_id=None,
        address="123 Main St, VIC 3000",
        state="draft",
        sale_method="private sale",
    )
    assert record_id is not None
    assert isinstance(record_id, int)

    # Fetch and verify
    record = accounts.get_pps_record(record_id, agent_id=1)
    assert record is not None
    assert record["address"] == "123 Main St, VIC 3000"
    assert record["state"] == "draft"


def test_pps_record_update():
    """Update a PPS record (e.g., add sale price)."""
    record_id = accounts.save_pps_record(
        agent_id=1,
        record_id=None,
        address="123 Main St, VIC 3000",
    )

    now = datetime.now(timezone.utc).isoformat()
    success = accounts.update_pps_record(
        record_id, agent_id=1, unconditional_at=now, sale_price="500000"
    )
    assert success is True

    record = accounts.get_pps_record(record_id, agent_id=1)
    assert record["sale_price"] == "500000"
    assert record["unconditional_at"] == now


def test_pps_record_deadline_price_update():
    """Price update deadline is 7 days after unconditional."""
    record_id = accounts.save_pps_record(
        agent_id=1,
        record_id=None,
        address="123 Main St, VIC 3000",
    )

    now = datetime.now(timezone.utc)
    unconditional = now.isoformat()
    accounts.update_pps_record(record_id, agent_id=1, unconditional_at=unconditional)

    record = accounts.get_pps_record(record_id, agent_id=1)
    due = datetime.fromisoformat(record["price_update_due"])
    expected = now + timedelta(days=7)
    # Allow 1 second tolerance for timing
    assert abs((due - expected).total_seconds()) < 1


def test_pps_record_deadline_reserve():
    """Reserve deadline is 7 days before auction."""
    past = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()
    record_id = accounts.save_pps_record(
        agent_id=1,
        record_id=None,
        address="123 Main St, VIC 3000",
        sale_method="auction",
        auction_date=past,
    )

    record = accounts.get_pps_record(record_id, agent_id=1)
    due = datetime.fromisoformat(record["reserve_due"])
    auction = datetime.fromisoformat(past)
    expected = auction - timedelta(days=7)
    assert abs((due - expected).total_seconds()) < 1


def test_pps_record_list_agent_scoped():
    """List records by agent."""
    record_id_1 = accounts.save_pps_record(
        agent_id=1, record_id=None, address="123 Main St"
    )
    record_id_2 = accounts.save_pps_record(
        agent_id=2, record_id=None, address="456 Oak Ave"
    )

    records_1 = accounts.list_pps_records(agent_id=1)
    assert len(records_1) == 1
    assert records_1[0]["id"] == record_id_1

    records_2 = accounts.list_pps_records(agent_id=2)
    assert len(records_2) == 1
    assert records_2[0]["id"] == record_id_2


def test_pps_record_public_id():
    """Record has a unique public_id for unauthenticated access."""
    record_id = accounts.save_pps_record(
        agent_id=1, record_id=None, address="123 Main St"
    )
    record = accounts.get_pps_record(record_id, agent_id=1)
    public_id = record["public_id"]

    # Fetch by public_id without auth
    public_record = accounts.get_pps_record_by_public_id(public_id)
    assert public_record is not None
    assert public_record["id"] == record_id
    assert public_record["address"] == "123 Main St"


def test_pps_record_public_until_18_months():
    """public_until is 18 months after unconditional date."""
    record_id = accounts.save_pps_record(
        agent_id=1, record_id=None, address="123 Main St"
    )

    now = datetime.now(timezone.utc)
    unconditional = now.isoformat()
    accounts.update_pps_record(record_id, agent_id=1, unconditional_at=unconditional)

    record = accounts.get_pps_record(record_id, agent_id=1)
    public_until = datetime.fromisoformat(record["public_until"])
    expected = now + timedelta(days=365 + 182)  # ~18 months
    # Allow 1 second tolerance
    assert abs((public_until - expected).total_seconds()) < 1
