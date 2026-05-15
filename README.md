# Relentless Shared Config

Source of truth for shared configuration across Relentless's internal agents (Coach, GHL agent, eQuote bot, future tooling).

## What's in here

| File | Purpose |
|---|---|
| `rep-slack-mapping.json` | One row per rep. Maps display name, GHL name, emails, Slack ID, market, role, and flags. Consumed by both Coach and Matt's GHL agent. |
| `.github/workflows/validate-mapping.yml` | Runs on every PR. Blocks merge if schema is invalid, emails/Slack IDs are duplicated, etc. |
| `.github/scripts/validate_mapping.py` | The validator. Edit here to extend the schema. |

## How to change the rep mapping

1. Open a pull request against `main` with your edit to `rep-slack-mapping.json`.
2. The validation action runs automatically. If it fails, read the error message in the PR check output and fix.
3. CODEOWNERS requires review from @joshuaholland05 AND @relentlessmatt before merge.
4. After merge, both Coach and the GHL agent pick up the change on their next scheduled run (they fetch this file at runtime).

## Schema

See the `_schema` block at the top of `rep-slack-mapping.json` for inline documentation of every field.

Required values:
- `role`: one of `setter | closer | manager | founder | ops`
- `flags`: subset of `veteran | leader`
- `markets`: subset of `AZ | UT`
- `slack_id`: format `U` + 8–11 alphanumeric chars, or `null`
- `active=false` requires `inactive_since` (ISO date)

## Consumers

| Agent | Owner | How it reads this file |
|---|---|---|
| Coach | Josh | Fetches `https://raw.githubusercontent.com/.../rep-slack-mapping.json` at startup with `SHARED_CONFIG_PAT`. Falls back to local cache, then bundled defaults. |
| GHL agent (`daily-pipeline-check`, `contract-signed-watch`) | Matt | Same pattern. Falls back to local cache. Skips DMs entirely if no cache. |

## How to add a new rep

1. Get their email, Slack ID (or leave null and let the agents resolve by email), market, and role.
2. Add a new object to the `reps` array. Copy the structure of an existing entry.
3. Open PR. Validation will catch typos.

## How to deactivate a rep

Set `active: false` and `inactive_since: "YYYY-MM-DD"`. Don't delete the entry — historical data still references it.
