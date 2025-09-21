from __future__ import annotations

from app.services.cbr import get_effective_rates, parse_cbr_xml


CBR_SAMPLE = """<ValCurs Date=\"06.09.2025\" name=\"Foreign Currency Market\">\n<Valute><CharCode>USD</CharCode><VunitRate>81,5556</VunitRate></Valute>\n<Valute><CharCode>EUR</CharCode><VunitRate>95,4792</VunitRate></Valute>\n<Valute><CharCode>JPY</CharCode><VunitRate>0,550271</VunitRate></Valute>\n<Valute><CharCode>CNY</CharCode><VunitRate>11,3884</VunitRate></Valute>\n<Valute><CharCode>AED</CharCode><VunitRate>22,2071</VunitRate></Valute>\n</ValCurs>"""  # noqa: E501


def test_parse_cbr_xml_basic():
    rates = parse_cbr_xml(CBR_SAMPLE)
    assert rates["USD_RUB"] == 81.5556
    assert rates["EUR_RUB"] == 95.4792
    assert rates["JPY_RUB"] == 0.550271
    assert rates["CNY_RUB"] == 11.3884
    assert rates["AED_RUB"] == 22.2071


def test_get_effective_rates_monkeypatch(monkeypatch):
    # Base static config
    base = {"currencies": {"USD_RUB": 90.0, "EUR_RUB": 100.0, "JPY_RUB": 0.60, "CNY_RUB": 12.0}}

    def fake_fetch():
        return {"USD_RUB": 81.5, "EUR_RUB": 95.4}

    monkeypatch.setattr("app.services.cbr.fetch_cbr_rates", lambda : fake_fetch())
    merged = get_effective_rates(base)
    assert merged["currencies"]["USD_RUB"] == 81.5
    assert merged["currencies"]["EUR_RUB"] == 95.4
    # Unchanged codes remain
    assert merged["currencies"]["JPY_RUB"] == 0.60
    assert merged.get("live_source") == "cbr"
