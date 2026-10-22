#!/usr/bin/env python3
"""Structure and copy-parity checks for this skill repository.

Checks, in order:
  1. structure    every bucket child is a skill dir with a SKILL.md
  2. frontmatter  `name` exists, matches the directory name, no duplicates
  3. invocation   `disable-model-invocation` agrees with agents/openai.yaml
  4. index        each bucket README lists every skill exactly once
  5. counts       the root README's per-bucket counts match reality
  6. parity       the Proma copy is identical to this repo except the `version` line

Exit code is 0 when every check passes, 1 otherwise. Deliberate divergences must be
registered in scripts/proma-divergence.yaml with a reason; unregistered drift fails.

Usage:
    python scripts/check_consistency.py [--proma-root PATH] [--quiet]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BUCKETS = ("engineering", "productivity")
DEFAULT_PROMA = Path(r"C:\Users\sam\Documents\codes\Proma\apps\electron\default-skills")
ALLOW_FILE = REPO / "scripts" / "proma-divergence.yaml"

problems: list[str] = []
notes: list[str] = []


def rel(p: Path) -> str:
    try:
        return p.relative_to(REPO).as_posix()
    except ValueError:
        return str(p)


def read_lines(p: Path) -> list[str]:
    """Universal-newline read; keeps no line terminators."""
    return p.read_bytes().decode("utf-8-sig").replace("\r\n", "\n").split("\n")


def parse_frontmatter(lines: list[str]) -> dict[str, str] | None:
    if not lines or lines[0].strip() != "---":
        return None
    out: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return out
        if not line or line[0] in " \t#-" or ":" not in line:
            continue
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip().strip('"').strip("'")
    return None


def load_allowlist() -> dict[str, dict[str, str]]:
    """Minimal reader for scripts/proma-divergence.yaml (no PyYAML dependency).

    One record per skill, keys `reason` and `proma_version`. Handles both
    `reason: text` and the folded block form `reason: >-` followed by
    more-indented lines, because the reasons here are long enough to wrap.
    """
    if not ALLOW_FILE.exists():
        return {}
    entries: dict[str, dict[str, str]] = {}
    current: str | None = None
    collecting: str | None = None
    buffer: list[str] = []
    for line in read_lines(ALLOW_FILE):
        if collecting is not None:
            if line.strip() and line.startswith("      "):
                buffer.append(line.strip())
                continue
            entries[current][collecting] = " ".join(buffer)
            collecting, buffer = None, []
        m = re.match(r"^  ([a-z0-9][a-z0-9-]*):\s*$", line)
        if m:
            current = m.group(1)
            entries[current] = {}
            continue
        if current is None:
            continue
        m = re.match(r"^    ([a-z_]+):\s*(.*)$", line)
        if m:
            key, value = m.group(1), m.group(2).strip()
            if value in (">", ">-", "|", "|-", ""):
                collecting, buffer = key, []
            else:
                entries[current][key] = value.strip('"').strip("'")
    if collecting is not None and current is not None:
        entries[current][collecting] = " ".join(buffer)
    return entries


def discover() -> dict[str, dict]:
    skills: dict[str, dict] = {}
    for bucket in BUCKETS:
        root = REPO / bucket
        if not root.is_dir():
            problems.append(f"structure: bucket directory missing: {bucket}/")
            continue
        for entry in sorted(root.iterdir()):
            if not entry.is_dir():
                continue
            skill_md = entry / "SKILL.md"
            if not skill_md.is_file():
                problems.append(f"structure: {rel(entry)}/ has no SKILL.md")
                continue
            lines = read_lines(skill_md)
            fm = parse_frontmatter(lines)
            if fm is None:
                problems.append(f"frontmatter: {rel(skill_md)} has no closed YAML block")
                continue
            skills[entry.name] = {
                "dir": entry,
                "bucket": bucket,
                "fm": fm,
                "body": lines,
                "path": skill_md,
            }
    return skills


def check_names(skills: dict[str, dict]) -> None:
    seen: dict[str, str] = {}
    for name, meta in skills.items():
        declared = meta["fm"].get("name")
        if not declared:
            problems.append(f"frontmatter: {rel(meta['path'])} has no `name`")
            continue
        if declared != name:
            problems.append(
                f"frontmatter: `name: {declared}` does not match directory `{name}`"
            )
        if declared in seen:
            problems.append(f"frontmatter: duplicate name `{declared}` (also in {seen[declared]})")
        seen[declared] = meta["bucket"]


def check_invocation(skills: dict[str, dict]) -> tuple[int, int]:
    user_invoked = model_invoked = 0
    described_but_user_invoked: list[str] = []
    for name, meta in skills.items():
        fm = meta["fm"]
        is_user = fm.get("disable-model-invocation", "").lower() == "true"
        yaml_path = meta["dir"] / "agents" / "openai.yaml"
        if not yaml_path.is_file():
            problems.append(f"invocation: {name}/ has no agents/openai.yaml")
            continue
        raw = yaml_path.read_text(encoding="utf-8")
        m = re.search(r"allow_implicit_invocation:\s*(true|false)", raw)
        yaml_blocks = m is not None and m.group(1) == "false"
        if re.search(r"display_name:\s*\S", raw) is None:
            problems.append(f"invocation: {name}/agents/openai.yaml has no display_name")
        if re.search(r"short_description:\s*\S", raw) is None:
            problems.append(f"invocation: {name}/agents/openai.yaml has no short_description")
        if is_user and not yaml_blocks:
            problems.append(
                f"invocation: {name} is user-invoked but openai.yaml does not set "
                f"`policy.allow_implicit_invocation: false`"
            )
        if not is_user and yaml_blocks:
            problems.append(
                f"invocation: {name} is model-invoked but openai.yaml blocks implicit invocation"
            )
        if is_user and fm.get("description"):
            described_but_user_invoked.append(name)
        if is_user:
            user_invoked += 1
        else:
            model_invoked += 1
    if described_but_user_invoked:
        notes.append(
            f"invocation: {len(described_but_user_invoked)}/{user_invoked} user-invoked skills "
            f"still carry a description; the root README says to drop it for zero context cost"
        )
    return user_invoked, model_invoked


def check_indexes(skills: dict[str, dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for bucket in BUCKETS:
        readme = REPO / bucket / "README.md"
        in_bucket = {n for n, m in skills.items() if m["bucket"] == bucket}
        counts[bucket] = len(in_bucket)
        if not readme.is_file():
            problems.append(f"index: {bucket}/README.md missing")
            continue
        linked = re.findall(r"\]\(\./([^/()]+)/SKILL\.md\)", readme.read_text(encoding="utf-8"))
        for missing in sorted(in_bucket - set(linked)):
            problems.append(f"index: {bucket}/README.md does not list `{missing}`")
        for extra in sorted(set(linked) - in_bucket):
            problems.append(f"index: {bucket}/README.md lists `{extra}`, which has no SKILL.md")
        for dup in sorted({n for n in linked if linked.count(n) > 1}):
            problems.append(f"index: {bucket}/README.md lists `{dup}` more than once")
    return counts


def check_root_counts(counts: dict[str, int]) -> None:
    readme = REPO / "README.md"
    if not readme.is_file():
        problems.append("counts: root README.md missing")
        return
    text = readme.read_text(encoding="utf-8")
    total = sum(counts.values())
    for bucket, actual in counts.items():
        m = re.search(rf"\| \[{bucket}/\]\(\./{bucket}/README\.md\) \| (\d+) \|", text)
        if m is None:
            notes.append(f"counts: root README has no count row for {bucket}/")
        elif int(m.group(1)) != actual:
            problems.append(
                f"counts: root README says {bucket}/ has {m.group(1)} skills, actual {actual}"
            )
    m = re.search(r"共 (\d+) 个 skill", text)
    if m and int(m.group(1)) != total:
        problems.append(f"counts: root README says {m.group(1)} skills total, actual {total}")


def strip_version(lines: list[str]) -> list[str]:
    return [ln for ln in lines if not ln.lstrip().startswith("version:")]


def check_parity(skills: dict[str, dict], proma: Path) -> None:
    if not proma.is_dir():
        notes.append(f"parity: Proma copy not found at {proma}, check skipped")
        return
    allowed = load_allowlist()
    proma_skills = {p.name for p in proma.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()}
    diverged: set[str] = set()

    for name in sorted(set(skills) - proma_skills):
        problems.append(f"parity: `{name}` is not in the Proma copy, so it never ships")

    for name in sorted(set(skills) & proma_skills):
        theirs = read_lines(proma / name / "SKILL.md")
        fm = parse_frontmatter(theirs)
        if fm is None or not fm.get("version"):
            problems.append(
                f"parity: Proma copy of `{name}` has no `version:`; its "
                f"parseSkillVersion returns 0.0.0 and installed workspaces never upgrade"
            )
        ours = strip_version(skills[name]["body"])
        other = strip_version(theirs)
        if ours == other:
            continue
        diverged.add(name)
        if name in allowed:
            record = allowed[name]
            reason = record.get("reason", "").strip()
            recorded_version = record.get("proma_version", "").strip()
            actual_version = (fm or {}).get("version", "").strip().strip('"')
            if not reason:
                problems.append(
                    f"parity: `{name}` is registered in proma-divergence.yaml without a reason"
                )
            elif not recorded_version:
                problems.append(
                    f"parity: `{name}` is registered without a `proma_version` baseline, so a "
                    f"change on the Proma side would go unnoticed"
                )
            elif recorded_version != actual_version:
                problems.append(
                    f"parity: `{name}` baseline is stale — record says proma_version "
                    f"{recorded_version}, the copy is now {actual_version or 'unversioned'}. "
                    f"The copy moved: re-rule this entry (re-register it, or drop it if the "
                    f"bodies are back in agreement)"
                )
            else:
                notes.append(f"parity: `{name}` diverges by design at copy v{actual_version} — {reason}")
            continue
        delta = len(other) - len(ours)
        problems.append(
            f"parity: `{name}` diverges from the Proma copy beyond the version line "
            f"({delta:+d} lines); register it in scripts/proma-divergence.yaml with a reason"
        )

    for stale in sorted(set(allowed) - diverged):
        if stale not in skills:
            problems.append(f"parity: `{stale}` is registered in proma-divergence.yaml but no longer exists here")
        elif stale in proma_skills:
            problems.append(
                f"parity: `{stale}` is registered as divergent but its body now matches the "
                f"Proma copy; drop the stale entry"
            )

    extra = sorted(proma_skills - set(skills))
    if extra:
        notes.append(
            f"parity: {len(extra)} Proma-only skill(s) not carried here: {', '.join(extra)}"
        )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--proma-root", type=Path, default=DEFAULT_PROMA)
    ap.add_argument("--quiet", action="store_true", help="only print failures and the summary")
    args = ap.parse_args()

    skills = discover()
    check_names(skills)
    user_invoked, model_invoked = check_invocation(skills)
    counts = check_indexes(skills)
    check_root_counts(counts)
    check_parity(skills, args.proma_root)

    if not args.quiet:
        for note in notes:
            print(f"  note  {note}")
    for problem in problems:
        print(f"  FAIL  {problem}")

    total = len(skills)
    spread = ", ".join(f"{b} {c}" for b, c in counts.items())
    print(
        f"\n{total} skills ({spread}) | model-invoked {model_invoked}, "
        f"user-invoked {user_invoked} | {len(problems)} problem(s), {len(notes)} note(s)"
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
