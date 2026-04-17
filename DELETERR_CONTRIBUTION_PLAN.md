# Plan: Media Deletion Automation — PR #16 Review & Recommendation

## Context

PR #16 proposes adding **Maintainerr** (UI-based rule manager) + **Deleterr** (YAML-configured Python tool) to automate media deletion. However, neither tool can fully implement the exact 3-rule deletion logic finalized in the Gemini conversation.

**Primary recommendation: Fork Deleterr, add the missing conditions, and submit PRs upstream.** Run your fork until PRs are accepted, then switch back to the upstream image. This is faster than building from scratch because all API clients (Plex, Tautulli, Seerr, Radarr, Sonarr), the scheduler, the "Leaving Soon" state machine, and the ARM64 Docker image are already done. Your net-new code is ~270 lines.

Additional requirements beyond the Gemini rules:
- Structured **logging** of every decision and action (Deleterr's `logger.py` already provides this)
- **Extensible rule/collection engine** (Deleterr's `check_*` method pattern + Pydantic schema)
- **Tautulli as authoritative watch state** (Plex watchlists don't always clear after watching); use Tautulli data to also clean up stale watchlist entries

---

## The User's Exact Deletion Rules (from Gemini_conversation.md)

A title is marked for deletion if **any** of these are true:

1. **Total Inactivity**: No one (requester or viewer) has viewed or requested the title for > 12 months
2. **Stale Completion**: Every requester finished the entire season > 6 months ago, AND no one else has watched any part of it in the last 3 months
3. **Abandoned Mid-Watch**: Someone who didn't request it started watching, but no one has returned for > 3 months

**Plus**: Plex watchlist additions count as "requester" status (validated against Tautulli; stale watchlist entries are cleaned up).

---

## Why Copilot's Approach (PR #16) Falls Short

| Requirement | Deleterr | Maintainerr |
|---|---|---|
| Requester vs. non-requester time thresholds (12mo vs. 3mo) | Approximated via `protect_unwatched_requesters` boolean — not time-based | Cannot combine multi-threshold logic across requester/non-requester |
| "All requesters finished entire season" condition | No native concept of season completion per requester | `sw_allEpisodesSeenBy` exists but can't combine with time thresholds |
| Plex watchlist = requester status | Not supported (open issue #60) | Experimental — unreliable |
| Git-friendly config | ✅ YAML | ❌ SQLite database |
| Structured logging / audit trail | Partial | None |
| Extensible rule engine | Partial (`check_*` pattern) | None |
| Watchlist cleanup via Tautulli | ❌ | ❌ |

**Running both tools still doesn't fully implement the rules**, and adds two services on a resource-constrained Raspberry Pi.

---

## What Already Works in Deleterr (No Changes Needed)

| Your Rule | Existing Deleterr Feature |
|---|---|
| Global last-watched threshold | `last_watched_threshold: 365` in `LibraryConfig` → `media_cleaner.py: check_watched_status()` |
| Protect requesters who haven't watched | `protect_unwatched_requesters: true` in `SeerrExclusions` — PR #244, merged Mar 2026 |
| "Leaving Soon" two-phase deletion | `leaving_soon` config block with `tag`/`duration` — `state.py` handles persistence |
| Tautulli and Plex watch providers | `WatchDataProvider` protocol in `modules/watch_provider.py`, with `tautulli.py` and `plex_watch_provider.py` |

---

## Phase 1: Plex Watchlist as Requester (Deleterr Issue #60)

**Good first PR — pure Python + PlexAPI, explicitly requested by the community since Dec 2023.**

**Files to modify:**

- `app/modules/plex.py` — add `get_user_watchlist(username) -> list[str]` using `PlexAPI` (already a dep: `PlexAPI==4.15.16`)
- `app/schema.py` — add `plex_watchlist: bool = False` to `Exclusions` model
- `app/media_cleaner.py: check_exclusions()` — add watchlist check against all configured Plex users

The `PlexAPI` library already supports watchlist queries, so this is mostly plumbing.

**Estimated lines: ~70**

---

## Phase 2: `get_users_who_watched()` Protocol Extension

Enables Rules 1 and 3 by distinguishing who-watched from who-requested.

**Files to modify:**

- `app/modules/watch_provider.py` — add `get_users_who_watched(item) -> list[str]` to `WatchDataProvider` protocol
- `app/modules/tautulli.py` — implement via Tautulli history API, returning usernames with last view date
- `app/modules/plex_watch_provider.py` — implement via Plex `viewedBy` or equivalent

**Estimated lines: ~60**

---

## Phase 3: New `check_*` Methods in `media_cleaner.py`

All Deleterr rule logic lives as `check_*` methods in `MediaCleaner` (return `True` = deletable, `False` = protect).

### Rule 1 — Total Inactivity (`check_no_combined_activity`)

```python
def check_no_combined_activity(self, library, media_data, requesters):
    # 1. Get all requesters from Seerr
    # 2. Get all watchers from watch_provider.get_users_who_watched()
    # 3. Find max(last_activity) across both groups
    # 4. Return True (deletable) if max > no_activity_days
```

Schema addition in `app/schema.py`: `no_activity_days: int = 365` in `LibraryConfig`.

### Rule 3 — Non-Requester Stale (`check_non_requester_stale`)

```python
def check_non_requester_stale(self, library, media_data, requesters):
    # 1. Get all users who watched via get_users_who_watched()
    # 2. Subtract requester list (from Seerr + validated watchlist)
    # 3. Return True if non-requester last_watched > protect_non_requester_days
```

Schema addition: `protect_non_requester_days: int = 90` in `SeerrExclusions`.

**Estimated lines for Rules 1 + 3: ~80**

---

## Phase 4: Season Completion Tracking (Rule 2 — Most Complex)

Determines whether ALL requesters have finished an entire season, then checks the non-requester stale condition.

### New protocol method (`app/modules/watch_provider.py`):

```python
def get_season_completion(self, series_id: int, season_num: int, user: str) -> tuple[int, int]:
    # returns (watched_episodes, total_episodes)
```

### New check method (`app/media_cleaner.py`):

```python
def check_all_requesters_completed_season(self, library, series, season, requesters):
    # For each requester: get_season_completion() == (total, total)
    # AND all completion dates > all_requesters_completed_days ago
    # AND check_non_requester_stale() passes for non-requesters
```

Schema addition: `all_requesters_completed_days: int = 180` in `SeerrExclusions`.

**Estimated lines: ~100**

---

## Watchlist Cleanup via Tautulli

Problem: Plex watchlists don't reliably clear when media is watched, so stale entries would incorrectly classify finished media as "still wanted by requester."

Solution (runs as a pre-evaluation pass before deletion rules):
1. Fetch each user's Plex watchlist
2. For each watchlisted title, query Tautulli for actual completion status
3. If Tautulli confirms completion (>90% for movies, all episodes for season), remove from Plex watchlist via API
4. Log all mutations as structured action entries
5. Proceed to deletion rule evaluation with a clean watchlist

This keeps watchlists representing genuine intent ("I still want to watch this") rather than forgotten history.

---

## Contributing Workflow

```
1. Fork rfsbraz/deleterr, checkout develop branch (not main)
2. Branch naming: feat/watchlist-requester, feat/rule-total-inactivity, etc.
3. make unit  ← fast feedback loop, no Docker needed
4. make test  ← full suite including integration (requires Docker)
5. PEP 8, docstrings on public methods, flake8 (200 char line limit, complexity 10)
6. Commit format: feat(plex): add watchlist exclusion support (issue #60)
7. PR targets develop branch, squash if requested by maintainer
```

### Recommended Contribution Order

1. **Issue #60** — Plex watchlist exclusion (pure Python + PlexAPI, already requested, best first PR)
2. **`get_users_who_watched()` protocol extension** — small interface change, unblocks Rules 1 and 3
3. **`check_no_combined_activity()`** — Rule 1 (Total Inactivity)
4. **`check_non_requester_stale()`** — Rule 3 (Abandoned Mid-Watch)
5. **`get_season_completion()` + `check_all_requesters_completed_season()`** — Rule 2 (Stale Completion, most complex)

---

## docker-compose.yml — Deleterr Fork Entry

Once the fork is building its own image via GitHub Actions:

```yaml
deleterr:
  image: ghcr.io/<yourfork>/deleterr:latest
  container_name: deleterr
  restart: unless-stopped
  environment:
    - TZ=America/Los_Angeles
  volumes:
    - /docker_configs/deleterr:/config
    - ./deleterr/settings.yaml:/config/settings.yaml:ro
  networks:
    - tunnel-network
  depends_on:
    - tautulli
    - overseerr
    - radarr
    - sonarr
```

Switch back to `ghcr.io/rfsbraz/deleterr:latest` once all PRs merge upstream.

---

## Verification Plan

1. Run with `dry_run: true` in `settings.yaml`
2. Inspect Deleterr logs for per-title decision entries (rule triggered, reason, data)
3. Confirm "Leaving Soon" Plex collection populates with expected titles
4. Verify watchlist cleanup log entries reflect correct Tautulli-confirmed completions
5. After validating logic, set `dry_run: false` for live operation
