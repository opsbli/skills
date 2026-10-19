---
name: recall
description: Rebuild recent working context across sessions and hand back a current-state brief before you resume work.
disable-model-invocation: true
argument-hint: "The topic or area to catch up on"
---

# Recall

**Before you start or resume work, you rebuild the user's recent working context and hand back a tight capsule of where things stand now and what to do next.**

Keep it tight and on-topic. Read only what the in-scope threads need, then stop.

Your context lives in two records. The conversation history holds what you did and decided. The shared record holds everything that happened around the same code under other names: the symptoms users keep reporting, the fixes that shipped and got reverted, the errors still firing in production. A feature with a long bug tail keeps most of its story there, so don't reconstruct it from your own transcripts alone.

1. Classify, then route. Resuming one specific conversation is the host's own resume, not this skill. Turning habits into durable environment changes is `/retro`. A portable summary for the next agent is `/handoff`. Recall loads working context across recent conversations before you act. If the user already gave you a full state capsule (paths, branch, the change), use it and skip the mining.
2. Lock the scope before searching. Pin the window ("recent" is a real range, default the last 7 days), the topic if named, and the workspace (default the active one. Never read another project's history without being asked). State the scope back. Never quietly turn "all" into "recent N".
3. Fan out across the conversation history. Before fanning out, check for an existing handoff document: the temp directory is its default landing spot, and the user may have passed a path. When one exists, use it as the skeleton and spend the mining on what it leaves out, filling those gaps from the shared record (step 4) and live state (step 5). Re-deriving what a handoff document already compressed wastes the work that produced it. Reach the history through the host's own retrieval tool for past conversations. When the host also stores transcripts as files, they live under its project state directory, and each line is one message: find that directory by asking the host or reading its docs rather than hardcoding a path. Spawn parallel subagents, each taking a slice of the corpus. Tell every subagent to order candidates by real modification time and never by filename or id, search the topic first and then read only the matching conversations and only their relevant regions, and skip the current conversation plus obvious noise (subagent, eval, and test runs). Each returns the same schema, one block per conversation: topic, the user's goal, decisions, open threads, struggles and corrections, and artifacts (PRs, tickets, branches), each citing the conversation it came from. For one or two conversations, skip the fan-out and search directly. The raw material stays in the subagents. The main thread gets only their findings.
4. Sweep the shared record whenever the topic names a feature, file, subsystem, area, or bug. This is the default, not a judgment call, and "my work on X" does not exempt it. Run one investigator per source, in parallel with the conversation mining: source control (`git log`, `git blame`, reverted commits, PR descriptions), the issue tracker, long-form docs and ADRs, and any error tracker or log store the project has wired up. Aim each investigator at "what's the current state, what's been tried and didn't hold, and what are users still reporting" rather than "why was this built this way". Null results are findings. Skip an unavailable source and say so. Fold what comes back into the brief. Skip this step only for pure activity recall with no named target ("what did I do this week"), where your own history and live state are the entire answer.
5. Verify against live state. Take the PRs, branches, and tickets that the mining and the sweep surfaced and check them with `git` and `gh`. When the answer hinges on what an agent actually did (the tools it ran, files it read, errors it hit), read the full transcript, not just a trimmed summary.
6. Write the brief to the contract below. Group by thread. Stay on the named topic.

## Output contract

Lead with the capsule, then the thread status, then the problems, then the next move. Deeper detail goes below or gets cut.

- **Capsule.** At most 5 bullets. What this work is and where it stands overall.
- **Threads.** One line each, prefixed with exactly one status tag: `[merged #N]`, `[open PR #N]`, `[in flight <branch>]`, `[verified, uncommitted]`, `[reverted #N]`, or `[planned, not started]`. A thread with no tag is not done yet, so tag it.
- **Problems.** At most 5, the recurring ones. Include the symptoms users keep reporting and any fix that shipped and was reverted, so the next attempt starts where the last one failed.
- **Next move.** The single most useful next action, concrete.

An adjacent feature or ticket stays out unless it blocks this one. When the capsule and thread lines outgrow a screen, cut detail before you cut threads. Write the brief through the `unslop` rules, cite conversation findings by the id the host gives them and shared-record findings by their source (PR #, ticket ID, permalink, error-tracker issue), and sanitize private context before any public output.

**Reply:** the brief, to the contract above.
