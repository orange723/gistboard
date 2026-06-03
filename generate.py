#!/usr/bin/env python3
"""Fetch all public gists for a GitHub user and generate a terminal-style HTML page."""

import json
import os
import sys
import time
from datetime import datetime, timezone
from html import escape
from urllib.request import Request, urlopen

USERNAME = "orange723"
API_URL = f"https://api.github.com/users/{USERNAME}/gists"
PER_PAGE = 100  # max allowed by GitHub API
OUT_DIR = "dist"
OUT_FILE = os.path.join(OUT_DIR, "index.html")


def fetch_all_gists() -> list[dict]:
    """Paginate through the GitHub API and return all public gists."""
    all_gists = []
    page = 1
    while True:
        url = f"{API_URL}?page={page}&per_page={PER_PAGE}"
        req = Request(url, headers={"Accept": "application/vnd.github+json",
                                     "User-Agent": "gistboard/1.0"})
        with urlopen(req, timeout=30) as resp:
            gists = json.loads(resp.read().decode())
        if not gists:
            break
        all_gists.extend(gists)
        if len(gists) < PER_PAGE:
            break
        page += 1
        time.sleep(0.1)  # be nice to the API
    return all_gists


def relative_time(iso_str: str) -> str:
    """Convert ISO 8601 timestamp to a human-friendly relative time string."""
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    delta = now - dt
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "just now"
    mins = seconds // 60
    if mins < 60:
        return f"{mins}m ago"
    hours = mins // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    if days < 30:
        return f"{days}d ago"
    months = days // 30
    if months < 12:
        return f"{months}mo ago"
    return f"{months // 12}y ago"


def lang_color(lang: str) -> str:
    """Return a terminal-appropriate ANSI-ish color for a language."""
    colors = {
        "Python":       "#4B8BBE",
        "JavaScript":   "#F0DB4F",
        "TypeScript":   "#3178C6",
        "HTML":         "#E34C26",
        "CSS":          "#563D7C",
        "Shell":        "#89E051",
        "Ruby":         "#CC342D",
        "Go":           "#00ADD8",
        "Rust":         "#DEA584",
        "Java":         "#B07219",
        "C":            "#555555",
        "C++":          "#F34B7D",
        "C#":           "#178600",
        "Swift":        "#FFAC45",
        "Kotlin":       "#A97BFF",
        "Scala":        "#C22D40",
        "PHP":          "#4F5D95",
        "R":            "#198CE7",
        "Dart":         "#00B4AB",
        "Lua":          "#000080",
        "Makefile":     "#427819",
        "Dockerfile":   "#384D54",
        "Vim Script":   "#199F4B",
        "Emacs Lisp":   "#C065DB",
        "SQL":          "#E38C00",
        "YAML":         "#CB171E",
        "JSON":         "#292929",
        "Markdown":     "#083FA1",
        "Text":         "#AAAAAA",
    }
    return colors.get(lang, "#AAAAAA")


def render_gist(gist: dict) -> str:
    """Render a single gist as a terminal-styled HTML row."""
    gist_id = gist["id"]
    html_url = gist["html_url"]
    description = gist.get("description") or "(no description)"
    created = relative_time(gist["created_at"])
    updated = relative_time(gist["updated_at"])

    files = gist.get("files", {})
    file_names = list(files.keys())
    file_count = len(file_names)
    file_label = "file" if file_count == 1 else "files"

    # Collect unique languages
    langs = set()
    for f in files.values():
        lang = f.get("language")
        if lang:
            langs.add(lang)
    lang_str = ", ".join(sorted(langs)) if langs else "N/A"

    # Title: prefer first filename, or description
    title = file_names[0] if file_names else "untitled"
    desc_safe = escape(description)
    title_safe = escape(title)

    # Language tags
    lang_tags = ""
    for lang in sorted(langs):
        c = lang_color(lang)
        lang_tags += f'<span class="lang-tag" style="color:{c}">[{escape(lang)}]</span> '

    return f"""<div class="gist-row">
  <span class="prompt">$</span>
  <a href="{escape(html_url)}" target="_blank" class="gist-link">{title_safe}</a>
  <span class="gist-meta">({file_count} {file_label})</span>
  <span class="gist-desc">{desc_safe}</span>
  <span class="gist-info">
    {lang_tags}
    <span class="gist-time">updated {updated}</span>
  </span>
</div>"""


