#!/usr/bin/env python3
"""
Convert a published brief HTML page into the embed feed formats.

    python3 build-embed.py ../briefs/brief-2026-08-17.html --out .

Writes:
    latest.json   structured feed the widget fetches
    <date>.json   dated copy, so you keep an addressable archive
    static.html   self-contained no-JavaScript fragment you can paste directly

This exists to backfill a brief that was already published. Going forward the
routine emits latest.json itself (see prompt.md step 5d), so this is a
convenience tool, not part of the daily path.

Deliberately stdlib-only — no pip install on any machine that runs it.
"""

import argparse
import html
import json
import pathlib
import re
import sys
from datetime import datetime, timezone

TAG = re.compile(r"<[^>]+>")
ANCHOR = re.compile(r'<a\s+href="([^"]+)"[^>]*>(.*?)</a>', re.S)


def text(fragment: str) -> str:
    """Strip tags and unescape entities, collapsing whitespace."""
    return re.sub(r"\s+", " ", html.unescape(TAG.sub("", fragment))).strip()


def one(pattern: str, source: str, label: str, required=True):
    m = re.search(pattern, source, re.S)
    if not m:
        if required:
            raise SystemExit(f"parse error: could not find {label}")
        return None
    return m.group(1)


def parse(page: str) -> dict:
    date_label = text(one(r'<div class="date">(.*?)</div>', page, "date"))

    tldr_block = one(r'<div class="tldr">(.*?)</div>', page, "tldr block")
    tldr = [text(li) for li in re.findall(r"<li>(.*?)</li>", tldr_block, re.S)]

    # .item blocks contain a nested div, so split on the opening tag rather
    # than trying to match balanced closers.
    chunks = re.split(r'<div class="item">', page)[1:]
    if not chunks:
        raise SystemExit("parse error: no .item blocks found")
    chunks[-1] = re.split(r"<footer", chunks[-1])[0]

    items = []
    for i, chunk in enumerate(chunks, start=1):
        src_block = one(r'<p class="src">(.*?)</p>', chunk, "sources", required=False) or ""
        sources = [
            {"outlet": text(label), "url": html.unescape(url)}
            for url, label in ANCHOR.findall(src_block)
        ]
        items.append(
            {
                "slot": i,
                "category": text(one(r'<div class="cat">(.*?)</div>', chunk, "category")),
                "headline": text(one(r"<h3>(.*?)</h3>", chunk, "headline")),
                "body": text(one(r"<p>(.*?)</p>", chunk, "body")),
                "plain": text(
                    one(
                        r'<p class="plain"><b>In plain terms</b>(.*?)</p>',
                        chunk,
                        "plain-terms",
                    )
                ),
                "why": text(
                    one(
                        r'<p class="why"><b>Why it matters</b><br>(.*?)</p>',
                        chunk,
                        "why-it-matters",
                    )
                ),
                "sources": sources,
            }
        )

    if len(items) != 10:
        print(f"warning: expected 10 items, parsed {len(items)}", file=sys.stderr)

    missing = [it["slot"] for it in items if not it["plain"]]
    if missing:
        print(f"warning: slots missing 'In plain terms': {missing}", file=sys.stderr)

    try:
        iso = datetime.strptime(date_label, "%A, %B %d, %Y").strftime("%Y-%m-%d")
    except ValueError:
        iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        print(f"warning: could not parse '{date_label}', dating feed {iso}", file=sys.stderr)

    return {
        "date": iso,
        "dateLabel": date_label,
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tldr": tldr,
        "items": items,
    }


