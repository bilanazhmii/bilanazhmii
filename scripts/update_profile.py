#!/usr/bin/env python3
from __future__ import annotations

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


def row(repo: dict) -> str:
    name = repo["name"]
    links = f"[**{name}**]({repo['html_url']}) ↗"
    homepage = (repo.get("homepage") or "").strip()
    description = clean_description(repo)
    if homepage.startswith(("https://", "http://")):
        description += f" [Live ↗]({homepage})"
    return f"| {links} | {description} | `{language(repo)}` |"


repos = [
    repo
    for repo in fetch_repositories()
    if not repo.get("fork")
    and not repo.get("archived")
    and repo["name"] not in EXCLUDED
]

table = [
    "| Project | What it is | Built with |",
    "| :-- | :-- | :-- |",
    *(row(repo) for repo in repos[:5]),
]

repo_block = (
    f"{MANAGED_START}\n"
    + "\n".join(table)
    + "\n\n"
    + '<div align="right"><a href="https://github.com/'
    + f'{OWNER}?tab=repositories">View all repositories →</a></div>\n'
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
