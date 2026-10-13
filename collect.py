#!/usr/bin/env python3
"""
Collect GitHub traffic (clones & views) for the Tatar projects and accumulate
them into an all-time total + a rolling 14-day growth figure.

Why accumulate: GitHub's traffic API only returns the LAST 14 DAYS of per-day
data. To build an "all-time" number we must fetch on a schedule and merge each
day into history.json. Days on/before BASELINE_DATE are already counted inside
BASELINE (the figures captured from the original snapshot), so all-time only
adds days strictly AFTER the baseline to avoid double counting.

Needs env var STATS_TOKEN = a GitHub token (classic 'repo' scope, or a
fine-grained token with Administration:read) that can read traffic for the repos.
Stdlib only.
"""
import os, json, sys, datetime, urllib.request, urllib.error

OWNER = "ochmunkh"
REPOS = [
    {"slug": "Tatar-Kuber",     "name": "Tatar Kuber",     "icon": "kuber"},
    {"slug": "Tatar-Kuber-Lab", "name": "Tatar Kuber Lab", "icon": "lab"},
    {"slug": "Tatar-Triage",    "name": "Tatar Triage",    "icon": "triage"},
    {"slug": "Tatar-Shield",    "name": "Tatar Shield",    "icon": "shield"},
    {"slug": "Tatar-Relay",     "name": "Tatar Relay",     "icon": "relay"},
]

# All-time totals captured from the original snapshot (baseline). Days after this
# date are added on top from live traffic data.
BASELINE_DATE = "2026-10-05"
BASELINE = {
    "Tatar-Kuber":     {"clones": 964, "cloners": 493, "views": 2442, "visitors": 340},
    "Tatar-Kuber-Lab": {"clones": 310, "cloners": 214, "views": 276,  "visitors": 75},
    "Tatar-Triage":    {"clones": 427, "cloners": 201, "views": 696,  "visitors": 70},
    "Tatar-Shield":    {"clones": 179, "cloners": 116, "views": 684,  "visitors": 92},
    "Tatar-Relay":     {"clones": 234, "cloners": 124, "views": 555,  "visitors": 34},
}

TOKEN = os.environ.get("STATS_TOKEN")
if not TOKEN:
    print("ERROR: STATS_TOKEN env var is not set.", file=sys.stderr)
    sys.exit(1)

HIST_PATH = "history.json"
DATA_PATH = "data.json"


def api(path):
    url = f"https://api.github.com/repos/{OWNER}/{path}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "tatar-stats-collector",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def main():
    history = load_json(HIST_PATH, {})
    today = datetime.date.today()
    cutoff14 = (today - datetime.timedelta(days=14)).isoformat()

    out_repos = []
    for r in REPOS:
        slug = r["slug"]
        h = history.setdefault(slug, {"clones": {}, "views": {}})

        # ---- fetch & merge daily data (API is authoritative for last 14 days) ----
        try:
            cl = api(f"{slug}/traffic/clones")
            for d in cl.get("clones", []):
                day = d["timestamp"][:10]
                h["clones"][day] = {"count": d["count"], "uniques": d["uniques"]}
        except urllib.error.HTTPError as e:
            print(f"WARN {slug} clones: HTTP {e.code}", file=sys.stderr)
        except Exception as e:
            print(f"WARN {slug} clones: {e}", file=sys.stderr)

        try:
            vw = api(f"{slug}/traffic/views")
            for d in vw.get("views", []):
                day = d["timestamp"][:10]
                h["views"][day] = {"count": d["count"], "uniques": d["uniques"]}
        except urllib.error.HTTPError as e:
            print(f"WARN {slug} views: HTTP {e.code}", file=sys.stderr)
        except Exception as e:
            print(f"WARN {slug} views: {e}", file=sys.stderr)

        b = BASELINE.get(slug, {"clones": 0, "cloners": 0, "views": 0, "visitors": 0})

        def total(metric, field, base):
            # baseline + days strictly after BASELINE_DATE
            return base + sum(v[field] for day, v in h[metric].items() if day > BASELINE_DATE)

        def growth(metric, field):
            # activity within the last 14 days
            return sum(v[field] for day, v in h[metric].items() if day >= cutoff14)

        out_repos.append({
            "name": r["name"], "slug": slug, "icon": r["icon"],
            "clones":     total("clones", "count",   b["clones"]),
            "clones_g":   growth("clones", "count"),
            "cloners":    total("clones", "uniques", b["cloners"]),
            "cloners_g":  growth("clones", "uniques"),
            "views":      total("views",  "count",   b["views"]),
            "views_g":    growth("views",  "count"),
            "visitors":   total("views",  "uniques", b["visitors"]),
            "visitors_g": growth("views",  "uniques"),
        })

    data = {
        "updated": today.isoformat(),
        "tagline": "Build Secure Mongolia",
        "repos": out_repos,
    }

    with open(HIST_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"OK updated {DATA_PATH} for {len(out_repos)} repos ({today})")


if __name__ == "__main__":
    main()
