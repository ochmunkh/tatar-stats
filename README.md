# Tatar Projects — GitHub Repository Statistics

Live dashboard of GitHub traffic (clones, unique cloners, views, unique visitors)
for the Tatar ecosystem, aggregated across all repos with all-time totals and
14-day growth.

**Live page:** https://ochmunkh.github.io/tatar-stats/

## How it works

- `index.html` — the dashboard (GitHub Pages). Reads `data.json`.
- `collect.py` — fetches each repo's traffic via the GitHub API and accumulates
  it into `history.json` (all-time) + `data.json` (what the page shows).
- `.github/workflows/update-stats.yml` — runs **weekly** (Mondays) and on manual
  trigger, then commits the refreshed data.

GitHub's traffic API only keeps the **last 14 days**, so the stats are summed up
over time. Numbers up to the baseline date (2026-10-05) are kept as a fixed
baseline; newer days are added on top.

## One-time setup: the `STATS_TOKEN` secret

The workflow needs a token that can read **traffic** for the Tatar repos
(the repo's built-in token can't read other repos' traffic).

1. Create a token at **GitHub → Settings → Developer settings → Personal access tokens**:
   - *Classic:* scope **`repo`**, or
   - *Fine-grained:* repository access = the 5 Tatar repos, permission
     **Administration → Read-only**.
2. In **this repo → Settings → Secrets and variables → Actions → New repository secret**:
   - Name: `STATS_TOKEN`
   - Value: the token
3. Run it once: **Actions → Update Tatar stats → Run workflow**.

To add/remove repos, edit the `REPOS` list in `collect.py`.
To change the schedule, edit the `cron` line in the workflow.
