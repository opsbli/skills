---
name: diagnosing-bugs
description: Diagnosis loop for hard bugs and performance regressions. Use when the user says "diagnose"/"debug this", or reports something broken/throwing/failing/slow.
---

# Diagnosing Bugs

A discipline for hard bugs. Skip phases only when explicitly justified.

When exploring the codebase, read `GLOSSARY.md` (if it exists) to get a clear mental model of the relevant modules, and check ADRs in the area you're touching.

## Redact

This skill has you show commands, outputs and captured artifacts. **Redact every secret first**: write `<REDACTED>` in its place. Build loops against env vars, so the credential stays in the environment rather than in what you show. Captured artifacts carry auth headers: quote only the lines that carry the signal.

If the redacted output is not enough to diagnose the bug, say so and ask the user.

## Phase 1: Build a feedback loop

**This is the skill.** Everything else is mechanical. If you have a **tight** pass/fail signal for the bug (one that goes red on _this_ bug), you will find the cause; bisection, hypothesis-testing, and instrumentation all just consume it. If you don't have one, no amount of staring at code will save you.

Spend disproportionate effort here. **Be aggressive. Be creative. Refuse to give up.**

### Ways to construct one, in roughly this order

1. **Failing test** at whatever seam reaches the bug: unit, integration, e2e.
2. **Curl / HTTP script** against a running dev server.
3. **CLI invocation** with a fixture input, diffing stdout against a known-good snapshot.
4. **Headless browser script** (Playwright / Puppeteer) that drives the UI and asserts on DOM/console/network.
5. **Replay a captured trace.** Save a real network request / payload / event log to disk; replay it through the code path in isolation.
6. **Throwaway harness.** Spin up a minimal subset of the system (one service, mocked deps) that exercises the bug code path with a single function call.
7. **Property / fuzz loop.** If the bug is "sometimes wrong output", run 1000 random inputs and look for the failure mode.
8. **Bisection harness.** If the bug appeared between two known states (commit, dataset, version), automate "boot at state X, check, repeat" so you can `git bisect run` it.
9. **Differential loop.** Run the same input through old-version vs new-version (or two configs) and diff outputs.
10. **HITL bash script.** Last resort. If a human must click, drive _them_ with `scripts/hitl-loop.template.sh` so the loop is still structured. Captured output feeds back to you.

Build the right feedback loop, and the bug is 90% fixed.

### Tighten the loop

Treat the loop as a product. Once you have _a_ loop, **tighten** it:

- Can I make it faster? (Cache setup, skip unrelated init, narrow the test scope.)
- Can I make the signal sharper? (Assert on the specific symptom, not "didn't crash".)
- Can I make it more deterministic? (Pin time, seed RNG, isolate filesystem, freeze network.)

A 30-second flaky loop is barely better than no loop; a 2-second deterministic one is tight, a debugging superpower.

### Non-deterministic bugs

The goal is not a clean repro but a **higher reproduction rate**. Loop the trigger 100×, parallelise, add stress, narrow timing windows, inject sleeps. A 50%-flake bug is debuggable; 1% is not, so keep raising the rate until it's debuggable.

### When you genuinely cannot build a loop

Stop and say so explicitly. List what you tried. Ask the user for: (a) access to whatever environment reproduces it, (b) a redacted captured artifact (HAR file, log dump, core dump, screen recording with timestamps), or (c) permission to add temporary production instrumentation. Do **not** proceed to hypothesise without a loop.

### Completion criterion: a tight loop that goes red

Phase 1 is done when the loop is **tight** and **red-capable**: you can name **one command** (a script path, a test invocation, a curl) that you have **already run at least once** (show the invocation and its output, redacted), and that is:

- [ ] **Red-capable**: it drives the actual bug code path and asserts the **user's exact symptom**, so it can go red on this bug and green once fixed. Not "runs without erroring"; it must be able to _catch this specific bug_.
- [ ] **Deterministic**: same verdict every run (flaky bugs: a pinned, high reproduction rate, per above).
- [ ] **Fast**: seconds, not minutes.
- [ ] **Agent-runnable**: you can run it unattended; a human in the loop only via `scripts/hitl-loop.template.sh`.
- [ ] **Seamed**: `seam` and `covers` are written down, and every hop the evidence has not cleared sits inside `covers` (per the seam rule below).

