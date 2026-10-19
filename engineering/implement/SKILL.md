---
name: implement
description: Implement a unit of work once the tickets exist. Use when a ticket or a settled spec is ready to be built, when work has to be driven test-first at agreed seams, or when the build needs closing out with review and a commit.
---

Implement the work described by the user in the spec or tickets.

If the user passes a ticket reference, fetch it from the issue tracker and state its title before starting. If the reference is ambiguous, ask.

**Read `docs/agents/project-standards.md` before the first edit** when it exists. It decides the skeleton, naming, layering, DDL and migration shape, and the verification floor — reading it after the code is written turns every violation into rework. Three rules bind the read:

- Where it names a **code generator**, generate the skeleton and then extend it; hand-writing what the generator emits is a violation even when the result compiles and looks right.
- Where the document and your plan disagree, **the document wins**. Report the conflict in your outcome instead of diverging quietly; a stale rule is amended by a human through `/project-standards`, not by an implementation choice.
- ⚠️ items are not enforced. Do not treat them as rules, and do not invent a decision for them.

When the repo has no such document and the work is substantial, say so in one line and offer `/project-standards` once, then proceed. Do not block the build on it.

Call the Skill tool with "tdd" where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

When the repo has a `verify-<app>` skill, drive it against the feature you built before calling the work done. Passing tests prove the seams; the verification skill proves a user can reach the behavior. If no harness exists and the work is user-facing, offer `/create-verification-skill` once rather than claiming the behavior works from tests alone.

Once done, call the Skill tool with "code-review" to review the work.

Commit your work to the current branch.
