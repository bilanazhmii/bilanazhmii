#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import urllib.request

OWNER = "bilanazhmii"
README = "README.md"
API = f"https://api.github.com/users/{OWNER}/repos?per_page=100&sort=updated&direction=desc"

MANAGED_START = "<!-- AUTO-REPOS:START -->"
MANAGED_END = "<!-- AUTO-REPOS:END -->"

# Featured projects already have full editorial cards above the generated list.
EXCLUDED = {OWNER.lower(), "SchoolDMS", "Our-bisnis", "puzzle-mobile"}

# GitHub descriptions are intentionally short; these fallbacks keep the profile
# useful while repository metadata is still being polished.
CURATED = {
    "Portofolio": (
        "The current portfolio experience for selected work, capabilities, "
        "and an intentionally crafted developer identity."
    ),
    "MyPortofolio": (
        "An immersive 3D portfolio with motion, spatial interaction, and a "
        "cinematic WebGL experience."
    ),
    "BotIndo": (
        "A Discord and Minecraft operations bot with RCON, server status, "
        "commands, AI utilities, and a web dashboard."
    ),
}


def fetch_repositories() -> list[dict]:
    request = urllib.request.Request(
        API,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": f"{OWNER}-profile-updater",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def clean_description(repo: dict) -> str:
    name = repo["name"]
    raw = (repo.get("description") or "").strip().replace("\n", " ")
    # Ignore placeholder metadata and use reviewed editorial copy instead.
    if len(raw) < 12:
        raw = CURATED.get(name, "A software project from my public workspace.")
    raw = raw.replace("|", "\\|")
    return raw[:157].rstrip() + "..." if len(raw) > 160 else raw


def language(repo: dict) -> str:
    return repo.get("language") or "Open Source"


def card(repo: dict) -> str:
    name = html.escape(repo["name"])
    repo_url = html.escape(repo["html_url"], quote=True)
    description = html.escape(clean_description(repo))
    repo_language = html.escape(language(repo))
    homepage = (repo.get("homepage") or "").strip()
    actions = (
        f'<a href="{repo_url}"><img src="./assets/btn-view-repo.svg" '
        f'alt="View {name} repository" height="32"></a>'
    )
    if homepage.startswith(("https://", "http://")):
        safe_homepage = html.escape(homepage, quote=True)
        actions += (
            f'&nbsp;<a href="{safe_homepage}"><img src="./assets/btn-live-demo.svg" '
            f'alt="Open {name} live site" height="32"></a>'
        )

    return (
        '<td width="50%" valign="top">\n\n'
        f'<strong>{name}</strong><br>\n'
        f'<sub>{description}</sub>\n\n'
        f'<sub>{repo_language}</sub>\n\n'
        f'<br>{actions}\n\n'
        '</td>'
    )


repos = [
    repo
    for repo in fetch_repositories()
    if not repo.get("fork")
    and not repo.get("archived")
    and repo["name"] not in EXCLUDED
]

cards = [card(repo) for repo in repos[:4]]
if len(cards) % 2:
    cards.append('<td width="50%"></td>')

rows = [
    '<tr>\n' + cards[index] + '\n' + cards[index + 1] + '\n</tr>'
    for index in range(0, len(cards), 2)
]

repo_block = (
    f"{MANAGED_START}\n"
    + '<details>\n'
    + '<summary><strong>OPEN SOURCE INDEX</strong> · More experiments and systems</summary>\n'
    + '<br>\n\n<table>\n'
    + "\n".join(rows)
    + '\n</table>\n\n'
    + '<p align="right"><a href="https://github.com/'
    + f'{OWNER}?tab=repositories"><img src="./assets/btn-all-repositories.svg" '
    + 'alt="Explore all repositories" height="34"></a></p>\n'
    + '</details>\n'
    + f"{MANAGED_END}"
)

with open(README, "r", encoding="utf-8") as handle:
    readme = handle.read()

if MANAGED_START not in readme or MANAGED_END not in readme:
    raise SystemExit("Missing AUTO-REPOS markers in README.md")

updated = re.sub(
    re.escape(MANAGED_START) + r".*?" + re.escape(MANAGED_END),
    repo_block,
    readme,
    count=1,
    flags=re.S,
)

with open(README, "w", encoding="utf-8") as handle:
    handle.write(updated)