If you catch yourself reading code to build a theory before this command exists, **stop: jumping straight to a hypothesis is the exact failure this skill prevents.** No red-capable command, no Phase 2.

### Reach the deepest seam you can observe

Every hop between the human's click and the stored row can be the one that loses the evidence: **client state → serialised payload → the wire → handler input → domain logic → store.**

Drive the deepest hop you can reach, and name the loop's reach in one line: `seam: <hop>` plus `covers: <hops above it>`. A loop also stubs every bug living behind the hop it stubs, so a harness over a mocked API can decide any hypothesis about the hops above the mock and none about the hops below it — the mock's assumptions become the ceiling of the diagnosis. When no hop owns the symptom yet, locating that hop is the loop's first job, not an assumption to carry into it.

This is the sibling of the fixture rule below, and the two fail differently: an invented fixture fakes the **data**, a shallow seam fakes the **path**. Both produce a loop that goes red for a reason of your own making.

### A loop over your own fixture is not a loop

A harness built from data *you* invented reproduces the bug you already believed in, so it goes red without telling you anything. The failure mode is specific and common: you hypothesize a dirty state, hand-build that state, watch it break, and call it root cause — while the user's actual path never ran.

So the fixture has to come from evidence, not imagination:

- [ ] **The input was captured, not composed.** Real payload, real GET response, real log line, real recorded state. If you had to hand-write it to make the bug appear, say so and keep hunting.
- [ ] **The user's click path ran**, not just your function call. Driving the component and clicking it is evidence; importing a helper and calling it with the values you expect it to receive is not.
- [ ] **It fails the way they saw it.** Assert the same numbers, the same shape, the same ordering. A loop that fails "differently but nearby" is Phase 2's failure mode, caught later.

When you cannot get real data, say so and ask for it rather than manufacturing it. An invented fixture that goes red is worse than no fixture: it buys false confidence and consumes the phases that would have found the cause.

### When a fix does not hold

A fix that survives review and still fails in the user's hands is not a partial success. Go back to Phase 1 and rebuild the loop against the **new** observation, because the old loop asserted a symptom that was never the real one.

Two guards, both cheap:

- **Do not stack another fix on top.** Each unverified attempt narrows the search space without a single confirmed cause, and three confirmations in a row is not diligence — it is a loop with no exit condition. If the second attempt on the same premise fails, the premise is what needs examining, which is the first line of Phase 3.
- **Change the premise, or change the layer.** A fix that survives means the guess about *where* was wrong, not that the guess was slightly off. Adding a confirmation dialog to a symptom you never reproduced is the clearest example: it hardens the path you happened to observe and leaves the path that actually broke untouched.

## Phase 2: Reproduce + minimise

Run the loop. Watch it go red as the bug appears.

Confirm:

- [ ] The loop produces the failure mode the **user** described, not a different failure that happens to be nearby. Wrong bug = wrong fix.
- [ ] The failure is reproducible across multiple runs (or, for non-deterministic bugs, reproducible at a high enough rate to debug against).
- [ ] You have captured the exact symptom (error message, wrong output, slow timing) so later phases can verify the fix actually addresses it.

### Minimise

Once it's red, shrink the repro to the **smallest scenario that still goes red**. Cut inputs, callers, config, data, and steps **one at a time**, re-running the loop after each cut, and keep only what's load-bearing for the failure.

Why bother: a minimal repro shrinks the hypothesis space in Phase 3 (fewer moving parts left to suspect) and becomes the clean regression test in Phase 5.

Done when **every remaining element is load-bearing**: removing any one of them makes the loop go green.

Do not proceed until you have reproduced **and** minimised.

## Phase 3: Hypothesise

### The repeat-attempt check comes first

