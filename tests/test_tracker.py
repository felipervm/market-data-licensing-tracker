import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import tracker as t


def test_utp_rolls_weekend_to_next_business_day():
    rule = {"due_rule": "day15_next_month", "grace": "next_business_day"}
    # Oct 2026 report: Nov 15 2026 is a Sunday -> Monday Nov 16
    assert t.due_date(rule, 2026, 10) == dt.date(2026, 11, 16)


def test_cboe_has_no_grace():
    rule = {"due_rule": "day15_next_month", "grace": "none"}
    assert t.due_date(rule, 2026, 10) == dt.date(2026, 11, 15)


def test_nyse_second_to_last_business_day_skips_weekend():
    # Nov 2026: last business day Mon 30, second to last Fri 27
    assert t.second_to_last_business_day(2026, 11) == dt.date(2026, 11, 27)
    # Dec 2026: Thu 31 last, Wed 30 second to last
    assert t.second_to_last_business_day(2026, 12) == dt.date(2026, 12, 30)


def test_expired_partner_is_flagged():
    partners = [{"partner": "X", "authorization_expires": "2026-11-10", "feeds_enabled": "UTP"}]
    alerts = t.partner_alerts(dt.date(2026, 11, 16), partners)
    assert alerts and alerts[0][3].startswith("EXPIRED")


def test_usage_counts_users_with_any_access_in_month():
    ents = [
        {"partner": "P", "user_id": "a", "feed": "UTP", "user_type": "nonprofessional", "access_start": "2026-09-01", "access_end": "2026-10-01"},
        {"partner": "P", "user_id": "b", "feed": "UTP", "user_type": "nonprofessional", "access_start": "2026-10-20", "access_end": "2026-12-01"},
        {"partner": "P", "user_id": "c", "feed": "UTP", "user_type": "nonprofessional", "access_start": "2026-11-02", "access_end": "2026-12-01"},
    ]
    rows = t.usage_report(ents, 2026, 10)
    assert rows == [("UTP Plan (Nasdaq-listed SIP)", "P", "UTP", "nonprofessional", 2)]


def test_deadlines_for_16_nov_2026():
    rules = t.read("reporting_rules.csv")
    items = t.upcoming_deadlines(dt.date(2026, 11, 16), rules)
    dated = [(d, src) for d, src, _, _ in items if d]
    assert dated[0] == (dt.date(2026, 11, 16), "UTP Plan (Nasdaq-listed SIP)")
    assert (dt.date(2026, 11, 27), "NYSE / CTA") in dated
    assert (dt.date(2026, 12, 15), "Cboe U.S. Equities/Options") in dated
    assert any(d is None and src == "OPRA" for d, src, _, _ in items)
