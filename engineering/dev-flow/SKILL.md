---
name: dev-flow
version: 1.1.7
description: The entry procedure for a workspace with the orchestration gate on: classify the request, grade its risk, write a plan snapshot, then route to the skill that does the work.
disable-model-invocation: true
---

# Dev Flow

Every request enters here once the orchestration gate is on for this workspace. Classify, grade risk, snapshot, then hand off. Do not start editing before the snapshot is written.

## 1. Classify

Name the type out loud before routing. When two types fit, say which one you picked and why, so the human can correct it before work starts.

| Type | Chain | Done when |
|---|---|---|
| Defect | `/diagnosing-bugs` → `/code-review` → commit | The regression test goes red then green, the original repro stops reproducing, the `[DEBUG-*]` instrumentation is gone |
| Feature | `/grill-with-docs` → `/to-spec` → `/to-tickets` → `/implement` or `/implement-spec` → `/code-review` → `/pr` | Every ticket's tdd cycle closes, and both review axes pass |
| Restructure | `/codebase-design` → `/implement` → `/code-review` | Behaviour is unchanged, proven by the `verify-<app>` skill, and the shape is smaller or shallower |
| Investigation | `/research` → feeds `/grill-with-docs` or `/to-spec` | A cited Markdown file exists, and it was handed to a flow rather than left standing |
| Answer | Reply directly | Nothing is written to the repo |
| Unsure | `/ask-matt` | The human picks a type and flow returns here |

A one-file change inside a single context window enters at `/implement`. Its steps still call `/tdd` and `/code-review`, so a shortcut skips phases, never discipline.

**Pick the build path after `/to-tickets`, not before.** The choice needs the graph, so state it once the tickets exist:

- Count the **widest frontier**, not the ticket total. A graph that only ever has one ready ticket gains nothing from parallel implementers, so it takes `/implement` per ticket, clearing context between them.
- Two or more ready at once, and four or more tickets overall, is where `/implement-spec` starts paying: one integration branch, implementers in worktrees, `/code-review` once over the branch.
- Both paths call `/tdd` inside and both close with `/code-review`. The choice changes the topology, never the discipline.

**On-ramps** feed the table rather than replacing it:

- A backlog of issues you did not create → `/triage`, which produces agent-ready issues for `/implement`. Do not triage tickets that `/to-tickets` already produced.
- A greenfield effort too large for one session → `/wayfinder`, whose decision map collapses into `/to-spec`. Never route a map straight to `/implement`: the collapse is where the decisions between tickets get carried.
- Structural debt with no concrete request yet → `/improve-codebase-architecture`, whose finding becomes an idea for `/grill-with-docs`.

## 2. Layers that ride along

These are not steps. Never route to them. Each fires on its own trigger or on a cadence, and the chain above stays correct without mentioning them.

Fires whenever its trigger matches:

- `/typescript-best-practices` on any `.ts` or `.tsx` edit, with `/type-system-discipline` and `/boundary-discipline` beneath it as the language-agnostic rules.
- `/unslop` on everything a person reads: the snapshot, the plan, the PR body, and your replies.

Called by hand, at a lifecycle boundary:

- `/recall` before resuming work that did not start in this session, so the first move comes from the record rather than from memory.
- `/project-standards` when the repo has no enforceable standards document, or when a generator, framework, or convention changed under it. Run `generate` once per repo, then `audit` on a cadence. Its output is what `/code-review`'s Standards axis enforces, so a missing document is a missing precondition rather than a step in the chain.
- `/create-verification-skill` when a chain needs proof and the repo has no harness. Generate `verify-<app>` before `/pr` claims evidence, not after.
- `/maintain-verification-skill` on a cadence, or after a feature area moves.
- `/retro` when a session ends, to change the environment rather than the code.

## 3. Grade the risk

Any single hit raises the grade. Do not average them.

- **Low**: read-only, one file, revertible, touches no data and no deploy. Proceed.
- **Medium**: several files, a shared interface, or a new dependency. State the approach, then proceed.
- **High**: data, deploy, anything irreversible, or a cross-module restructure. Write the plan in the snapshot and wait for confirmation before touching code.

## 4. Write the snapshot

The gate section names the snapshot path. Running this without the gate, write `.scratch/flow/snapshot.yaml` at the project root, alongside the specs, tickets, and decision maps the rest of the flow keeps under `.scratch/`. Five lines, nothing else:

```
request: <one sentence, the goal rather than the wording>
type: <from step 1>
risk: <from step 3>
route: <the chain>
preconditions: <what must be true before the first step, or none>
```

`.scratch/` is transient working state rather than a deliverable, and who works on what varies by person, so it belongs in the project's `.gitignore`. When that entry is missing, say so and offer to add it. Never commit a snapshot or a ticket file.

An `Answer` writes nothing, not even the snapshot. This file holds one current plan, so a side question that overwrote it would erase the route out from under work already in flight. The moment a request needs to change a file, it goes back through step 1 and writes a plan.

If the snapshot cannot be written, return `blocked` and name what is missing. Do not skip it and continue: the gate exists because the third fix built on the wrong premise is the expensive one.

## 5. Hand off

Start the chain at its first step. What that means depends on the skill, because the two kinds are not equally reachable:

- **Model-invoked** (`/diagnosing-bugs`, `/research`, `/codebase-design`, `/implement`, `/implement-spec`, `/tdd`, `/code-review`, `/pr`): call it yourself with the Skill tool.
- **User-invoked** (`/grill-with-docs`, `/to-spec`, `/to-tickets`, `/triage`, `/wayfinder`): you cannot call these, and pretending otherwise stalls the run. Name the one to run, give the exact command to type, and say why that one rather than its neighbour, then stop and wait.

Say the one line either way. It is what lets the human redirect before the first edit rather than after the third.

The boundary is deliberate. Deciding what to build and how to split it stays with the person: those steps produce a spec and a set of tickets, and nothing downstream can repair a wrong one. Once the tickets exist, the build, its review, and the PR run on their own.
