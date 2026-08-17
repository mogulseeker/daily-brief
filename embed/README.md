# Embedding the brief on your website

## Why you can't just iframe it

The Artifact page sends `content-security-policy: frame-ancestors 'self'`, so no other
origin is allowed to frame it. Even if that header changed, the page needs your claude.ai
login to load, and **each day is a different URL** — so an iframe would break daily anyway.

So the embed works the other way round: the brief is published as a small JSON feed, and a
self-contained widget on your page renders it. One snippet, pasted once, always current.

## Option A — the widget (recommended)

1. Upload **`latest.json`** somewhere your site can serve it. The simplest place is your own
   web root, next to the page — same origin means no CORS to think about at all.
2. Paste the contents of **`brief-embed.html`** into your page.
3. Point `data-feed` at the file:

```html
<div class="daily-brief-embed" data-feed="/latest.json"></div>
```

That's it. No dependencies, no build step, no framework. It works in plain HTML,
WordPress (a Custom HTML block), Squarespace (a Code block), Ghost, Astro, Next — anywhere
you can put markup.

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
out. This is tested against a host page that force-sets `h2,h3,h4 {color:red; font-family:
cursive}` and `p {color:magenta; line-height:3}` — none of it penetrates.

**`auto` matches the page, not the operating system.** The widget's own background is
transparent so it blends into your layout, which means the OS preference is the wrong signal:
a visitor with dark mode on, reading your white page, would get near-white text on white.
Instead it walks up the DOM for the first real background colour and measures its luminance.
Verified both ways with the OS forced to dark. Override with `data-theme` if you want to pin
it.

### If your site sets a strict CSP

The snippet uses an inline `<script>`. If your Content-Security-Policy blocks inline scripts,
either move the script block to its own `.js` file and include it normally, or add the nonce
your site uses. The widget makes exactly one network request — the `fetch` for your feed — so
`connect-src` must allow wherever the feed is hosted.

## Option B — the static fragment (no JavaScript)

`static.html` is one day's brief as plain, self-contained HTML. Paste it and it renders with
no script and no feed. Use this if your site strips JavaScript, or you just want to try the
look.

The tradeoff: it does not update. You'd regenerate and re-paste each day. Note it paints its
own background rather than blending — with no JS it can't measure the page, so an explicit
ground is the only way to guarantee the text stays legible in both themes.

## Keeping the feed current

The widget is only as fresh as `latest.json`. Three ways to keep it updated, easiest first:

1. **Let the routine publish it.** Once the Claude GitHub App has access to
   `mogulseeker/daily-brief` (see the main [README](../README.md) — same grant the local
   `briefs/` archive is waiting on), the 6am routine writes `embed/latest.json` on every run.
   Your server then just needs to `git pull`, or you point `data-feed` at a GitHub Pages URL.
2. **GitHub Pages, cross-origin.** Publish the feed from a *public* repo with Pages enabled
   and point `data-feed` at `https://<user>.github.io/<repo>/latest.json`. Pages sends
   `Access-Control-Allow-Origin: *`, so cross-origin fetch works. Only do this if you're
   comfortable with the feed being publicly readable — a Pages site is public even when
   sourced from a private repo on paid plans.
3. **Manual, right now.** Regenerate from any published brief page and upload:

   ```sh
   python3 build-embed.py path/to/brief-2026-08-17.html --out .
   ```

   Writes `latest.json`, a dated `2026-08-17.json` copy for your archive, and `static.html`.
   Standard library only — nothing to install.

## Feed shape

```json
{
  "date": "2026-08-17",
  "dateLabel": "Monday, August 17, 2026",
  "generated": "2026-08-17T17:15:04+00:00",
  "tldr": ["🤖 Stripe finalizes a reported $7B+ deal …", "…"],
  "items": [
    {
      "slot": 1,
      "category": "AI Industry",
      "headline": "Stripe finalizes a reported $7 billion-plus purchase of OpenRouter",
      "body": "Bloomberg reported on August 16 that …",
      "plain": "Stripe is the company that quietly handles …",
      "why": "The premium is being paid for the routing layer …",
      "sources": [{ "outlet": "Bloomberg", "url": "https://…" }]
    }
  ]
}
```

Stable contract — the widget ignores fields it doesn't know, so extra keys are safe to add.
If you'd rather render it yourself, just fetch the JSON and skip the widget entirely.

## One editorial note

Publishing the brief on a public page puts summaries of other outlets' reporting in front of
an audience, which is a different footing from reading it yourself. Every item carries its
source links, which is the right practice — keep them in place if you re-style the output,
and the attribution takes care of itself.
