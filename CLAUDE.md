# ForgeReels workspace

This folder is a video studio. The user clones it once and makes every video inside it.

- Video work starts with the `/forge-reels` skill (`.claude/skills/forge-reels/SKILL.md`). Read it first.
- Each video gets its own folder: `reels/<yyyy-mm-dd>-<slug>/`. Keep all of that video's files inside it.
- Finished videos go to `output/<slug>.mp4`. Drafts and QC material stay in the video's folder.
- Brand packs live in `brand/<name>/` (brand.md, MOTION.md). Read the right one before designing.
- Reference reels and example projects live in `references/`. Study them for style; never copy them.
- Tools and models live outside this folder in `~/forge-reels` (venv, models, caches), set up by
  `bash setup/setup-mac.sh`. Run scripts with `~/forge-reels/venv/bin/python -I <script>`.
- Never commit anything under `reels/`, `output/` or reference media: they are the user's own work.
