"""Creates data/entitlements.csv: synthetic user entitlements (who had access
to which feed, and when). Fixed random seed, so the result is always the same."""
import csv
import datetime as dt
import random
from pathlib import Path

PARTNERS = {
    "Broker Alpha": ["UTP", "CTA", "OPRA"],
    "Broker Beta": ["UTP", "CTA"],
    "Wealth Gamma": ["CTA", "Cboe"],
    "Crypto Delta": ["UTP"],
}


def generate(path=Path(__file__).parent / "data" / "entitlements.csv"):
    random.seed(7)
    rows = []
    for partner, feeds in PARTNERS.items():
        for i in range(random.randint(40, 90)):
            user_id = f"{partner.split()[1][:2].upper()}{i:03d}"
            professional = random.random() < 0.15
            start = dt.date(2026, 10, 1) + dt.timedelta(days=random.randint(0, 40))
            end = start + dt.timedelta(days=random.randint(5, 90))
            for feed in feeds:
                if random.random() < 0.85:
                    rows.append([partner, user_id, feed,
                                 "professional" if professional else "nonprofessional",
                                 start.isoformat(), end.isoformat()])
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["partner", "user_id", "feed", "user_type", "access_start", "access_end"])
        w.writerows(rows)
    return len(rows)


if __name__ == "__main__":
    print(f"{generate()} entitlement rows written")
