import pytest

from app import gateway
from tests.helpers_f03 import make_event, make_ticket


def test_decide_table(monkeypatch):
    # Arrange
    monkeypatch.setenv("GATEWAY_DELAY_SCALE", "1")
    cases = {"0001": (True, 2, 5), "0002": (False, 2, 5), "0003": (True, 30, 40), "0004": (False, 30, 40), "9999": (False, 2, 5)}

    for last4, (ok, lo, hi) in cases.items():
        # Act
        approved, delay = gateway.decide("400000000000" + last4)

        # Assert
        assert approved is ok
        assert lo <= delay <= hi


@pytest.mark.anyio
async def test_apply_result_only_pending(db, running_app):
    # Arrange
    event_id = await make_event(db)
    tid = await make_ticket(db, event_id, "cancelled")

    # Act
    await gateway.apply_result(tid, True)

    # Assert
    cur = await db.execute("SELECT status FROM tickets WHERE id=%s", (tid,))
    assert (await cur.fetchone())["status"] == "cancelled"


@pytest.mark.anyio
async def test_apply_result_missing_ticket_is_noop(running_app):
    # Arrange / Act
    await gateway.apply_result("tkt_nope", True)

    # Assert: no exception