def build_html(gists: list[dict]) -> str:
    """Assemble the full HTML document."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    gist_count = len(gists)
    total_files = sum(len(g.get("files", {})) for g in gists)

    rows = "\n".join(render_gist(g) for g in gists)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>gistboard — {escape(USERNAME)}</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html {{ font-size: 14px; }}
  body {{
    background: #0c0c0c;
    color: #c0c0c0;
    font-family: "SF Mono", "Menlo", "Monaco", "Cascadia Code", "Consolas",
                 "Liberation Mono", "Courier New", monospace;
    min-height: 100vh;
    display: flex;
    justify-content: center;
    padding: 2rem 1rem;
  }}
  .terminal {{
    width: 100%;
    max-width: 900px;
    background: #141414;
    border-radius: 8px;
    border: 1px solid #333;
    box-shadow: 0 8px 32px rgba(0,0,0,0.6);
    overflow: hidden;
  }}
  .terminal-header {{
    background: #1e1e1e;
    padding: 10px 14px;
    display: flex;
    align-items: center;
    gap: 8px;
    border-bottom: 1px solid #2a2a2a;
    user-select: none;
  }}
  .dot {{
    width: 12px; height: 12px; border-radius: 50%;
    display: inline-block;
  }}
  .dot.red    {{ background: #FF5F57; }}
  .dot.yellow {{ background: #FEBC2E; }}
  .dot.green  {{ background: #28C840; }}
  .term-title {{
    color: #888;
    font-size: 0.85rem;
    margin-left: 6px;
  }}
  .terminal-body {{
    padding: 16px 18px 24px;
    min-height: 400px;
    line-height: 1.6;
  }}
  .header-line {{
    color: #569CD6;
    margin-bottom: 6px;
  }}
  .stats-line {{
    color: #6A9955;
    margin-bottom: 16px;
  }}
  .gist-row {{
    padding: 6px 0;
    border-bottom: 1px solid #1e1e1e;
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 6px;
  }}
  .gist-row:last-child {{ border-bottom: none; }}
  .gist-row:hover {{ background: #1a1a1a; margin: 0 -18px; padding-left: 18px; padding-right: 18px; }}
  .prompt {{
    color: #28C840;
    font-weight: bold;
    margin-right: 4px;
    flex-shrink: 0;
  }}
  .gist-link {{
    color: #61AFEF;
    text-decoration: none;
    font-weight: bold;
  }}
  .gist-link:hover {{ text-decoration: underline; }}
  .gist-meta {{
    color: #6A9955;
    font-size: 0.85rem;
  }}
  .gist-desc {{
    color: #888;
    font-style: italic;
  }}
  .gist-info {{
    display: block;
    width: 100%;
    padding-left: 14px;
    font-size: 0.8rem;
    color: #666;
    margin-top: 1px;
  }}
  .lang-tag {{
    font-weight: bold;
    margin-right: 6px;
  }}
  .gist-time {{
    color: #555;
  }}
  .footer-line {{
    margin-top: 20px;
    padding-top: 10px;
    border-top: 1px solid #2a2a2a;
    color: #555;
    font-size: 0.8rem;
  }}
  .footer-line .prompt {{ color: #28C840; }}
  .cursor {{
    display: inline-block;
    width: 8px; height: 16px;
    background: #c0c0c0;
    animation: blink 1s step-end infinite;
    vertical-align: text-bottom;
    margin-left: 2px;
  }}
  @keyframes blink {{ 50% {{ opacity: 0; }} }}
</style>
</head>
<body>
<div class="terminal">
  <div class="terminal-header">
    <span class="dot red"></span>
    <span class="dot yellow"></span>
    <span class="dot green"></span>
    <span class="term-title">gistboard — {escape(USERNAME)}</span>
  </div>
  <div class="terminal-body">
    <div class="header-line">$ gistboard --fetch {escape(USERNAME)}</div>
    <div class="header-line">$ fetching from api.github.com...</div>
    <div class="stats-line">$ found {gist_count} gists ({total_files} files) &mdash; last build: {now_str}</div>
    <div class="stats-line">$ ─────────────────────────────────────────────</div>
{rows}
    <div class="footer-line">
      <span class="prompt">$</span> built by <a href="https://github.com/{escape(USERNAME)}/gistboard" style="color:#61AFEF;text-decoration:none;">gistboard</a> &middot; {now_str}<span class="cursor"></span>
    </div>
  </div>
</div>
</body>
</html>"""


def main() -> None:
    print(f"[gistboard] fetching gists for {USERNAME}...")
    gists = fetch_all_gists()
    print(f"[gistboard] got {len(gists)} gists")

    gists.sort(key=lambda g: g["updated_at"], reverse=True)

    html = build_html(gists)

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(OUT_FILE) / 1024
    print(f"[gistboard] wrote {OUT_FILE} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
