# Embedding the brief on your website

## Why you can't just iframe it

The Artifact page sends `content-security-policy: frame-ancestors 'self'`, so no other
origin is allowed to frame it. Even if that header changed, the page needs your claude.ai
login to load, and **each day is a different URL** — so an iframe would break daily anyway.

So the embed works the other way round: the brief is published as a small JSON feed, and a
self-contained widget on your page renders it. One snippet, pasted once, always current.

## The snippet

Paste this into your page. That is the entire integration:

```html
<div class="daily-brief-embed"
     data-feed="https://mogulseeker.github.io/daily-brief/embed/latest.json"
     data-show="full"
     data-theme="light"></div>
<script src="https://mogulseeker.github.io/daily-brief/embed/brief-embed.js"></script>
```

It also lives in [snippet.html](snippet.html). Works anywhere you can put markup — Google
Sites, WordPress (Custom HTML block), Squarespace (Code block), Ghost, Astro, Next.

**Restyling never requires touching the site again.** The widget is served from this repo,
so editing `brief-embed.js` and pushing changes how the brief looks everywhere it is
embedded. Only the four `data-` attributes live on the host page.

### Options

| Attribute | Values | Effect |
|---|---|---|
| `data-feed` | URL | **Required.** Where `latest.json` lives. |
| `data-show` | `full` (default) · `tldr` · `plain` | `tldr` = ten headlines only, good for a sidebar. `plain` = headlines + the plain-English explainers, skipping the dense reporting. |
| `data-limit` | number | Render only the first N items, e.g. `data-limit="5"`. |
| `data-theme` | `auto` (default) · `light` · `dark` | See below. |

Multiple widgets on one page are fine — each is initialised independently.

### Two things it does deliberately

**It renders inside a shadow root.** Your site's CSS cannot leak in and its CSS cannot leak
out. Verified against a host page that force-sets `h2,h3,h4 {color:red !important;
font-family:cursive !important}` and `p {color:magenta !important; line-height:3
!important}` — none of it penetrates.

**`auto` matches the page, not the operating system.** A visitor with dark mode on, reading
your white page, would otherwise get near-white text on white. Instead it walks up the DOM
for the first real background colour and measures its luminance. `data-theme="light"` pins
it, which is what the snippet above does.

## Why the script is hosted rather than pasted inline

The widget used to be one big paste. On Google Sites it rendered as a blank white area with
no error at all. Two independent causes, both inherent to pasting a large script:

1. **Transit corruption.** The source contained `'Loading today's brief'` with a curly
   apostrophe. Straightened anywhere along the way, it closes the string literal early and
   throws `SyntaxError` — and a `<script>` block with a syntax error does not partially
   run, it does not run *at all*. No widget, and no error message either, because the
   widget's own error handler is inside the block that failed to parse. Hence: blank.
2. **Size.** The inline version is ~11.6KB. **Google Sites caps its embed-code box at
   10,000 characters**, so it was being truncated regardless.

Hosting the script fixes both permanently, and shrinks the thing you paste from ~11.6KB to
~300 bytes.

Two guards keep cause 1 dead: `brief-embed.js` is **pure ASCII by construction** (the two
non-ASCII glyphs it needs are written as `\uXXXX` escapes), and `build-inline.py` refuses to
build if that ever stops being true.

## Editing the widget

`brief-embed.js` is the single source of truth. After changing it:

```sh
python3 build-inline.py    # checks ASCII + syntax, regenerates the two paste forms
git add embed/ && git commit -m "Restyle embed" && git push
```

Pages redeploys in about 15 seconds. Nothing on your site needs to change.

`build-inline.py` regenerates:

- **`snippet.html`** — the two-line loader above
- **`brief-embed.html`** — an all-in-one inline fallback, for a host that forbids external
  scripts. Note it exceeds the Google Sites limit, so it is not the path to use there.

## Option B — the static fragment (no JavaScript)

`static.html` is one day's brief as plain, self-contained HTML. Paste it and it renders with
no script and no feed. Use this if your site strips JavaScript.

The tradeoff: it does not update. You'd regenerate and re-paste each day. It also paints its
own background rather than blending — with no JS it can't measure the page, so an explicit
ground is the only way to guarantee the text stays legible in both themes.

## Keeping the feed current

The widget is only as fresh as `latest.json`. The 6am routine writes `embed/latest.json` and
a dated copy into this repo on every run, and GitHub Pages serves them at

```
https://mogulseeker.github.io/daily-brief/embed/latest.json
```

Pages sends `Access-Control-Allow-Origin: *`, so the cross-origin fetch from your site
works. To regenerate by hand from any published brief page:

```sh
python3 build-embed.py path/to/brief-2026-08-17.html --out .
```

Writes `latest.json`, a dated `2026-08-17.json` copy, and `static.html`. Stdlib only.

> A Pages site is public. The feed is readable by anyone with the URL — that is what makes
> the embed work, but it is worth knowing.

## Feed shape

```json
{
  "date": "2026-08-17",
  "dateLabel": "Monday, August 17, 2026",
  "generated": "2026-08-17T17:15:04+00:00",
  "tldr": ["Stripe finalizes a reported $7B+ deal ...", "..."],
  "items": [
    {
      "slot": 1,
      "category": "AI Industry",
      "headline": "Stripe finalizes a reported $7 billion-plus purchase of OpenRouter",
      "body": "Bloomberg reported on August 16 that ...",
      "plain": "Stripe is the company that quietly handles ...",
      "why": "The premium is being paid for the routing layer ...",
      "sources": [{ "outlet": "Bloomberg", "url": "https://..." }]
    }
  ]
}
```

Stable contract — the widget ignores fields it doesn't know, so extra keys are safe to add.

## One editorial note

Publishing the brief on a public page puts summaries of other outlets' reporting in front of
an audience, which is a different footing from reading it yourself. Every item carries its
source links, which is the right practice — keep them in place if you re-style the output,
and the attribution takes care of itself.
