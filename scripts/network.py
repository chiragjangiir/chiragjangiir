#!/usr/bin/env python3
"""Update assets/network.svg using GitHub's public REST API."""
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / "assets" / "network.svg"
USERNAME = os.environ.get("GITHUB_USERNAME", "chiragjangiir")
TOKEN = os.environ.get("GITHUB_TOKEN", "")


def get_json(url):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-readme-network-refresh"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def xml_escape(value):
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;"))


def replace_text(svg, element_id, value):
    pattern = rf'(<text\s+id="{re.escape(element_id)}"\b[^>]*>).*?(</text>)'
    result, count = re.subn(pattern, lambda m: m.group(1) + xml_escape(value) + m.group(2), svg, count=1, flags=re.S)
    if not count:
        raise ValueError(f"SVG element id not found: {element_id}")
    return result


def main():
    profile = get_json(f"https://api.github.com/users/{USERNAME}")
    followers = get_json(f"https://api.github.com/users/{USERNAME}/followers?per_page=3")
    svg = SVG.read_text(encoding="utf-8")
    svg = replace_text(svg, "followers", profile.get("followers", 0))
    svg = replace_text(svg, "repos", profile.get("public_repos", 0))
    names = ", ".join(user.get("login", "") for user in followers if user.get("login"))
    svg = replace_text(svg, "recent", names[:30] if names else "No followers yet")
    SVG.write_text(svg, encoding="utf-8")
    print(f"Updated {SVG.relative_to(ROOT)} for @{USERNAME}")


if __name__ == "__main__":
    try:
        main()
    except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Could not refresh network.svg: {exc}")
