# Daily Brief

A ten-item news brief, delivered every morning at ~6am Mountain Time.

## What arrives, and where

| Channel | When | What |
|---|---|---|
| **Slack DM** | ~6:10am MT | The ten TL;DR headlines + a link to the full page |
| **Artifact page** | ~6:10am MT | The full formatted brief, a new URL each day |
| **`briefs/YYYY-MM-DD.md`** | ~7:20am MT | Canonical markdown, pulled to this repo by launchd |

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

Each item is a headline, two or three sentences of what happened, one "why it matters"
line, and sources. ~700 words total, a 3-minute read.

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

Edit [prompt.md](prompt.md), commit, push. That's the whole loop.

The routine's own prompt is a three-line bootstrap that pulls this repo and reads
`prompt.md`, so the file genuinely is the spec — there's no second copy to keep in sync and
no routine update needed. Add a category, reorder the slots, change the word count, tighten
the sourcing rules: all of it lives in that one file.

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
  compact TL;DR plus a link, not the full 700 words.
