#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_ad_metrics.py

Pulls lifetime spend / impressions / clicks for a single Meta Ads campaign
("קמפיין יהב-אליאס", in Rachel's ad account) from the Marketing API, and
writes them to ad_metrics.json in the repo root.

dashboard.html fetches this static JSON file client-side (same-origin, no
API token exposed to the public page) to fill in the "Spend / Impressions /
Clicks" KPIs in the ad-campaign-funnel section, replacing the old manual
Google-Sheet entry.

Run via GitHub Actions on a schedule (see .github/workflows/update-ad-metrics.yml).
Requires the META_ACCESS_TOKEN environment variable (a Meta System User token
with read access to the ad account below).
"""

import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

AD_ACCOUNT_ID = "1362031111389290"  # רחל
CAMPAIGN_ID = "120250022352280245"  # קמפיין יהב-אליאס
API_VERSION = "v21.0"
GRAPH_URL = f"https://graph.facebook.com/{API_VERSION}"

ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "")
OUT_FILE = "ad_metrics.json"


def fetch_campaign_lifetime_stats() -> dict:
    """שולף spend/impressions/clicks מצטברים (כל הזמן) עבור הקמפיין הבודד."""
    url = f"{GRAPH_URL}/act_{AD_ACCOUNT_ID}/insights"
    params = {
        "level": "campaign",
        "date_preset": "maximum",
        "fields": "campaign_id,spend,impressions,clicks",
        "filtering": json.dumps([
            {"field": "campaign.id", "operator": "IN", "value": [CAMPAIGN_ID]}
        ]),
        "access_token": ACCESS_TOKEN,
    }
    resp = requests.get(url, params=params, timeout=30)
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"Meta API error: {data['error']}")

    rows = data.get("data", [])
    if not rows:
        # אין עדיין נתונים (למשל קמפיין חדש) - מחזירים אפסים במקום לקרוס.
        return {"spend": 0.0, "impressions": 0, "clicks": 0}

    row = rows[0]
    return {
        "spend": round(float(row.get("spend", 0) or 0), 2),
        "impressions": int(row.get("impressions", 0) or 0),
        "clicks": int(row.get("clicks", 0) or 0),
    }


def main() -> None:
    if not ACCESS_TOKEN:
        print("META_ACCESS_TOKEN לא מוגדר", file=sys.stderr)
        sys.exit(1)

    stats = fetch_campaign_lifetime_stats()
    stats["updated_at"] = datetime.now(ZoneInfo("Asia/Jerusalem")).strftime("%d/%m/%Y %H:%M")

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"{OUT_FILE} נוצר: {stats}")


if __name__ == "__main__":
    main()
