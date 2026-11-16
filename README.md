# Market data licensing tracker

A small tool I built to understand the operations side of market data: usage reporting deadlines, license renewals and partner authorizations.

**Independent case study.** The deadlines are real exchange rules applied to the real calendar. The partners ("Example Broker A" to "D"), licenses and users are made up, just to show how the alerts work. The reporting rules are short summaries of public exchange policies (links in `data/reporting_rules.csv`). Always confirm them against the current documents. Rules checked in November 2026 (UTP Data Policies published October 2026; the NYSE/CTA rule comes from the CTA Exhibit A, which has no date).

## What it does

Run it for any date:

```
python3 tracker.py 2026-11-16
```

It prints:

1. **Upcoming reporting deadlines** for each data source. It handles the rules that are easy to miss:
   - UTP: due the 15th of the next month, and a weekend or holiday rolls to the next business day.
   - Nasdaq and Cboe: due the 15th of the next month.
   - NYSE / CTA: the inventory report is due the second-to-last business day of the *same* month, so before the month ends.
   - NYSE non-display: no monthly report, but an annual declaration by January 31.
   - OPRA: monthly. The exact day comes from the OPRA agreement, so the tool asks you to confirm it.
2. **Licenses inside their renewal notice window**, so nothing lapses.
3. **Partners whose redistribution authorization expired or is about to expire** while their feeds are still on.
4. **A draft usage report for last month** (`out/usage_report_YYYY_MM.csv`): users with access during the month, by source, partner, feed and professional/non-professional.

`render.py` makes the one-page summary in `out/ops_check.png` (needs `matplotlib`). `tracker.py` uses only the Python standard library.

## Tests

```
python3 -m pytest -q tests
```

The tests cover the weekend roll for UTP, the NYSE second-to-last business day, the deadlines for 16 Nov 2026, expired partner flags and the monthly user count.

## Files

- `data/reporting_rules.csv`: reporting rule per source, with the policy link
- `data/licenses.csv`: synthetic licenses with renewal dates and notice periods
- `data/partners.csv`: synthetic broker partners, enabled feeds and when their redistribution authorization expires
- `generate_data.py`: creates `data/entitlements.csv`, the synthetic user entitlements (who had access to which feed, and when). `tracker.py` runs it automatically the first time.
