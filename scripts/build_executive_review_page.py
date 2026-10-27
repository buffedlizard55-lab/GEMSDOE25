#!/usr/bin/env python3
"""Render the dated current-review Markdown as a static GitHub Pages HTML page."""
from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def inline(text: str) -> str:
    code: list[str] = []

    def hold(match: re.Match[str]) -> str:
        code.append(f"<code>{html.escape(match.group(1))}</code>")
        return f"\x00{len(code) - 1}\x00"

    text = re.sub(r"`([^`]+)`", hold, text)
    text = html.escape(text)

    def link(match: re.Match[str]) -> str:
        label, href = match.groups()
        if href.startswith("../docs/"):
            href = href[len("../docs/"):]
        elif not href.startswith(("../", "http://", "https://", "mailto:", "#")):
            if href.startswith(("knowledge/", "registry/", "evidence/", "scripts/")):
                href = "../" + href
            else:
                href = "../knowledge/" + href
        return f'<a href="{html.escape(href, quote=True)}">{inline(label)}</a>'

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    for i, item in enumerate(code):
        text = text.replace(f"\x00{i}\x00", item)
    return text


def cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def render_markdown(markdown: str) -> str:
    lines = markdown.splitlines()
    out: list[str] = []
    paragraph: list[str] = []
    listing = False
    table = False
    quote = False

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            out.append("<p>" + inline(" ".join(paragraph)) + "</p>")
            paragraph = []

    def close_list() -> None:
        nonlocal listing
        if listing:
            out.append("</ul>")
            listing = False

    def close_table() -> None:
        nonlocal table
        if table:
            out.append("</tbody></table>")
            table = False

    def close_quote() -> None:
        nonlocal quote
        if quote:
            out.append("</blockquote>")
            quote = False

    for line in lines:
        if line.startswith("|"):
            flush_paragraph()
            close_list()
            close_quote()
            row = cells(line)
            if all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in row):
                continue
            if not table:
                out.append("<table><thead><tr>" + "".join(f"<th>{inline(cell)}</th>" for cell in row) + "</tr></thead><tbody>")
                table = True
                continue
            out.append("<tr>" + "".join(f"<td>{inline(cell)}</td>" for cell in row) + "</tr>")
            continue
        close_table()
        if not line.strip():
            flush_paragraph()
            close_list()
            close_quote()
            continue
        heading = re.match(r"^(#{1,4})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            close_list()
            close_quote()
            level = len(heading.group(1))
            text = heading.group(2)
            slug = re.sub(r"[^a-z0-9]+", "-", re.sub(r"[`*]", "", text.lower())).strip("-")
            out.append(f'<h{level} id="{html.escape(slug, quote=True)}">{inline(text)}</h{level}>')
            continue
        if line.startswith("> "):
            flush_paragraph()
            close_list()
            if not quote:
                out.append("<blockquote>")
                quote = True
            out.append("<p>" + inline(line[2:]) + "</p>")
            continue
        if line.startswith("- "):
            flush_paragraph()
            close_quote()
            if not listing:
                out.append("<ul>")
                listing = True
            out.append("<li>" + inline(line[2:]) + "</li>")
            continue
        if line.strip() == "---":
            flush_paragraph()
            close_list()
            close_quote()
            out.append("<hr>")
            continue
        close_list()
        close_quote()
        paragraph.append(line.strip())
    flush_paragraph()
    close_list()
    close_table()
    close_quote()
    return "\n".join(out)


def main() -> None:
    source = ROOT / "knowledge/39_current_review_2026-10-27.md"
    body = render_markdown(source.read_text())
    page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nine-site executive review · GEMSDOE25</title><link rel="stylesheet" href="assets/style.css">
<style>.report{{max-width:1050px;margin:2rem auto;padding:2rem;background:#fff;border-radius:14px;line-height:1.65}}.report table{{display:block;overflow-x:auto;border-collapse:collapse;width:100%;font-size:.92rem}}.report td{{border:1px solid #d9e1ea;padding:.55rem;vertical-align:top}}.report h1{{font-size:2.1rem}}.report blockquote{{border-left:4px solid #2563eb;padding:.2rem 1rem;color:#334155}}.report ul{{padding-left:1.4rem}}.report a{{overflow-wrap:anywhere}}</style></head>
<body><header class="top"><div class="wrap"><div class="brand">GEMSDOE25<small>DOE GEMS Prize · current evidence review</small></div><nav>
<a href="index.html">Start here</a><a href="current-review.html">Current review</a><a class="on" href="current-executive-review.html">Nine-site report</a><a href="executive-summary.html">How to submit</a><a href="research.html">Research</a><a href="sources.html">Sources &amp; audit</a></nav></div></header>
<main class="report">{body}<p><a href="../knowledge/39_current_review_2026-10-27.md">Open source Markdown</a> · <a href="../registry/run_card_current_review_2026-10-27.json">Machine-readable run card</a></p></main>
<footer><div class="wrap">No leaderboard score is promised. No competition upload is automated. Current eligibility is <b>NO — DO NOT SUBMIT</b>.</div></footer></body></html>'''
    (ROOT / "docs/current-executive-review.html").write_text(page)
    print("docs/current-executive-review.html: rendered nine-site report")


if __name__ == "__main__":
    main()
