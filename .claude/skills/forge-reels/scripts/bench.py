#!/usr/bin/env python3
"""Run a command and print one JSON line: {"cmd", "wall_s", "peak_rss_mb", "exit"}.

  python -I bench.py -- <command...>

Peak memory comes from macOS `/usr/bin/time -l` ("maximum resident set size", bytes): the peak of the
LARGEST single process in the tree, not the sum. Right for one Python model process; for Chromium renders
(many processes) it undercounts, so watch `memory_pressure` there. The command's own output passes through;
the JSON line is printed last and the command's exit code is returned.
"""
import json
import re
import shlex
import subprocess
import sys
import time


def main(argv):
    if "--" not in argv or argv.index("--") == len(argv) - 1:
        sys.exit("usage: bench.py -- <command...>")
    cmd = argv[argv.index("--") + 1:]
    t0 = time.monotonic()
    r = subprocess.run(["/usr/bin/time", "-l", *cmd], stderr=subprocess.PIPE, text=True, errors="replace")
    wall = time.monotonic() - t0
    m = re.search(r"(\d+)\s+maximum resident set size", r.stderr)
    # print the command's stderr without time's own report (it starts at the "real/user/sys" line)
    sys.stderr.write(re.split(r"^\s*[\d.]+ real\s", r.stderr, maxsplit=1, flags=re.M)[0])
    print(json.dumps({"cmd": shlex.join(cmd), "wall_s": round(wall, 2),
                      "peak_rss_mb": round(int(m.group(1)) / 2**20, 1) if m else None, "exit": r.returncode}))
    return r.returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
