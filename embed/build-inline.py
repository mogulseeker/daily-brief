#!/usr/bin/env python3
"""
Regenerate snippet.html and brief-embed.html from brief-embed.js.

    python3 build-inline.py

brief-embed.js is the single source of truth for the widget. This script
derives the two paste-able forms from it:

    snippet.html      the two-line loader (recommended)
    brief-embed.html  the all-in-one inline fallback

Run it after any edit to brief-embed.js, then commit all three.

Deliberately stdlib-only.
"""

import pathlib
import subprocess
import sys

FEED = "https://mogulseeker.github.io/daily-brief/embed/latest.json"
JS = "https://mogulseeker.github.io/daily-brief/embed/brief-embed.js"

HERE = pathlib.Path(__file__).parent
src = HERE / "brief-embed.js"
js = src.read_text(encoding="utf-8")

# brief-embed.js must stay pure ASCII. A smart quote inside one of its string
# literals is a live hazard: straightened in transit it closes the literal
# early, throws SyntaxError, and takes down the whole <script> with no visible
# error - the page just renders blank. Fail loudly rather than ship that.
bad = [(i, line) for i, line in enumerate(js.splitlines(), 1)
       if any(ord(c) > 127 for c in line)]
if bad:
    print("brief-embed.js contains non-ASCII - use \\uXXXX escapes instead:",
          file=sys.stderr)
    for i, line in bad:
        print(f"  line {i}: {line.strip()[:80]}", file=sys.stderr)
    raise SystemExit(1)

# Cheap but real syntax gate, when node happens to be around.
try:
    subprocess.run(["node", "--check", str(src)], check=True,
                   capture_output=True)
    print("node --check: OK")
except FileNotFoundError:
    print("node not found - skipping syntax check")
except subprocess.CalledProcessError as e:
    print(e.stderr.decode(), file=sys.stderr)
    raise SystemExit("brief-embed.js does not parse")

snippet = f'''<!-- Daily Brief - paste this into your page. That is the whole thing. -->
<div class="daily-brief-embed"
     data-feed="{FEED}"
     data-show="full"
     data-theme="light"></div>
<script src="{JS}"></script>
'''
(HERE / "snippet.html").write_text(snippet, encoding="utf-8")

# A literal </script> inside the JS (it appears in the header comment) would
# close the host <script> element early, so neutralise it on the way in.
inline = js.replace("</script>", "<\\/script>")

allinone = f'''<!-- Daily Brief - all-in-one embed (no external script).
     GENERATED FROM brief-embed.js by build-inline.py. Do not hand-edit.

     Prefer snippet.html: it is ~300 characters instead of ~11KB, which matters
     because Google Sites caps its embed-code box at 10,000 characters, and a
     pasted script can be corrupted in transit (a curly apostrophe becoming a
     straight one is enough to kill the entire block silently). -->
<div class="daily-brief-embed"
     data-feed="{FEED}"
     data-show="full"
     data-theme="light"></div>
<script>
{inline}</script>
'''
(HERE / "brief-embed.html").write_text(allinone, encoding="utf-8")

for name in ("snippet.html", "brief-embed.html"):
    n = len((HERE / name).read_text(encoding="utf-8"))
    flag = "  <- over the Google Sites 10,000 char limit" if n > 10000 else ""
    print(f"wrote {name} ({n} chars){flag}")