**Check for a repeat attempt first.** If two or more earlier fixes share one premise and all failed the same gate, the premise is now the suspect, not the bug. Write it as one sentence: the thing every failed fix assumed. Then find an observation that would come out differently if it were false, and run it. Look at how the failures are distributed, not just how big each one was. Do not rank a hypothesis that assumes the premise until that check has run. If it confirms the premise, the earlier fixes likely treated a consequence, so ask the next "why". If it contradicts, the cause is elsewhere, and what the failures have in common is what the premise failed to predict.

That check is not optional and it is not a mood. On the second attempt at one bug, before you generate any new hypothesis, you owe three artifacts:

1. **The shared premise, in one sentence**, written down where the next reader can find it.
2. **An observation that discriminates it** — something that comes out differently if the premise is false, plus the run that shows which way it comes out.
3. **A statement of what you are now assuming instead**, and why the previous attempts could not have seen it.

The tell that you skipped it: your new hypotheses differ from the old one only in detail. "Maybe it is the X handler this time" after "maybe it is the X handler" is the same premise with a fresh verb. Detail-level variety across attempts is the symptom the check exists to catch, not evidence that you are converging.

### Read the shape of the number

Before ranking causes, look at what the wrong value *looks like*. The surviving subset is often more informative than the count, and it costs one pass:

- **A prefix or suffix of the previous good value** ("80 became 3, and they are the first 3 in the same order") points at a truncation, a slice, a page cap, or an index that ran off the end — not at a user mistake and not at a single bad record.
- **A contiguous or alternating subset** points at filtering, sampling, or a merge that lost a branch.
- **Scattered survivors that each kept something real** (ids, timestamps, nested objects) point at identity-based removal: duplicate keys, a map keyed the wrong way, an overwrite in a loop.
- **Counts that land on a round number, or exactly repeat an earlier good value**, point at a default, a cap, or a stale read rather than at arithmetic on the data.
- **A change that appears only on the second edit of the same object** points at state that survives the first save: a stale snapshot, a cache, an alias to the array being written.
- **The same shape with a different amount each attempt** ("80 became 3, then 79, then 2") points at one mechanism whose **window** depends on the data — a pattern removing an interval, a boundary set by a position, an ordering-dependent merge — not at N places that each delete something. A fix that shrinks the amount without changing the shape treated a consequence.

Write the shape down in the hypothesis list. A guess that cannot explain the shape is wrong even when it explains the count.

### Then rank

Generate **3–5 ranked hypotheses** before testing any of them. Single-hypothesis generation anchors on the first plausible idea.

Each hypothesis must be **falsifiable**: state the prediction it makes.

> Format: "If <X> is the cause, then <changing Y> will make the bug disappear / <changing Z> will make it worse."

If you cannot state the prediction, the hypothesis is a vibe: discard or sharpen it.

**Show the ranked list to the user before testing.** They often have domain knowledge that re-ranks instantly ("we just deployed a change to #3"), or know hypotheses they've already ruled out. Cheap checkpoint, big time saver. Don't block on it; proceed with your ranking if the user is AFK.

### Spread the hypotheses across layers

A bug that crosses a boundary has a cause on at least one side of it, so the list has to cover both. Reading a request, seeing a short payload, and concluding "the front end sent less" names the *symptom's* location, not its cause — the other end of that same boundary can turn a short payload into irreversible damage, and that is worth ruling in or out deliberately.

So when the bug spans a client, a service, and a datastore, reserve at least one slot for each of:

- **The producer**: what built the value that arrived wrong.
- **The consumer**: what it did with a value it did not expect — including whether it validated, whether it fails safe or fails destructive, and whether it is reversible at all.
- **The contract**: the agreement between them. Who defines the complete set, who is allowed to send a partial one, and what a partial one is interpreted to mean.
- **The wire**: what carried the value between them — proxy, gateway, filters, body rewriting, content coding. A rewriter on the wire hands on a payload short enough to survive, complete enough to parse, and wrong.

A destructive default on the consumer side — deleting, overwriting, truncating — makes "the producer sent less" an incident rather than a bug, and that framing changes which fix counts as the fix. Skipping the consumer slot is how a chain of client-side patches gets built on top of a service that was never safe to underfeed.

When the earlier attempts all landed on the same layer and none held, that is itself the diagnosis: move a slot, don't re-rank the same layer harder.

### Count the quantity at every hand-off

