# gistboard

terminal-themed dashboard for [orange723's gists](https://gist.github.com/orange723).

**how it works:** github actions runs daily, fetches all public gists via api, generates a single static html page, and deploys to cloudflare pages.

```
$ gistboard --fetch orange723
$ fetching from api.github.com...
$ found 16 gists (18 files) — last build: 2026-06-03 18:53 UTC
$ ─────────────────────────────────────────────
$ init-system.sh        (1 file)  [Shell]     updated 4mo ago
$ install-ss.sh         (1 file)  [Shell]     updated 4mo ago
...
```
