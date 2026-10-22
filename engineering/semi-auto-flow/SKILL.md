---
name: semi-auto-flow
description: "Entry procedure for one human conversation and no other stops: classify the request, grill the design when it is a larger Feature or a Defect without enough evidence, then carry spec, tickets, implement, review and commit through unattended."
disable-model-invocation: true
argument-hint: "The request to classify and run"
---

# Semi-Auto Flow

The front door for a workspace that wants the design interrogated by the human, and nothing after that interrupted. One phase talks to the user; every phase behind it runs to completion.

This file is self-contained. It carries its own classification table, completion criteria, risk grading, layer list and build-path rule, so no step here sends you to another entry document.

## 1. Opening the skill is the step

Every `/name` below means: load that skill before you use it. Where the host exposes a Skill tool, call it with that name. Where it does not, read the skill's `SKILL.md` and follow it. Either way the file gets opened — the name in the route is not the work.

Naming a skill in the plan and then working from memory leaves no trace that it was ever consulted: the run reads as if it followed `/implement` while `/tdd` and `/code-review` were never opened, and nobody downstream can tell the difference. If the skill cannot be loaded, say which one and do the work inline.

There is no "light" version of a review. Writing `/code-review` in the route and then running a self-check from memory is the failure this rule exists to stop. Either open it and run what it says, or leave it out of the route and say the review did not happen.

## 2. Classify

Name the type out loud before routing. When two types fit, say which one you picked and why, so the human can correct it before work starts. The type decides whether an interview happens, where the chain begins, and what counts as done, so one table holds all three.

| Type | Route | Done when | Interview |
|---|---|---|---|
| Defect | `/diagnosing-bugs` → `/code-review` → commit | The regression test goes red then green, the original repro stops reproducing, and the `[DEBUG-*]` instrumentation is gone | Only when the evidence does not yet support a diagnosis |
| Feature, one file inside one context window | `/implement` | The ticket's tdd cycle closes and both review axes pass | Only when a signal in section 3 hits; otherwise `/implement` directly |
| Feature, larger than one file | `/to-spec` sections → `/to-tickets` slices and blocking edges → `/implement` per ticket in dependency order → `/code-review` | Every ticket's tdd cycle closes and both review axes pass | **Always** |
| Restructure | `/codebase-design` → `/implement` → `/code-review` | Behaviour is unchanged, proven by the `verify-<app>` skill, and the shape is smaller or shallower | Only when a signal in section 3 hits |
| Investigation | `/research` → feeds `/grill-with-docs` or `/to-spec` | A cited Markdown file exists, and it was handed to a flow rather than left standing | No |
| Answer | Reply directly | Nothing is written to the repo | No. Reply and stop |
| Unsure | `/ask-matt`, then return to this table | The human picks a type | No |
| Close-out — the work is already done and the request is to commit, verify or report it | Verify what exists: relevant tests, typecheck, then commit. `/code-review` over the diff first when the change is more than a version bump or a docs-only edit | Relevant tests and typecheck pass, and the work is committed | Only when scope is genuinely ambiguous. Then one round: what goes in, what stays out |

Two boundary rules. A one-file change inside a single context window enters at `/implement`, and its steps still open `/tdd` and `/code-review`, so the shortcut skips phases and never discipline. Close-out is not a Feature: do not borrow the Feature route to cover a commit, and do not start an interview for it unless the scope is genuinely unclear.

## 2.1 The Defect attempt gate

A Defect is the one type where re-entering the route is normal, because its first answer can be wrong in a way that passes review and still fails on the user's machine. This file governs those re-entries, so the chain stays honest about how many times it has been through.

**Attempt 1 is the whole route.** `/diagnosing-bugs` runs to a confirmed cause, `/code-review` runs over the diff, then commit. Nothing about that is provisional.

**Attempt 2 and beyond re-enter at `/diagnosing-bugs` Phase 1, not at the fix.** The gate is one question, and it is answered in the report:

> Did the previous attempt reproduce the user's symptom on the user's path, in a loop that went red?

- **Yes** → the previous attempt reproduced it and the fix did not hold, which is a wrong cause rather than a missing patch. Continue diagnosing; do not write code first.
- **No** → the previous attempt fixed something adjacent and reported it as this bug. Say that plainly, and rebuild the loop on real data before touching source.

The answer is recorded in the snapshot's `loop_seam` (section 11), not in memory: the hop the loop reaches is what makes "did it run the user's path" checkable by a reader instead of arguable by the next attempt.

What this gate forbids is the pattern it exists to break: **attempt N+1 differs from attempt N only by adding a guard to the same layer.** A confirmation dialog, a validation, a clamp, one more interceptor. Each can be defensible on its own and together they are a chain that never located the cause — the symptom moves, so each attempt looks like progress while the cause stays where it was. When you catch yourself adding the second guard to one symptom, that is the signal to re-read the premise, not to write the second guard.

The cost is asymmetric and worth stating once: an extra diagnosis round is a few minutes, while an unreproduced cause leaves the user re-testing builds by hand, one deployment at a time. When the two options are open, take the round.

