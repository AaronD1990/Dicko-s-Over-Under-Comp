#!/usr/bin/env python3
"""Refresh data/standings.json with every NBA team's current wins and losses.

Source: ESPN's public standings feed. The script refuses to write anything unless
the data passes all checks, so a bad fetch can never wipe out good standings.

Usage:
  python scripts/update_standings.py                  fetch from ESPN and update
  python scripts/update_standings.py --from-file F    read an ESPN-shaped JSON file instead (for testing)
"""
import argparse, json, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

SEASON_ID = "2026-27"          # must match the id in data/seasons.json
ESPN_SEASON = 2027             # ESPN names a season by the year it ends
URL = f"https://site.api.espn.com/apis/v2/sports/basketball/nba/standings?level=3&season={ESPN_SEASON}"
OUT = Path(__file__).resolve().parent.parent / "data" / "standings.json"

# Name used in the comp spreadsheet -> last word(s) of ESPN's team name
TEAMS = {
    "Atlanta": "Hawks", "Boston": "Celtics", "Brooklyn": "Nets", "Charlotte": "Hornets",
    "Chicago": "Bulls", "Cleveland": "Cavaliers", "Dallas": "Mavericks", "Denver": "Nuggets",
    "Detroit": "Pistons", "Golden State": "Warriors", "Houston": "Rockets", "Indiana": "Pacers",
    "LA Clips": "Clippers", "LA Luka's": "Lakers", "Memphis": "Grizzlies", "Miami": "Heat",
    "Milwaukee": "Bucks", "Minnesota": "Timberwolves", "New Orleans": "Pelicans",
    "New York": "Knicks", "OKC": "Thunder", "Orlando": "Magic", "Philadelphia": "76ers",
    "Phoenix": "Suns", "Portland": "Trail Blazers", "Sacramento": "Kings",
    "San Antonio": "Spurs", "Toronto": "Raptors", "Utah": "Jazz", "Washington": "Wizards",
}


def fail(msg):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(1)


def walk(node, found, seasons):
    """Collect every standings entry (a dict with 'team' and 'stats') and any season labels."""
    if isinstance(node, dict):
        if isinstance(node.get("team"), dict) and isinstance(node.get("stats"), list):
            found.append(node)
        if "seasonDisplayName" in node:
            seasons.add(str(node["seasonDisplayName"]))
        for v in node.values():
            walk(v, found, seasons)
    elif isinstance(node, list):
        for v in node:
            walk(v, found, seasons)


def stat(entry, name):
    for s in entry["stats"]:
        if s.get("name") == name:
            v = s.get("value")
            if v is None:
                v = s.get("displayValue")
            try:
                f = float(v)
            except (TypeError, ValueError):
                return None
            return int(f) if f == int(f) else None
    return None


def sheet_name(display):
    words = display.split()
    for sheet, nick in TEAMS.items():
        n = len(nick.split())
        if words[-n:] == nick.split():
            return sheet
    return None


def parse(data):
    found, seasons = [], set()
    walk(data, found, seasons)
    if seasons and seasons != {SEASON_ID}:
        fail(f"ESPN returned season {sorted(seasons)}, expected {SEASON_ID}. Nothing written.")
    teams = {}
    for e in found:
        name = sheet_name(e["team"].get("displayName", ""))
        if name is None:
            continue
        w, l = stat(e, "wins"), stat(e, "losses")
        if w is None or l is None:
            fail(f"No wins/losses for {e['team'].get('displayName')}. Nothing written.")
        teams[name] = {"w": w, "l": l}
    missing = sorted(set(TEAMS) - set(teams))
    if missing:
        fail(f"Found {len(teams)} of 30 teams, missing: {', '.join(missing)}. Nothing written.")
    for n, r in teams.items():
        if r["w"] < 0 or r["l"] < 0 or r["w"] + r["l"] > 82:
            fail(f"Implausible record for {n}: {r['w']}-{r['l']}. Nothing written.")
    return teams


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-file")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    out = Path(a.out)

    if a.from_file:
        data = json.loads(Path(a.from_file).read_text())
    else:
        req = urllib.request.Request(URL, headers={"User-Agent": "over-under-comp/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8"))

    teams = parse(data)

    old = {}
    if out.exists():
        try:
            old = json.loads(out.read_text())
        except Exception:
            old = {}
    if old.get("season") == SEASON_ID and old.get("teams"):
        for n, r in teams.items():
            o = old["teams"].get(n)
            if o and (r["w"] + r["l"]) < (o["w"] + o["l"]):
                fail(f"{n} has fewer games than the saved file ({r['w']}-{r['l']} vs {o['w']}-{o['l']}). Nothing written.")
        if old["teams"] == teams:
            print("No change in standings.")
            return

    doc = {
        "season": SEASON_ID,
        "mode": "live",
        "updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "ESPN",
        "teams": dict(sorted(teams.items())),
    }
    out.write_text(json.dumps(doc, indent=1) + "\n")
    played = sum(r["w"] + r["l"] for r in teams.values()) // 2
    print(f"Updated standings: {played} games played so far.")


if __name__ == "__main__":
    main()
