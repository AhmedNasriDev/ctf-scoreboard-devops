#!/usr/bin/env python3
"""Plant the lab sheet 2 defects in a working copy.

    python3 tools/seed.py --team <your-team-name>

Your team name selects one of several variants, so the team at the next
machine is debugging something else. Run it once, from the root of your
repository, on a clean working tree.

    --commit        make one commit per defect (recommended: your pipeline
                    then has something to react to). The commits are made
                    with --no-verify: one of the defects is a planted
                    credential, and a gitleaks pre-commit hook, if you
                    installed one, would otherwise refuse it -- which is
                    precisely why a hook alone is not a control (lab
                    sheet 2, Exercise 2).
    --dry-run       say what would change and change nothing
    --revert        put everything back, if you have not committed

A word about tools/seeds.dat
----------------------------
The defects are compressed rather than written out in the open, which stops
you reading the answer by accident. It is not encryption and it is not meant
to be: twenty seconds of Python will print the lot.

That is deliberate, and it is the same bargain as the solutions to any
exercise. The graded skill in lab sheet 2 is diagnosing a failure from a pipeline
log, and you cannot be given that skill, only the opportunity to practise it.
The handout therefore asks you to commit your written diagnosis *before* the
commit that fixes anything, and the order of those two commits is what is
marked.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import sys
import zlib
from pathlib import Path
from zlib import crc32

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = HERE / "seeds.dat"
MARKER = ROOT / ".seeded"


def load_variants() -> dict:
    if not DATA.is_file():
        sys.exit(f"missing {DATA}; ask your instructor for the complete bundle")
    raw = zlib.decompress(base64.b64decode(DATA.read_text().strip()))
    return json.loads(raw)


def pick(team: str, names: list[str]) -> str:
    return names[crc32(team.strip().lower().encode()) % len(names)]


def apply_pin(spec: dict, revert: bool, dry_run: bool) -> str:
    """Rewrite one line of requirements.txt.

    Matched by package name rather than by exact text, so that re-pinning
    the manifest -- which has to happen every year, because advisories keep
    being published against versions that were clean when they were chosen
    -- does not break the seeding.
    """
    path = ROOT / "requirements.txt"
    text = path.read_text()
    name = spec["package"]
    line_re = re.compile(rf"(?mi)^{re.escape(name)}\s*==.*$")

    if revert:
        if spec.get("original"):
            text = line_re.sub(spec["original"], text, count=1)
        else:
            text = line_re.sub("", text)
            text = re.sub(r"\n{3,}", "\n\n", text)
    else:
        if line_re.search(text):
            text = line_re.sub(spec["pin"], text, count=1)
        else:
            text = text.rstrip("\n") + "\n" + spec["pin"] + "\n"

    if not dry_run:
        path.write_text(text)
    return "  requirements.txt"


def apply_edit(spec: dict, revert: bool, dry_run: bool) -> str:
    path = ROOT / spec["file"]
    if not path.is_file():
        sys.exit(f"{path} not found -- are you in the repository root?")
    text = path.read_text()

    find, replace = spec["find"], spec["replace"]
    if revert:
        find, replace = replace, find

    if not find:
        # An empty search string matches at offset 0 and would insert the
        # block at the top of the file. Every defect is stored with both
        # sides non-empty precisely so this cannot happen; if it does, the
        # data is wrong and silently mangling the file is the worst answer.
        sys.exit(f"malformed defect for {spec['file']}: empty search string")

    if find not in text:
        if replace and replace in text:
            return f"  already applied in {spec['file']}"
        sys.exit(
            f"cannot patch {spec['file']}: the file has been modified.\n"
            f"Run this on a clean checkout, before you start work."
        )
    text = text.replace(find, replace, 1)

    if not dry_run:
        path.write_text(text)
    return f"  {spec['file']}"


def apply_defect(spec: dict, revert: bool, dry_run: bool) -> str:
    if spec.get("package"):
        return apply_pin(spec, revert, dry_run)
    return apply_edit(spec, revert, dry_run)


def git(*args: str) -> None:
    done = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if done.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed:\n{done.stderr or done.stdout}")


def in_git_repo() -> bool:
    return (ROOT / ".git").exists()


def main() -> None:
    ap = argparse.ArgumentParser(description="Plant the lab sheet 2 defects.")
    ap.add_argument("--team", required=True, help="your team name")
    ap.add_argument("--commit", action="store_true", help="one commit per defect")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--revert", action="store_true", help="undo an uncommitted seed")
    args = ap.parse_args()

    blob = load_variants()
    names = sorted(blob["variants"])
    variant = pick(args.team, names)
    defects = blob["variants"][variant]

    if args.revert:
        for key in ("D4", "D3", "D2", "D1"):
            apply_defect(defects[key], revert=True, dry_run=args.dry_run)
        MARKER.unlink(missing_ok=True)
        print("reverted")
        return

    if MARKER.exists() and not args.dry_run:
        sys.exit("already seeded; use --revert first if you need to start again")

    if args.commit and not in_git_repo():
        sys.exit("--commit needs a git repository")

    print(f"team {args.team!r}: planting four defects")
    for key in ("D1", "D2", "D3", "D4"):
        print(apply_defect(defects[key], revert=False, dry_run=args.dry_run))
        if args.commit and not args.dry_run:
            git("add", "-A")
            git("commit", "-q", "--no-verify", "-m", blob["commits"][key])

    if not args.dry_run:
        MARKER.write_text(
            "This working copy carries the lab sheet 2 defects.\n"
            "Delete this file once you have repaired them.\n"
        )
    print(
        "\nDone. Push a branch, open a pull request, and read the pipeline log.\n"
        "Write your diagnosis and COMMIT IT before you commit any fix."
    )


if __name__ == "__main__":
    main()
