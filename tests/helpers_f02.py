from datetime import datetime, timedelta

FUT = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%dT21:00")
PAST = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT21:00")


def form(**over):
    return {"name": "Jazz no Porão", "starts_at": FUT, "venue": "Bar do Zé", "capacity": "2", "price": "100,00", **over}


async def create(client, **over):
    r = await client.post("/org/events/new", data=form(**over))
    assert r.status_code == 303
    return r.headers["location"].rsplit("/", 1)[1]
