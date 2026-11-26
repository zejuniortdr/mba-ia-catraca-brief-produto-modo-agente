from datetime import datetime, timedelta, timezone

from app.events import parse_event_form
from app.web import format_brl

TZ = timezone(timedelta(hours=-3))
NOW = datetime(2026, 11, 1, 12, 0, tzinfo=TZ)
BASE = {"name": "Jazz", "venue": "Bar", "starts_at": "2026-12-05T21:00", "capacity": "10", "price": "100,00"}


def parse(**over):
    return parse_event_form({**BASE, **over}, NOW)


def test_parse_valid():
    data, errors = parse()

    assert errors == [] and data["price_cents"] == 10000 and data["capacity"] == 10


def test_parse_price_variants():
    results = {p: parse(price=p)[0]["price_cents"] for p in ("100", "100.00", "150,50")}

    assert results == {"100": 10000, "100.00": 10000, "150,50": 15050}


def test_capacity_zero_rejected():
    data, errors = parse(capacity="0")

    assert data is None and errors == ["Lotação deve ser um inteiro maior ou igual a 1"]


def test_price_zero_rejected():
    data, errors = parse(price="0")

    assert data is None and errors == ["Preço deve ser maior que zero"]


def test_past_date_rejected():
    _, errors = parse(starts_at="2026-10-01T21:00")

    assert errors == ["Data de início precisa estar no futuro"]


def test_missing_name_rejected():
    _, errors = parse(name=" ")

    assert errors == ["Nome é obrigatório"]


def test_starts_at_offset_minus3():
    data, _ = parse()

    assert data["starts_at"] == datetime(2026, 12, 5, 21, 0, tzinfo=TZ)


def test_format_brl():
    assert format_brl(10000) == "R$ 100,00" and format_brl(35000) == "R$ 350,00"
