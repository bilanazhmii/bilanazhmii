#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import urllib.request
from datetime import datetime, timezone

OWNER = "bilanazhmii"
README = "README.md"
API = f"https://api.github.com/users/{OWNER}/repos?per_page=100&sort=updated&direction=desc"

MANAGED_START = "<!-- AUTO-REPOS:START -->"
MANAGED_END = "<!-- AUTO-REPOS:END -->"
UPDATED_START = "<!-- AUTO-UPDATED:START -->"
UPDATED_END = "<!-- AUTO-UPDATED:END -->"

# These are kept as curated featured projects rather than being reordered
# automatically, so the visual hierarchy remains intentional.
FEATURED = {"SchoolDMS", "Our-bisnis"}

req = urllib.request.Request(
    API,
    headers={
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
        "User-Agent": f"{OWNER}-profile-updater",
    },
)

with urllib.request.urlopen(req, timeout=30) as response:
    repos = json.load(response)

repos = [
    r for r in repos
    if not r.get("fork", False) and not r.get("archived", False)
]

def lang(repo: dict) -> str:
    language = repo.get("language")
    return language or "Open Source"

def card(repo: dict) -> str:
    name = repo["name"]
    description = (repo.get("description") or "No description yet.").strip()
    description = description.replace("\n", " ")
    if len(description) > 120:
        description = description[:117].rstrip() + "..."
    homepage = repo.get("homepage") or ""
    repo_url = repo["html_url"]
    links = [f'[<img src="./assets/btn-view-repo.svg" alt="View repository" height="32">]({repo_url})']
    if homepage.startswith("http"):
        links.append(f'[<img src="./assets/btn-live-demo.svg" alt="Live demo" height="32">]({homepage})')
    return (
        f'<td width="50%" valign="top">\n\n'
        f'### {name}\n\n'
        f'{description}\n\n'
        f'`{lang(repo)}`\n\n'
        + " &nbsp; ".join(links)
        + "\n\n</td>"
    )

# Keep the four-column/2x2 layout balanced by selecting the most recently
# updated repositories. New repositories automatically appear here.
rows = []
for i in range(0, len(repos[:8]), 2):
    pair = repos[i:i+2]
    row = "<tr>\n" + "\n\n".join(card(r) for r in pair) + "\n</tr>"
    rows.append(row)

repo_block = (
    f"{MANAGED_START}\n"
    "<table cellspacing=\"20\">\n"
    + "\n\n".join(rows)
    + "\n</table>\n\n"
    '<p align="center">\n'
    '  <a href="https://github.com/bilanazhmii?tab=repositories"><img src="./assets/btn-all-repositories.svg" alt="All repositories" height="36"></a>\n'
    '</p>\n'
    f"{MANAGED_END}"
)

utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
updated_block = (
    f"{UPDATED_START}\n"
    f'<sub>Profile data refreshed automatically · {utc_now}</sub>\n'
    f"{UPDATED_END}"
)

readme = open(README, "r", encoding="utf-8").read()

if MANAGED_START not in readme or MANAGED_END not in readme:
    raise SystemExit("Missing AUTO-REPOS markers in README.md")

readme = re.sub(
    re.escape(MANAGED_START) + r".*?" + re.escape(MANAGED_END),
    repo_block,
    readme,
    count=1,
    flags=re.S,
)

# Add a tiny status line just below the top social links.
if UPDATED_START in readme:
    readme = re.sub(
        re.escape(UPDATED_START) + r".*?" + re.escape(UPDATED_END),
        updated_block,
        readme,
        count=1,
        flags=re.S,
    )
else:
    marker = '<sub>Independent developer · Lembang, Indonesia</sub>'
    readme = readme.replace(
        marker,
        marker + "\n\n" + updated_block,
        1,
    )

open(README, "w", encoding="utf-8").write(readme)