STATIC_CSS = """
/* This fragment paints its own background on purpose. It cannot measure the
   page it lands on the way the JS widget does, so leaving the ground
   transparent would put dark-mode text on a light page for any visitor whose
   OS is set to dark. An explicit background keeps text and ground agreeing. */
.ndb{--ndb-bg:#fbfaf8;--ndb-surface:#fff;--ndb-border:#e5e1d9;--ndb-text:#1a1a18;
--ndb-muted:#6b6862;--ndb-accent:#9a3412;--ndb-rule:#ede9e0;--ndb-pbg:#eef1f5;
--ndb-pink:#3a4a5c;--ndb-pborder:#dde3ea;--ndb-plabel:#4d6480;
--ndb-serif:ui-serif,Georgia,"Times New Roman",serif;
--ndb-sans:ui-sans-serif,system-ui,-apple-system,sans-serif;
font-family:var(--ndb-serif);font-size:16px;line-height:1.65;color:var(--ndb-text);
background:var(--ndb-bg);padding:1.75rem 2rem 2rem;border-radius:8px;
max-width:44rem;box-sizing:border-box}
@media (prefers-color-scheme:dark){.ndb{--ndb-bg:#14140f;--ndb-surface:#1c1c17;
--ndb-border:#2f2f27;--ndb-text:#f0efe9;--ndb-muted:#9d9a90;--ndb-accent:#fb923c;
--ndb-rule:#26261f;--ndb-pbg:#161b21;--ndb-pink:#c3d2e0;--ndb-pborder:#262d36;
--ndb-plabel:#8fa9c4}}
@media (max-width:34rem){.ndb{padding:1.25rem 1.25rem 1.5rem}}
.ndb *{box-sizing:border-box}
.ndb-hd{border-bottom:2px solid var(--ndb-text);padding-bottom:.75rem;margin-bottom:1.5rem}
.ndb-hd h2{font-size:1.5rem;margin:0 0 .2rem;letter-spacing:-.02em}
.ndb-date{font-family:var(--ndb-sans);font-size:.75rem;text-transform:uppercase;
letter-spacing:.08em;color:var(--ndb-muted)}
.ndb-tldr{background:var(--ndb-surface);border:1px solid var(--ndb-border);border-radius:6px;
padding:1.125rem 1.375rem;margin-bottom:2rem}
.ndb-tldr h3{font-family:var(--ndb-sans);font-size:.6875rem;text-transform:uppercase;
letter-spacing:.1em;color:var(--ndb-muted);margin:0 0 .625rem}
.ndb-tldr ol{margin:0;padding-left:1.25rem;font-size:.9375rem}
.ndb-tldr li{margin-bottom:.4rem}
.ndb-item{padding-top:1.5rem;margin-top:1.5rem;border-top:1px solid var(--ndb-rule)}
.ndb-item:first-of-type{border-top:0;margin-top:0;padding-top:0}
.ndb-cat{font-family:var(--ndb-sans);font-size:.6875rem;text-transform:uppercase;
letter-spacing:.1em;color:var(--ndb-accent);font-weight:600;margin-bottom:.35rem}
.ndb-item h4{font-size:1.1875rem;line-height:1.35;margin:0 0 .55rem;letter-spacing:-.01em}
.ndb-item p{margin:0 0 .7rem}
.ndb-plain{background:var(--ndb-pbg);border:1px solid var(--ndb-pborder);border-radius:6px;
padding:.8rem 1.0625rem .9rem;color:var(--ndb-pink);font-family:var(--ndb-sans);
font-size:.9375rem;line-height:1.7}
.ndb-plain b{display:block;font-size:.6875rem;text-transform:uppercase;letter-spacing:.09em;
color:var(--ndb-plabel);margin-bottom:.25rem}
.ndb-why{border-left:3px solid var(--ndb-accent);padding-left:.8rem}
.ndb-why b{display:block;font-family:var(--ndb-sans);font-size:.75rem;text-transform:uppercase;
letter-spacing:.06em;color:var(--ndb-accent);margin-bottom:.15rem}
.ndb-src{font-family:var(--ndb-sans);font-size:.75rem;color:var(--ndb-muted)}
.ndb-src a{color:var(--ndb-muted);text-decoration:underline;text-underline-offset:2px}
"""


def static_html(feed: dict) -> str:
    e = html.escape
    out = ["<!-- Daily Brief — static fragment. No JavaScript. -->",
           "<style>" + STATIC_CSS.strip() + "</style>",
           '<div class="ndb">',
           '  <div class="ndb-hd"><h2>Daily Brief</h2>',
           f'    <div class="ndb-date">{e(feed["dateLabel"])}</div></div>']

    if feed.get("tldr"):
        out.append('  <div class="ndb-tldr"><h3>The whole thing in 30 seconds</h3><ol>')
        for line in feed["tldr"]:
            out.append(f"    <li>{e(line)}</li>")
        out.append("  </ol></div>")

    for it in feed["items"]:
        out.append('  <div class="ndb-item">')
        out.append(f'    <div class="ndb-cat">{e(it["category"])}</div>')
        out.append(f'    <h4>{e(it["headline"])}</h4>')
        out.append(f'    <p>{e(it["body"])}</p>')
        out.append(f'    <p class="ndb-plain"><b>In plain terms</b>{e(it["plain"])}</p>')
        out.append(f'    <p class="ndb-why"><b>Why it matters</b>{e(it["why"])}</p>')
        if it["sources"]:
            links = " · ".join(
                f'<a href="{e(s["url"])}" target="_blank" rel="noopener noreferrer">'
                f'{e(s["outlet"])}</a>'
                for s in it["sources"]
            )
            out.append(f'    <p class="ndb-src">Sources: {links}</p>')
        out.append("  </div>")

    out.append("</div>")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="path to a published brief HTML file")
    ap.add_argument("--out", default=".", help="output directory (default: cwd)")
    args = ap.parse_args()

    page = pathlib.Path(args.source).read_text(encoding="utf-8")
    feed = parse(page)

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    blob = json.dumps(feed, indent=2, ensure_ascii=False) + "\n"
    (out / "latest.json").write_text(blob, encoding="utf-8")
    (out / f"{feed['date']}.json").write_text(blob, encoding="utf-8")
    (out / "static.html").write_text(static_html(feed), encoding="utf-8")

    print(f"{feed['dateLabel']} — {len(feed['items'])} items, "
          f"{len(feed['tldr'])} tldr lines")
    print(f"wrote {out/'latest.json'}, {out/(feed['date']+'.json')}, {out/'static.html'}")


if __name__ == "__main__":
    main()
