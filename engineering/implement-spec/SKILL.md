---
name: implement-spec
description: Implement a whole spec on one integration branch. Use when a spec has several tickets with blocking edges and the build should run across the ready frontier in parallel, or when the deliverable is one branch to review as a unit.
---

You have been provided a spec. This spec should have tickets associated with it, describing how to implement the spec.

The issue tracker should have been provided to you. If not, tell the user to run `/setup-matt-pocock-skills`.

The goal is the entire spec implemented on a single **integration branch**, with every ticket resolved the way the issue tracker closes work.

The tickets are not a list of steps. They are a **task graph** with blocking relationships between them. This means there is always a **frontier** of tickets which are ready to be grabbed.

Communication to and from subagents should be sparse. Communicate primarily through **context pointers**: to the spec, tickets, research notes, and previous commits. Don't duplicate information already available via pointers.

**Implementer subagents** should be run in the background where possible for maximum concurrency.

## Steps

1. Read the spec and tickets to understand the task graph. Also read `docs/agents/project-standards.md` when it exists: every implementer subagent inherits the same skeleton, naming, and migration rules, so a ticket that contradicts the document is a ticket to re-cut rather than a decision to make inside a worktree.

2. (optional) Use an **exploration subagent** to conduct any exploration required by the tickets - relevant codebase files or external documentation. Ensure the exploration subagent can save files - it should save its markdown notes in a directory outside the repo, accessible by all future subagents. This lets **implementer subagents** focus on implementation rather than exploration.

3. Create the integration branch. If the issue tracker closes work through PRs, or the user asks for one, open a draft PR after the first merge in step 5 (a branch with no commits ahead of main can't open one), marked as closing the spec and tickets.

4. Use **implementer subagents** to implement each ticket, each in its own worktree on its own branch. Each implementer subagent:
   - confirms its worktree is based on the integration branch before starting, and resets onto it if not;
   - reads `docs/agents/project-standards.md` before its first edit, and follows it: where it names a code generator, the skeleton is generated and then extended, never hand-written; where the document and the ticket disagree, the document wins and the conflict is reported in its outcome instead of resolved silently; ⚠️ items are not enforced;
   - calls the Skill tool with `tdd` to build the ticket;
   - drives the repo's `verify-<app>` skill against the behavior it built, where one exists: tests prove the seams, only that skill proves a user can reach the behavior. Where none exists and the ticket is user-facing, report the missing harness in its outcome rather than claiming proof;
   - merges the integration branch tip into its own branch before reporting done

5. Once an **implementer subagent** completes, merge its work to the integration branch with a **merger subagent**.

6. If this changes the **frontier** of available tickets, kick off more **implementer subagents** to work on the new tickets. This allows for maximum concurrency.

7. Once all tickets are complete, call the Skill tool with `code-review` on the integration branch. Fix all issues raised by the code review in a single **implementer subagent**.

8. If a draft PR exists, mark it ready for review. Otherwise, resolve each ticket the way the issue tracker closes work, and report the integration branch.

9. Clean up all **implementer subagent** worktrees.