Every earlier attempt is part of the final report, with what it assumed. A bug that took six attempts and a fixed cause is worth reading; the same six attempts presented as six fixes teaches the next person nothing.

## 3. When the interview is required

Route by type first, then decide whether this request earns a conversation. The table in section 2 already answers this per type; these are the signals that force an interview on a type that would otherwise skip one.

| Signal | Test |
|---|---|
| Undefined term | The request names a concept with no glossary entry, or contradicts an existing one |
| Unconstrained decision | No ADR covers the area being changed, and undoing the choice would be expensive |
| Unknown boundary | A module or interface ownership decision that the project standards do not settle |
| Insufficient evidence | The repro, the failing path, or the responsible layer is still a guess. A bug fixed on a hunch is worse than one left open: ask what the human has actually seen instead of inventing a cause |

A missing file is not a signal by itself. Domain docs are created lazily, so a new repo legitimately has none; treating absence as the trigger fires on every project.

## 4. Run the interview

Load `/grilling`, then run that loop with the human.

`grill-with-docs` is a one-line wrapper whose whole body is "grill and domain-model twice". Load `/grilling` and `/domain-modeling` directly; the wrapper adds nothing loadable.

Ask in rounds, as the loop prescribes. Use a structured question when the choice is structured and you can offer real options; ask in prose when the decision needs the human's own words. Either way the human answers before you move on.

Load `/domain-modeling` as well whenever the conversation coins or challenges a term, or records a decision that would be expensive to reverse. It owns the glossary discipline and the test for when an ADR is warranted.

Fold these into the frontier so the interview settles them in the same pass, instead of leaving them for a later checkpoint:

- The seam the tests will hang on, at the highest point that exists.
- Whether the work splits into tickets at all.
- Ticket granularity and blocking edges, when it does.

Write what the human decides into the snapshot's decision ledger as each answer lands. These are their decisions, not your assumptions: keep the two separate, so a later reader can tell which parts carry human authority and which are your judgement.

## 5. One conversation, then stop asking

A per-request stop at every user-invoked step is two stops too many here. But removing all of them would be the opposite error, because the design decisions are the ones only the human can make.

So consolidate. Every question lands in one front phase; nothing after it asks again.

- The interview is a real conversation with the human. Ask, wait, iterate by rounds. It is not a self-interview, and a ledger of your own guesses is not a substitute for it.
- Everything a later checkpoint would confirm belongs inside that same conversation, raised as part of its frontier. Ask once, in the right place, rather than three times in the wrong ones.
- Once the interview closes, no step asks for confirmation again. A question that surfaces afterwards is answered by your own recorded decision, with a note in the final report naming what a human should re-check.

If the human stops answering, that ends the interview. It does not license inventing their answers: say which design decision is still open and stop the run. Guessing through a decision they were mid-way through is worse than not starting.

## 6. Grade the risk

Any single hit raises the grade. Do not average them.

- **Low**: read-only, one file, revertible, touches no data and no deploy. Proceed.
- **Medium**: several files, a shared interface, or a new dependency. State the approach, then proceed.
- **High**: data, deploy, anything irreversible, or a cross-module restructure. Write the plan in the snapshot and name the rollback path before touching code. The interview was the place a human could have stopped it; once that closes, risk raises the evidence bar rather than adding a stop.

## 7. Layers that ride along

These are not steps. Never route to them. Each fires on its own trigger or on a cadence, and the chains below stay correct without mentioning them.

Fires whenever its trigger matches:

- `/typescript-best-practices` on any `.ts` or `.tsx` edit, with `/type-system-discipline` and `/boundary-discipline` beneath it as the language-agnostic rules.
- `/unslop` on everything a person reads: the snapshot, the spec, the tickets, the PR body, and your replies.

Called by hand, at a lifecycle boundary:

- `/recall` before resuming work that did not start in this session, so the first move comes from the record rather than from memory.
- `/project-standards` when the repo has no enforceable standards document, or when a generator, framework, or convention changed under it. Run `generate` once per repo, then `audit` on a cadence. Its output is what `/code-review`'s Standards axis enforces, so a missing document is a missing precondition rather than a step in the chain.
- `/create-verification-skill` when a chain needs proof and the repo has no harness. Generate `verify-<app>` before `/pr` claims evidence, not after.
- `/maintain-verification-skill` on a cadence, or after a feature area moves.
- `/retro` when a session ends, to change the environment rather than the code.

## 7.1 When a bug crosses a boundary

A defect that touches more than one process is not a defect in the process you happen to be standing in. Two rules, both about not narrowing the frame on your own:

**Name the boundary before choosing a layer.** If the code path runs client → service → datastore, all three are in scope until a hypothesis rules one out. Reading a short payload and concluding that the producer sent too little identifies where the symptom surfaced, not what caused it — and the consumer's response to an unexpected value is a cause candidate with its own evidence.

**The far side's default behaviour is part of the bug.** When a consumer treats an incomplete input as a complete one and destroys what it does not recognise — a hard delete, an overwrite, a truncate with no soft-delete and no undo — then "the producer sent less" is an incident, not a defect. That reframing changes which fix counts, because it makes the destructive default a target rather than a bystander. A client-side guard on top of such a service reduces how often the service is mistreated; it does not make the service safe to mistreat, and the next client will not carry the guard.

