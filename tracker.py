"""Market data licensing tracker (independent case study, synthetic data).

Given a date, it:
  1. lists upcoming usage-reporting deadlines per data source,
  2. flags licenses that are inside their renewal notice window,
  3. flags partners whose redistribution authorization expired or is expiring
     while feeds are still enabled,
  4. drafts last month's usage report (users with access, by feed and user type).

Rules are simplified summaries of public exchange policies. Always confirm
against the current policy documents linked in data/reporting_rules.csv.
"""
import csv
import datetime as dt
import sys
from collections import defaultdict
from pathlib import Path

DATA = Path(__file__).parent / "data"
OUT = Path(__file__).parent / "out"

# US market holidays used for business-day logic (Nov 2026 - Feb 2027).
HOLIDAYS = {
    dt.date(2026, 11, 26),  # Thanksgiving
    dt.date(2026, 12, 25),  # Christmas
    dt.date(2027, 1, 1),    # New Year's Day
    dt.date(2027, 1, 18),   # MLK Day
    dt.date(2027, 2, 15),   # Presidents' Day
}

FEED_SOURCE = {
    "UTP": "UTP Plan (Nasdaq-listed SIP)",
    "CTA": "NYSE / CTA",
    "OPRA": "OPRA",
    "Cboe": "Cboe U.S. Equities/Options",
}


def read(name):
    if name == "entitlements.csv" and not (DATA / name).exists():
        import generate_data
        generate_data.generate()
    with open(DATA / name, newline="") as fh:
        return list(csv.DictReader(fh))


def is_business_day(d):
    return d.weekday() < 5 and d not in HOLIDAYS


def next_business_day(d):
    while not is_business_day(d):
        d += dt.timedelta(days=1)
    return d


def month_end(year, month):
    first_next = dt.date(year + month // 12, month % 12 + 1, 1)
    return first_next - dt.timedelta(days=1)


def second_to_last_business_day(year, month):
    d = month_end(year, month)
    found = 0
    while True:
        if is_business_day(d):
            found += 1
            if found == 2:
                return d
        d -= dt.timedelta(days=1)


def due_date(rule, year, month):
    """Due date for the report covering (year, month). None if not computable."""
    if rule["due_rule"] == "day15_next_month":
        ny, nm = (year + 1, 1) if month == 12 else (year, month + 1)
        d = dt.date(ny, nm, 15)
        if rule["grace"] == "next_business_day":
            d = next_business_day(d)
        return d
    if rule["due_rule"] == "second_to_last_business_day_same_month":
        return second_to_last_business_day(year, month)
    if rule["due_rule"] == "jan31":
        return dt.date(year + 1, 1, 31) if month == 12 else None
    return None


def upcoming_deadlines(today, rules, horizon_days=45):
    items = []
    periods = []
    y, m = today.year, today.month
    for back in range(-1, 3):  # previous month .. two months ahead
        mm = m - back
        yy = y
        while mm < 1:
            mm += 12
            yy -= 1
        while mm > 12:
            mm -= 12
            yy += 1
        periods.append((yy, mm))
    for rule in rules:
        if rule["due_rule"] == "jan31":
            d = dt.date(today.year + (1 if today > dt.date(today.year, 1, 31) else 0), 1, 31)
            items.append((d, rule["source"], rule["report"], "annual"))
            continue
        if rule["due_rule"] == "confirm_in_agreement":
            items.append((None, rule["source"], rule["report"], "confirm due day"))
            continue
        for yy, mm in sorted(set(periods)):
            d = due_date(rule, yy, mm)
            if d and today <= d <= today + dt.timedelta(days=horizon_days):
                label = "inventory" if rule["due_rule"].endswith("same_month") else "usage"
                items.append((d, rule["source"], rule["report"], f"{dt.date(yy, mm, 1):%b %Y} {label}"))
    return sorted(items, key=lambda x: (x[0] is None, x[0] or dt.date.max))


def renewal_alerts(today, licenses):
    alerts = []
    for lic in licenses:
        renewal = dt.date.fromisoformat(lic["renewal_date"])
        notice_by = renewal - dt.timedelta(days=int(lic["notice_days"]))
        if today >= notice_by and today <= renewal:
            alerts.append((lic["license_id"], lic["source"], lic["product"], renewal, notice_by, lic["auto_renew"]))
    return alerts


def partner_alerts(today, partners, warn_days=30):
    alerts = []
    for p in partners:
        exp = dt.date.fromisoformat(p["authorization_expires"])
        if exp < today:
            status = "EXPIRED - disable feeds or get new evidence"
        elif exp <= today + dt.timedelta(days=warn_days):
            status = f"expires in {(exp - today).days} days"
        else:
            continue
        alerts.append((p["partner"], exp, p["feeds_enabled"], status))
    return alerts


def usage_report(entitlements, year, month):
    """Users with access at any point in the month, per source, feed and user type."""
    start = dt.date(year, month, 1)
    end = month_end(year, month)
    counts = defaultdict(set)
    for e in entitlements:
        a = dt.date.fromisoformat(e["access_start"])
        b = dt.date.fromisoformat(e["access_end"])
        if a <= end and b >= start:
            key = (FEED_SOURCE[e["feed"]], e["partner"], e["feed"], e["user_type"])
            counts[key].add(e["user_id"])
    return sorted((k + (len(v),) for k, v in counts.items()))


def main(today_str=None):
    today = dt.date.fromisoformat(today_str) if today_str else dt.date.today()
    rules, licenses = read("reporting_rules.csv"), read("licenses.csv")
    partners, ents = read("partners.csv"), read("entitlements.csv")
    prev = (today.replace(day=1) - dt.timedelta(days=1))

    print(f"Market data ops check for {today:%a %d %b %Y}\n")
    print("Upcoming reporting deadlines")
    for d, src, rep, period in upcoming_deadlines(today, rules):
        when = f"{d:%a %d %b}" if d else "  ?    "
        flag = "  <-- TODAY" if d == today else ""
        print(f"  {when}  {src:<30} {rep} ({period}){flag}")

    print("\nLicenses inside renewal notice window")
    for lid, src, prod, ren, notice, auto in renewal_alerts(today, licenses):
        if auto == "no":
            print(f"  {lid} {prod:<16} ends {ren}, no auto-renew: renewal should have started by {notice}")
        else:
            print(f"  {lid} {prod:<16} auto-renews {ren}: last day to give notice was {notice}")

    print("\nPartner authorization issues")
    for name, exp, feeds, status in partner_alerts(today, partners):
        print(f"  {name:<13} feeds={feeds:<14} {status}")

    report = usage_report(ents, prev.year, prev.month)
    OUT.mkdir(exist_ok=True)
    path = OUT / f"usage_report_{prev:%Y_%m}.csv"
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["source", "partner", "feed", "user_type", "users_with_access"])
        w.writerows(report)
    print(f"\nDraft {prev:%B %Y} usage report: {path} ({len(report)} lines)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
