# Daily Brief

A ten-item news brief, delivered every morning at ~6am Mountain Time.

## What arrives, and where

| Channel | When | What | Status |
|---|---|---|---|
| **Slack DM** | ~6:10am MT | The ten TL;DR headlines + a link to the full page | ✅ live |
| **Artifact page** | ~6:10am MT | The full formatted brief, a new URL each day | ✅ live |
| **Google Drive `daily-brief/`** | ~6:10am MT | Canonical markdown, one file per day | ✅ live |
| **`briefs/YYYY-MM-DD.md`** | ~7:20am MT | Same markdown, on this Mac | ⏳ needs one grant |

> [!IMPORTANT]
> ## One step left: let Claude see this repo
>
> The local-disk archive is the only leg not yet running. The cloud routine can't commit
> to `mogulseeker/daily-brief` until the Claude GitHub App is granted access to it —
> attempting to attach the repo returns `403 You don't have access to a repository this
> routine uses`.
>
> **Fix:** go to <https://github.com/settings/installations> → **Claude** → **Configure** →
> under *Repository access* add **`daily-brief`** → Save.
>
> Then tell Claude *"the GitHub grant is done"* and it will switch the routine over to the
> repo (step 5c commits to `briefs/` instead of Drive, and `prompt.md` becomes the live
> spec). Until then the archive lives in Drive and `briefs/` stays empty — nothing else is
> affected, and the 6am brief still arrives on Slack and the web.
>
> The launchd job is already installed and tested, so it starts populating `briefs/` the
> moment the routine begins committing.

## The ten slots

Fixed order, every day:

1. 🤖 AI Industry — most important story
2. 🌍 International Affairs — most important story
3. 📉 Economics — most important story
4. 🏥 Healthcare — most important story
5. 🃏 Wildcards ×4 — next four most important from those same four categories, ranked by
   overall importance. Not one-per-category: a heavy AI day can yield three AI wildcards.
6. 🔴 Trump Watch — absurdities and corruption, anchored to the documented record
7. 💻 Tech — most important non-AI technology story

Each item has four parts:

1. **Headline** — plain language, no clickbait
2. **What happened** — two or three sentences, with the actual numbers
3. **In plain terms** — the same story explained to a bright 14-year-old: every proper noun
   and piece of jargon unpacked, the mechanism explained rather than just the outcome, and the
   genuinely interesting part (the irony, the catch) pointed at directly
4. **Why it matters** — one sentence on the second-order effect

Plus sources. ~700 words of reporting plus the explainers, so roughly a 5-minute read.

The "In plain terms" rules are deliberately strict about tone: simple words, adult register.
No forced analogies, no "imagine a lemonade stand," and it must carry any uncertainty down
from the reporting rather than sounding more confident than the sources do.

## How it works

```
   6:04am MT   Cloud routine "Daily Brief" fires (Anthropic cloud, not this Mac)
               │
               ├─ WebSearch/WebFetch across the six research areas
               ├─ picks 10 items, writes the brief
               ├─ publishes the Artifact page ─────────────► claude.ai
               ├─ DMs the TL;DR + link ───────────────────► Slack
               └─ commits briefs/YYYY-MM-DD.md ───────────► github.com/mogulseeker/daily-brief
                                                                    │
   7:20am MT   launchd runs sync/sync-briefs.sh ◄────────────────────┘
               └─ git pull --ff-only  →  briefs/ on this Mac
```

The split exists because cloud routines cannot write to local disk, and the local
`claude -p` CLI has no Slack or Drive connectors. Git is the transport that both halves
can reach, which also means the local sync is plain `git pull` — no AI, no API cost, no
auth to expire.

## Embedding it on a website

The brief is live on the website via a two-line paste:

```html
<div class="daily-brief-embed"
     data-feed="https://mogulseeker.github.io/daily-brief/embed/latest.json"
     data-show="full"
     data-theme="light"></div>
<script src="https://mogulseeker.github.io/daily-brief/embed/brief-embed.js"></script>
```

The routine writes `embed/latest.json` on every run and GitHub Pages serves it, so the page
updates itself each morning with nothing to do by hand.

Restyling ships from this repo: edit `embed/brief-embed.js`, run `python3
embed/build-inline.py`, push. The site is never touched again. See
[embed/README.md](embed/README.md) for the options, and for why the script is hosted rather
than pasted inline (short version: a pasted 11KB script hit both the Google Sites
10,000-character embed cap and a smart-quote syntax error that rendered the page silently
blank).

## Operating it

**Routine ID:** `trig_016kS3fazqeubeLeWGrSULfG`
**Dashboard:** https://claude.ai/code/routines/trig_016kS3fazqeubeLeWGrSULfG

The schedule is `4 12 * * *` in **UTC**, which is 6:04am MDT. Minute 4 rather than 0 to
stay off the top-of-hour spike.

> [!IMPORTANT]
> **DST shifts this.** When Mountain time falls back to MST (UTC−7) on **Nov 1, 2026**,
> `4 12 * * *` UTC becomes **5:04am** local. To keep it at 6am, update the routine to
> `4 13 * * *` then, and back to `4 12 * * *` at the March spring-forward.

### Changing what the brief covers

Edit [prompt.md](prompt.md), commit, push. That's the whole loop — **once the GitHub grant
above is done.** The routine's prompt then becomes a three-line bootstrap that pulls this
repo and reads `prompt.md`, so the file genuinely is the spec: no second copy to keep in
sync, no routine update needed.

> [!NOTE]
> **Until the grant:** the routine carries its own inline copy of the spec (the variant that
> writes to Drive rather than git). `prompt.md` is the intended spec and differs from what's
> live in exactly that one respect — step 5c. Edits to `prompt.md` won't affect the brief
> yet; ask Claude to push them to the routine, or just do the grant and be done with it.

### Debugging a missed or bad brief

Ask Claude, or use `RemoteTrigger` directly:

- `{action: "get", trigger_id: "trig_016kS3fazqeubeLeWGrSULfG"}` — is it enabled? next run?
- `{action: "list_runs", trigger_id: "..."}` — recent runs, newest first
- `{action: "get_run_log", session_id: "cse_..."}` — full tool-by-tool log of one run
- `{action: "run", trigger_id: "..."}` — fire it now

An empty `list_runs` does not prove it never fired — check `get` for `enabled` and
`next_run_at`.

For the local half: `sync/sync.log` records every pull with a before/after brief count.

### Changing the schedule or the format

Both are one-line changes — the cron expression on the routine, or the slot table in
[prompt.md](prompt.md) (then push it, per above).

## Known constraints

- **Egress proxy.** The cloud sandbox blocks some news domains (`apnews.com`,
  `techstartups.com` confirmed). The prompt tells the agent to skip blocked hosts rather
  than retry, and to source from WebSearch snippets when fetching fails.
- **Model.** Runs on `claude-opus-5` — the whole product is editorial judgment about what
  matters, which is the wrong place to economize. Switch to `claude-sonnet-5` in
  `job_config.ccr.session_context.model` if you want it cheaper.
- **Artifact pages accumulate.** One new page per day, ~365/year in your gallery. The
  alternative (one page updated in place) would need the URL persisted between runs and
  would destroy the archive, so per-day pages won.
- **Slack formatting.** Slack mangles heavy markdown, so the DM is deliberately the
  compact TL;DR plus a link, not the full brief. The "In plain terms" explainers live on the
  Artifact page and in the markdown archive.