Ask of any layer you are about to leave unexamined: what does it do when the value it receives is wrong, and can that be undone? If the answer is "delete, and no", then leaving it unexamined is a decision, not an oversight — say so in the report and give the evidence that would rule it out.

This is also why the Defect gate in section 2.1 exists. Fixes that only ever land on one side of a boundary are the signature of a frame that was never widened.

## 8. Build path and tickets

Load `/to-spec` and `/to-tickets` and follow them. Skip only their checkpoints — the seam check and the breakdown approval — because section 4 already settled both. Everything else in those files applies verbatim, including the spec sections and the tracer-bullet rules.

**Pick the build path after `/to-tickets`, not before.** The choice needs the graph, so state it once the tickets exist:

- Count the **widest frontier**, not the ticket total. A graph that only ever has one ready ticket gains nothing from parallel implementers, so it takes `/implement` per ticket, clearing context between them.
- Two or more ready at once, and four or more tickets overall, is where `/implement-spec` starts paying: one integration branch, implementers in worktrees, `/code-review` once over the branch.
- Both paths open `/tdd` inside and both close with `/code-review`. The choice changes the topology, never the discipline.

Choose `/implement` over `/implement-spec` when the widest ready frontier is one.

Write tickets under `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, one file per ticket, numbered in dependency order, unless a real tracker is configured. Never publish to a tracker that was not configured.

## 9. On-ramps

Work can arrive without a ticket or a type already settled. These feed section 2 rather than replacing it; name the landing skill so the run does not improvise its own version of it.

| Condition | Do this |
|---|---|
| A backlog of issues you did not create | `/triage` produces agent-ready issues for `/implement`. Read the tracker or `.scratch/**/issues/`, deduplicate and group. Where an item does not name a behaviour and an acceptance criterion, that rewrite is a design decision: put it to the human in the interview rather than inventing one. Do not triage tickets that `/to-tickets` already produced. |
| Work too large for one context window | `/wayfinder` produces a decision map: every open decision, its blockers, and your recommended resolution. The map is the interview's agenda. Collapse it into one spec only after the human has ruled on it. Never route a map straight to `/implement`, because the collapse is where the decisions between tickets get carried. |
| Structural debt with no request behind it | `/improve-codebase-architecture` carries the vocabulary, and you **record the finding, do not act on it.** Write it to `.scratch/architecture/<YYYY-MM-DD>-<slug>.md` and leave the run alone. Nobody asked for that refactor, and rearchitecting on your own initiative is indistinguishable from losing the plot. |

## 10. Decide alone after the interview

The interview covers what a human can rule on. It cannot cover what the run only discovers later: a seam that will not hold, a dependency that forces a different split, a test that reveals an unstated rule. Decide those yourself and record them in the assumption ledger: the decision, the reason, a confidence of `high` / `medium` / `low`, the alternative you rejected and why, and what breaks if you are wrong.

A low-confidence assumption does not block the run. It is escalated in the final report instead. Risk `high` does not block either; it raises the evidence bar, so the snapshot names the rollback path and the report leads with it.

## 11. Snapshot

The gate section names the snapshot path. Running this without the gate, write `.scratch/flow/snapshot.yaml` at the project root, alongside the specs, tickets and decision maps the rest of the flow keeps under `.scratch/`.

Two ledgers that must not be merged:

```
request: <one sentence, the goal rather than the wording>
type: <from section 2>
risk: <low | medium | high, from section 6>
route: <the chain>
preconditions: <what must be true before the first step, or none>
loop_seam: <Defect only: the hop the feedback loop reaches, and the hops above it that it covers — per /diagnosing-bugs>
decisions:
  - <what the human decided> | <their reason>
assumptions:
  - <what you decided> | <reason> | <confidence> | <alternative rejected and why> | <what breaks if wrong>
```

An empty `decisions:` block means the interview did not happen and should have. Say so rather than shipping it silently.

On a Defect, `loop_seam` is the field that earns the run its passage out of Phase 1: a loop that stops above the hop the evidence has not yet cleared keeps the run in Phase 1, whatever the rest of the file says.

`.scratch/` is transient working state rather than a deliverable, and who works on what varies by person, so it belongs in the project's `.gitignore`. When that entry is missing, say so and offer to add it. Never commit a snapshot or a ticket file.

An `Answer` writes nothing, not even the snapshot. This file holds one current plan, so a side question that overwrote it would erase the route out from under work already in flight. The moment a request needs to change a file, it goes back through section 2 and writes a plan.

If the snapshot cannot be written, return `blocked` and name what is missing. Do not skip it and continue: the gate exists because the third fix built on the wrong premise is the expensive one.

## 12. Close out

Commit on the current branch and write the PR body with `/pr`. Do not open the PR unless this workspace's `AGENTS.md` grants it explicitly: publishing outward is the one gate this file does not remove.

The final report leads with the decision ledger, then the assumption ledger, then what was built, then what a human should re-check.
