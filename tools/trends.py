#!/usr/bin/env python3
"""Google Trends "Trending now" (last N hours) for several countries, sports removed.

Usage: python3 tools/trends.py [--hours 24] [--geos US,GB,CA,DE,FR] [--top 25] [--json out.json]

Prints one merged list, biggest first: search volume, countries, categories, start time (UTC),
whether it is still rising, and related searches. Sports (category 17) and obvious match
queries ("x vs y", scores, line-ups) are dropped.
"""
import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request

URL = "https://trends.google.com/_/TrendsUi/data/batchexecute"
CATEGORIES = {
    1: "Autos", 2: "Beauty & Fashion", 3: "Business & Finance", 4: "Entertainment", 5: "Food & Drink",
    6: "Games", 7: "Health", 8: "Hobbies", 9: "Jobs & Education", 10: "Law & Government", 11: "Other",
    13: "Pets & Animals", 14: "Politics", 15: "Science", 16: "Shopping", 17: "Sports", 18: "Technology",
    19: "Travel & Transport", 20: "Climate",
}
SPORTS = 17
SPORTY = re.compile(
    r"\b(vs\.?|v|contre|gegen)\b|\b(score|scores|live stream|line-?ups?|highlights|kick-?off|odds|fixtures?|"
    r"standings|tabelle|classement|nfl|nba|nhl|mlb|mls|ufc|f1|grand prix|premier league|bundesliga|ligue 1|"
    r"champions league|world cup|olympi\w*|ironman|tennis|golf|marathon|fc|cf|afc|united)\b",
    re.I,
)


def fetch(geo, hours, lang="en-US"):
    req = [[["i0OFE", json.dumps([None, None, geo, 0, lang, hours, 1]), None, "generic"]]]
    body = urllib.parse.urlencode({"f.req": json.dumps(req)}).encode()
    r = urllib.request.Request(URL, data=body, headers={
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)",
    })
    raw = urllib.request.urlopen(r, timeout=40).read().decode("utf-8")
    for line in raw.splitlines():
        if line.startswith('[["wrb.fr"'):
            payload = json.loads(json.loads(line)[0][2])
            return payload[1] or []
    raise RuntimeError(f"unexpected response for {geo}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=24)
    ap.add_argument("--geos", default="US,GB,CA,DE,FR")
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--json")
    a = ap.parse_args()

    merged = {}
    for geo in a.geos.split(","):
        try:
            items = fetch(geo, a.hours)
        except Exception as e:  # keep going with the other countries
            print(f"! {geo}: {e}", file=sys.stderr)
            continue
        for it in items:
            kw, start, end, vol, rise = it[0], (it[3] or [0])[0], it[4], it[6] or 0, it[8] or 0
            cats = it[10] or []
            related = it[9] or []
            if SPORTS in cats or SPORTY.search(kw):
                continue
            key = kw.strip().lower()
            m = merged.setdefault(key, {"keyword": kw, "volume": 0, "countries": {}, "categories": set(),
                                        "start": start, "active": False, "related": []})
            m["volume"] += vol
            m["countries"][geo] = vol
            m["categories"].update(CATEGORIES.get(c, str(c)) for c in cats)
            m["start"] = min(m["start"] or start, start or m["start"])
            m["active"] = m["active"] or not end
            for q in related:
                if q.lower() != key and q not in m["related"]:
                    m["related"].append(q)

    rows = sorted(merged.values(), key=lambda m: (len(m["countries"]) > 1, m["volume"]), reverse=True)
    out = []
    for m in rows[: a.top]:
        row = {
            "keyword": m["keyword"],
            "volume": m["volume"],
            "countries": m["countries"],
            "categories": sorted(m["categories"]),
            "started_utc": time.strftime("%Y-%m-%d %H:%M", time.gmtime(m["start"])) if m["start"] else "",
            "rising": m["active"],
            "related": m["related"][:6],
        }
        out.append(row)
        geo = " ".join(f"{g}:{v:,}" for g, v in row["countries"].items())
        print(f"{row['volume']:>10,}  {row['keyword']}  [{geo}]  {', '.join(row['categories']) or '-'}"
              f"  since {row['started_utc']}{'  RISING' if row['rising'] else ''}")
        if row["related"]:
            print(f"{'':12}related: {'; '.join(row['related'])}")
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