The slots above are settled by one measurement, not by argument. When the symptom is a quantity — N rows, N items, N bytes — count the same action at each hop and find the first hop where the number changes:

| Hop | Read it from |
|---|---|
| Producer serialised | the client's payload panel, or one log line at the call site |
| The wire | proxy / gateway / access log, the request's `Content-Length` |
| Consumer received | request-body log, binding trace, audit table |

Two hops agree and one differs: the differing pair names the layer, and the rest of Phase 3 starts there. All three agree: the cause is downstream of the consumer. That is one request and one query, against a day of hypotheses about the hops that agreed.

A payload that arrives **shorter but still well-formed** is the wire's fingerprint: something rewrote it, rather than failing to read it. Sanitizers, XSS filters, HTML tag strippers, `Content-Length` truncation, decompression limits and template engines all read the body, clean it, and hand on a shorter one — so both ends behave correctly, the producer having sent a complete value and the consumer having honestly processed an incomplete one. Suspect the wire before re-ranking either end.

## Phase 4: Instrument

Each probe must map to a specific prediction from Phase 3. **Change one variable at a time.**

Tool preference:

1. **Debugger / REPL inspection** if the env supports it. One breakpoint beats ten logs.
2. **Targeted logs** at the boundaries that distinguish hypotheses.
3. Never "log everything and grep".

**Tag every debug log** with a unique prefix, e.g. `[DEBUG-a4f2]`. Cleanup at the end becomes a single grep. Untagged logs survive; tagged logs die.

**Perf branch.** For performance regressions, logs are usually wrong. Instead: establish a baseline measurement (timing harness, `performance.now()`, profiler, query plan), then bisect. Measure first, fix second.

## Phase 5: Fix + regression test

Write the regression test **before the fix**, but only if there is a **correct seam** for it.

A correct seam is one where the test exercises the **real bug pattern** as it occurs at the call site. If the only available seam is too shallow (single-caller test when the bug needs multiple callers, unit test that can't replicate the chain that triggered the bug), a regression test there gives false confidence.

**If no correct seam exists, that itself is the finding.** Note it. The codebase architecture is preventing the bug from being locked down. Flag this for the next phase.

If a correct seam exists:

1. Turn the minimised repro into a failing test at that seam.
2. Watch it fail. If you forced the red by mutating code or a fixture, `diff` against a pristine copy to prove the mutation landed before you trust it.
3. Apply the fix.
4. Watch it pass.
5. Re-run the Phase 1 feedback loop against the original (un-minimised) scenario.

### What counts as the fix

The fix addresses the cause you confirmed. Name that cause in the commit message, and if it does not fit there, the work is not finished — because these all look like fixes and are not:

- **A guard on the symptom.** A confirmation dialog, a validation error, a coercion, a clamp. These change what happens *after* the wrong state exists. They are worth adding, but as a second layer, never as the answer to "what caused it". One confirmation dialog per attempt is the signature of a cause that was never found.
- **The same fix, one level up.** The bug was in a helper; you patched the caller. Ask why the helper's contract let this through, because the next caller will hit it.
- **A test that only covers the fixture you invented.** It passes forever and would have passed before the fix.

When you ship a guard without a confirmed cause, say that explicitly in the report and name what evidence would confirm it. That sentence is the difference between a mitigation the team understands and one they inherit as a mystery.

## Phase 6: Cleanup

Required before declaring done:

- [ ] Original repro no longer reproduces (re-run the Phase 1 loop)
- [ ] Regression test passes (or absence of seam is documented)
- [ ] All `[DEBUG-...]` instrumentation removed (`grep` the prefix)
- [ ] Throwaway prototypes deleted (or moved to a clearly-marked debug location)
- [ ] The hypothesis that turned out correct is stated in the commit / PR message, so the next debugger learns

And two that only apply if this bug had a life before today:

- [ ] Every earlier failed attempt is named in the report, with what it assumed and what the current fix assumes instead. A chain of silent attempts is the most expensive thing to inherit.
- [ ] If you shipped any guard without confirming a cause, it is listed as a mitigation with the evidence that would confirm the cause — not folded into "what was built".
