import pytest


@pytest.mark.anyio
async def test_visitor_org_redirects_login(client):
    # Act
    r = await client.get("/org/events")

    # Assert
    assert r.status_code == 303 and r.headers["location"] == "/login"


@pytest.mark.anyio
async def test_participant_org_forbidden(participant):
    # Act
    r = await participant.get("/org/events")

    # Assert
    assert r.status_code == 403
    assert "Acesso restrito a organizadores" in r.text


@pytest.mark.anyio
async def test_organizer_org_ok(org_a):
    # Act
    r = await org_a.get("/org/events")

    # Assert
    assert r.status_code == 200
