#!/usr/bin/env python3
"""Mutation tests for check_consistency.py.

A checker that never fails is indistinguishable from no checker. Each case below
copies the repo to a temp directory, plants exactly one defect, and asserts the
checker exits non-zero with the message that names that defect.

The baseline case is the control: no defect, exit 0. If the baseline fails, every
other result is meaningless, so it runs first.

Usage:
    python scripts/test_check_consistency.py [--proma-root PATH]
"""

from __future__ import annotations

import argparse
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_PROMA = pathlib.Path(r"C:\Users\sam\Documents\codes\Proma\apps\electron\default-skills")
IGNORE = shutil.ignore_patterns(".git", ".workbuddy", "__pycache__")


def run(root: pathlib.Path, proma: pathlib.Path) -> tuple[int, str]:
    proc = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "check_consistency.py"),
            "--quiet",
            "--proma-root",
            str(proma),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout + proc.stderr


def staged(proma_root: pathlib.Path):
    """Yield a fresh (repo, proma) copy inside a temp dir."""

    class _Ctx:
        def __enter__(self):
            self._tmp = tempfile.TemporaryDirectory()
            base = pathlib.Path(self._tmp.name)
            self.root = base / "repo"
            self.proma = base / "proma"
            shutil.copytree(REPO, self.root, ignore=IGNORE)
            shutil.copytree(proma_root, self.proma, ignore=IGNORE)
            return self.root, self.proma

        def __exit__(self, *exc):
            self._tmp.cleanup()
            return False

    return _Ctx()


# --- mutations: one planted defect each -------------------------------------

def blank_reason(root: pathlib.Path, proma: pathlib.Path) -> None:
    """A registered divergence whose reason was emptied."""
    p = root / "scripts" / "proma-divergence.yaml"
    p.write_text(
        p.read_text(encoding="utf-8").replace("    reason: >-", '    reason: ""\n    note: >-'),
        encoding="utf-8",
    )


def stale_entry(root: pathlib.Path, proma: pathlib.Path) -> None:
    """An allowlist entry for a skill that in fact matches the copy."""
    p = root / "scripts" / "proma-divergence.yaml"
    p.write_text(
        p.read_text(encoding="utf-8") + '  wizard:\n    reason: "not actually divergent"\n',
        encoding="utf-8",
    )


def unregistered_drift(root: pathlib.Path, proma: pathlib.Path) -> None:
    """A body edit in a skill nobody registered as divergent."""
    p = root / "engineering" / "retro" / "SKILL.md"
    p.write_bytes(p.read_bytes() + b"\r\nan unregistered new line\r\n")


def missing_version(root: pathlib.Path, proma: pathlib.Path) -> None:
    """A Proma copy that lost its `version:` field, so upgrades never land."""
    p = proma / "wizard" / "SKILL.md"
    lines = [ln for ln in p.read_text(encoding="utf-8").split("\n") if not ln.startswith("version:")]
    p.write_text("\n".join(lines), encoding="utf-8")


def name_mismatch(root: pathlib.Path, proma: pathlib.Path) -> None:
    """A frontmatter `name` that drifted from its directory."""
    p = root / "engineering" / "tdd" / "SKILL.md"
    p.write_text(p.read_text(encoding="utf-8").replace("name: tdd", "name: tdd-wrong", 1), encoding="utf-8")


def index_missing(root: pathlib.Path, proma: pathlib.Path) -> None:
    """A bucket README that dropped one skill from its index."""
    p = root / "engineering" / "README.md"
    lines = [ln for ln in p.read_text(encoding="utf-8").split("\n") if "wayfinder/SKILL.md" not in ln]
    p.write_text("\n".join(lines), encoding="utf-8")


def policy_mismatch(root: pathlib.Path, proma: pathlib.Path) -> None:
    """A user-invoked skill whose openai.yaml still permits implicit invocation."""
    p = root / "engineering" / "semi-auto-flow" / "agents" / "openai.yaml"
    p.write_text(
        p.read_text(encoding="utf-8").replace(
            "allow_implicit_invocation: false", "allow_implicit_invocation: true"
        ),
        encoding="utf-8",
    )


def root_count_stale(root: pathlib.Path, proma: pathlib.Path) -> None:
    """A root README count that no longer matches the tree."""
    p = root / "README.md"
    p.write_text(
        p.read_text(encoding="utf-8").replace("| 27 |", "| 26 |", 1),
        encoding="utf-8",
    )


def baseline_drift(root: pathlib.Path, proma: pathlib.Path) -> None:
    """The Proma copy's version moved without the divergence record being revisited."""
    p = proma / "semi-auto-flow" / "SKILL.md"
    text = p.read_text(encoding="utf-8")
    # Version lines are inconsistently quoted across the copy, so match by pattern.
    mutated, count = re.subn(r"^version:\s*[\"']?0\.4\.0[\"']?", 'version: "0.4.1"', text, count=1, flags=re.M)
    assert count == 1, "mutation did not apply: version 0.4.0 not found"
    p.write_text(mutated, encoding="utf-8")


def baseline_missing(root: pathlib.Path, proma: pathlib.Path) -> None:
    """A registered divergence with no recorded baseline version."""
    p = root / "scripts" / "proma-divergence.yaml"
    p.write_text(
        p.read_text(encoding="utf-8").replace('    proma_version: "0.4.0"\n', "", 1),
        encoding="utf-8",
    )


CASES = [
    ("registered divergence with no reason", "without a reason", blank_reason),
    ("stale allowlist entry", "drop the stale entry", stale_entry),
    ("unregistered body drift", "diverges from the Proma copy", unregistered_drift),
    ("Proma copy missing version", "has no `version:`", missing_version),
    ("frontmatter name != directory", "does not match directory", name_mismatch),
    ("bucket README index missing entry", "does not list", index_missing),
    ("user-invoked but yaml allows implicit", "does not set", policy_mismatch),
    ("root README count stale", "root README says", root_count_stale),
    ("divergence baseline no longer matches copy", "baseline is stale", baseline_drift),
    ("divergence registered without a baseline", "without a `proma_version` baseline", baseline_missing),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--proma-root", type=pathlib.Path, default=DEFAULT_PROMA)
    args = ap.parse_args()

    if not args.proma_root.is_dir():
        print(f"proma copy not found: {args.proma_root}", file=sys.stderr)
        print("pass --proma-root, or run scripts/check_consistency.py on its own", file=sys.stderr)
        return 2

    with staged(args.proma_root) as (root, proma):
        code, out = run(root, proma)
    control_ok = code == 0
    print(f"{'PASS' if control_ok else 'FAIL'}  control: no mutation, expect exit 0 (got {code})")
    if not control_ok:
        print("      " + out.strip().replace("\n", "\n      ")[:1200])
        print("\ncontrol failed: every mutation result below would be meaningless")
        return 1

    failures = 0
    for label, expected, mutate in CASES:
        with staged(args.proma_root) as (root, proma):
            mutate(root, proma)
            code, out = run(root, proma)
        caught = code == 1 and expected in out
        print(f"{'PASS' if caught else 'FAIL'}  {label} — expect exit 1 containing {expected!r} (got {code})")
        if not caught:
            failures += 1
            print("      " + out.strip().replace("\n", "\n      ")[:1200])

    print(f"\n{len(CASES) - failures}/{len(CASES)} mutations caught")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
