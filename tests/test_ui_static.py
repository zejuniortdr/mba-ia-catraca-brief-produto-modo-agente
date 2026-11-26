import pytest


@pytest.mark.anyio
async def test_stylesheet_served_and_linked(client):
    # Act
    css = await client.get("/static/style.css")
    home = await client.get("/")

    # Assert
    assert css.status_code == 200
    assert "text/css" in css.headers["content-type"]
    assert '<link rel="stylesheet" href="/static/style.css">' in home.text
