# Facts: Git at AI scale (Anthropic Scion, OpenAI Pando)

## Anthropic: "Redesigning source control at Anthropic" (Oct 13, 2026, updated Oct 15)
Source: https://www.anthropic.com/research/redesigning-source-control (read 2026-11-16, full page)

| Claim | Page says |
|---|---|
| Merges per day: about 2,500 in May 2026 | "averaged around 2,500 code changes merged per day" (May 2026) |
| Over 30,000 per day as of September | "as of September, we merged over 30,000 per day" |
| Main branch history almost 100 GB; compressed working copy over 25 GB | as quoted |
| About 25 million checkouts per day for CI | "on the order of 25 million code checkouts per day" |
| Naively over 600 PB of git traffic per day | "over 600 PB of git traffic per day" (if fetched naively) |
| Several hundred internal git mirrors at peak | as quoted |
| Diagnosis: git used as a centralized system; nearly all clients are agents and jobs, always online | as quoted |
| New system: Scion, in-house version control; review tool: Antique | as quoted |
| Server does history, commits, merges, rebases; client keeps a bounded cache; source control via API; jobs often need no local repository | as described |
| Changesets created server-side; moving main = compare-and-swap on one Spanner row | as described |
| Built by a team of seven; fully migrated the monorepo from git in five months, while merges per day grew 10x | as quoted |
| Infrastructure footprint 200x smaller than the git mirroring setup | as quoted |
| CI and research checkouts two orders of magnitude faster (seconds, not minutes) | as quoted |
| CI: 25% CPU capacity win; cache hit rate over 99% per tier | as quoted |
| NOT a replacement for git in general; only for huge monorepos / swarms of agents | "by no means a suitable replacement for git for general use" |
| They expect these problems to be common within 6 to 12 months; offer to work with GitHub, GitLab, OSS | as quoted |
| NOT on the page: that Claude Code caused the growth (only "Claude" models credited for building work); no release plan | do not claim |

## OpenAI: "Scaling Git at OpenAI" (Nov 2, 2026; page also shows Oct 21, 2026)
Source: https://openai.com/index/scaling-git-at-openai/ (full text pasted by the user on 2026-11-16; the page itself
sits behind a bot check)

| Claim | Page says |
|---|---|
| Pando: a new backend for Git repositories, "without ... changing how our team uses Git" | as quoted |
| Pando powers all development in OpenAI's monorepo | "Pando now powers all development in OpenAI's monorepo" |
| Keeps the Git protocol and client; engineers and agents keep their workflows | "retaining compatibility with the Git protocol and client" |
| Cause named: Codex ("Codex has changed the scale and pace of development at OpenAI") | as quoted (unlike Anthropic, they credit their agent) |
| Before: slow fetches and pushes, failed merges, reliability "at times falling below 90%" | as quoted |
| Median push latency cut by nearly 5x = "reduced the latency of the median push by nearly 80%" | MEDIAN, not average |
| Nearly a petabyte of Git data per day | "delivers nearly a petabyte of Git data per day" |
| Over 57 TB of packs in a single hour, over 99% from local disk cache | as quoted |
| Post-merge reliability 99.99% (37 weekdays) | chart label |
| Built with Codex, kick-off to production in 10 weeks; core designed by a single engineer, implemented by teams of agents | as quoted |
| Serving production since April 2026, written in Rust | as quoted |
| How: each branch updated independently (only pushes to the same branch conflict); packfiles reused across fetches | as described |
| Fixes contributed back to upstream Git | as described |

## The shared point (both pages)
Both say agents broke the old setup at their scale. Anthropic left git for Scion (and says it is not for general
use); OpenAI kept Git and rebuilt the server behind it. Neither says Git is dead for normal teams. The reel says
exactly that and no more.
