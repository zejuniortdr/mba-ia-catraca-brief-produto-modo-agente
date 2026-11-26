import pytest


@pytest.mark.anyio
async def test_healthz_ok(client):
    # Act
    r = await client.get("/healthz")

    # Assert
    assert r.status_code == 200
    assert r.json() == {"ok": True}
