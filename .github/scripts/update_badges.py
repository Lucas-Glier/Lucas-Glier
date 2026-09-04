#!/usr/bin/env python3
"""
Minimal, resilient updater for TryHackMe and HackTheBox badges.
- Uses public profile pages (no login by default).
- Writes JSON files consumable by shields.io (schemaVersion 1).
- Safe: always writes something ("unavailable") instead of failing.
"""

import os
import re
import json
import time
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "github-badge-updater/1.0 (+https://github.com/Lucas-Glier)"}
TIMEOUT = 15


def write_badge(path, label, message, color="blue"):
    payload = {"schemaVersion": 1, "label": label, "message": message, "color": color}
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def fetch_tryhackme(user):
    url = f"https://tryhackme.com/profile/{user}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code != 200:
            return "unavailable"
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(" ", strip=True)
        # common patterns: "Streak 12", "12 day streak", "Total XP 1,234"
        m = re.search(r"streak[:\s]*([0-9]{1,5})", text, re.I)
        if not m:
            m = re.search(r"([0-9]{1,5})\s*day(?:s)?\s*streak", text, re.I)
        if m:
            return f"{m.group(1)} days"
        m = re.search(r"Total\s+XP[:\s]*([0-9,]{1,15})", text, re.I)
        if m:
            return f"{m.group(1)} XP"
    except Exception:
        pass
    return "unavailable"


def fetch_htb(user):
    # Try public profile page
    url = f"https://www.hackthebox.com/users/{user}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code != 200:
            return "unavailable"
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(" ", strip=True)
        # Try common patterns: "Rank #123", "Points 4567", "Profile Score 12"
        m = re.search(r"Rank[:\s#]*([0-9,]{1,15})", text, re.I)
        if m:
            return f"Rank #{m.group(1)}"
        m = re.search(r"Points[:\s]*([0-9,]{1,15})", text, re.I)
        if m:
            return f"{m.group(1)} pts"
        m = re.search(r"Score[:\s]*([0-9,]{1,15})", text, re.I)
        if m:
            return f"{m.group(1)} pts"
    except Exception:
        pass
    return "unavailable"


def main():
    thm_user = os.getenv("THM_USER", "lucas.glier")
    htb_user = os.getenv("HTB_USER", "lucasglier")

    badges_dir = ".github/badges"
    os.makedirs(badges_dir, exist_ok=True)

    thm_msg = fetch_tryhackme(thm_user)
    write_badge(os.path.join(badges_dir, "thm.json"), "TryHackMe", thm_msg or "unavailable", "blue")

    htb_msg = fetch_htb(htb_user)
    write_badge(os.path.join(badges_dir, "htb.json"), "HackTheBox", htb_msg or "unavailable", "green")


if __name__ == "__main__":
    # small delay to reduce chance of transient network errors causing empty files
    for attempt in range(2):
        try:
            main()
            break
        except Exception:
            time.sleep(2)
