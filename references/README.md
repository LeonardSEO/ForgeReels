# references/

Videos and projects to learn from.

- `examples/`: three reference explainers with all their sources (script, facts, scene, visual plan). Build one with
  `python -I .claude/skills/forge-reels/scripts/pipeline/build_explainer.py --project references/examples/touchscreen --render`.
  They are also regression tests: after any change to the explainer runtime, they must still build and pass.
- Put reels you want to study or match in here (any subfolder). Claude analyses them for pacing, captions, layout
  and motion (frames + transcript), and makes your video inspired by them, never a copy.

Video files you add here stay on your machine: media in this folder is ignored by git (only `examples/` is shared).
