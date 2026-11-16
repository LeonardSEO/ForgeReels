# references/

Videos and projects to learn from.

- `examples/`: reference explainers with all their sources (script, facts, scene, visual plan). Build one with
  `python -I .claude/skills/forge-reels/scripts/pipeline/build_explainer.py --project references/examples/touchscreen --render --deliver`.
  They are also regression tests: after any change to the explainer runtime, they must still build and pass.
- Put reels you want to study or match in here (any subfolder). Claude studies each one once
  (`scripts/study_reference.py`: contact sheet, cuts, dark/light switches, timed transcript), writes what it learned
  in the folder's `NOTES.md`, and every new video's brief must name at least three techniques it takes, with its
  own version of each. Learned, never copied.

Video files you add here stay on your machine: media in this folder is ignored by git (only `examples/` is shared).
