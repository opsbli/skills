---
name: project-standards
description: Write, update, or audit a repo's enforceable engineering standards document (docs/agents/project-standards.md), sourced from its code generator when one exists and from code regularities when one does not.
disable-model-invocation: true
---

# Project Standards

One repo, one enforceable standards document: `docs/agents/project-standards.md`. This skill generates it, updates it, and audits code against it. Execution skills (`/code-review`, `/implement`, `/implement-spec`, `/tdd`) read the document, never this skill.

## The rule that outranks everything

**Facts are found by exploration; standards are confirmed by humans.** Exploration reports what the code *does*; only the human decides what it *must* do. Never promote an inferred convention into an enforced rule without explicit confirmation. Items awaiting a decision carry a ⚠️ marker and are not enforced.

## Generator first

A repo with a code generator has already answered most "what should code look like" questions in executable form. Treat that answer as the primary source instead of averaging over whatever the codebase currently contains.

Decide per **concern**, not per repo: a monorepo can have a generator for the backend and none for the frontend.

1. **Generator for this concern exists** → its templates define the skeleton, naming, annotations, and data conventions. Existing code that disagrees is an **outlier**, not a competing convention: it gets counted, named, and marked touch-and-fix.
2. **No generator for this concern** → infer from code by three signals, in this order: **majority** (how many instances), **recency** (which variant the newest code uses), **stability** (which one the last few commits stopped changing). Majority alone is not enough — a deprecated pattern can hold the count. Two of three agreeing is the bar for "high confidence"; anything less is a ⚠️ item with both variants named and counted.

### Generator present — the test

Require **two of three** signals, otherwise it is a leftover artifact rather than a living generator:

- a template directory (`vm/`, `templates/`, `generators/`, `*.vm`, `*.hbs`, `*.mustache`, `*.ejs`, `*.jinja`)
- a generator config file or module (`generator.yml`, `jhipster`, `.yo-rc.json`, `prisma/schema.prisma`, generator CLI in the build)
- a generated-output marker (files whose headers say "generated", a `.gitattributes` marked `linguist-generated`)

See [`GENERATORS.md`](GENERATORS.md) for per-stack markers.

### Generator config is a defect surface, not a standard

The templates define the standard. The **configuration** decides whether the generator agrees with *this* repo, and it is frequently wrong. Audit it before writing any rule:

- **Defaults vs reality**: does the configured package/base path/table prefix/author match what this repo actually uses? A generator shipped with upstream defaults (another company's package name, another project's prefix, another person's author) produces code that compiles and is architecturally wrong — a silent failure and always a P0 finding.
- **Single config, multiple modules**: when one global config cannot express several modules (a multi-module repo with one `packageName`), the standard must state the **per-generation override** procedure instead of pretending a default applies.
- **Input contract**: list the generator's input fields and which ones are *mandatory to set on every generation* (package, module, business name, permission prefix, template category, author). Anything left at its default inherits the defect above.
- **Capability boundary**: which template categories exist (CRUD vs tree, single vs master-detail), and what the generator deliberately does **not** produce. Business actions outside that boundary get extended on the generated skeleton, never hand-built from scratch.

Report config defects as findings with file and line. The fix is either to correct the config or to write the override procedure into the standard — never to encode a wrong default as a rule.

### Template and existing standard disagree

When a repo already has a standards document whose rule contradicts what the template emits, **the template wins** and the rule gets rewritten as "template baseline + direction of travel":

- The template's output is compliant as generated. Never fail a diff for following the generator.
- The divergence is recorded with the human's ruling and date, because the human is the only one allowed to move a rule.
- The forward direction stays stated (e.g. "generated pages migrate to `<search-form>` when next touched"), so the baseline does not freeze forever.

## Pick a mode

- **`generate`** — no `docs/agents/project-standards.md` yet. Full pass: detect → explore → draft → confirm → write.
- **`update`** — the doc exists and something changed (new framework, new generator, a rule needing tightening). Targeted delta pass.
- **`audit`** — the doc exists; check code against it, read-only. Also re-checks generator config and template drift.

No mode named: `generate` when the file is missing, `audit` when the doc exists and the question is "are we following it", `update` otherwise.

## generate

1. **Detect the stack and the generator.** Read the manifests (`pom.xml`, `build.gradle`, `package.json`, `go.mod`, `requirements.txt`, `Cargo.toml`) and run the generator test above, per concern. State the detection result in one line before exploring, including the case "no generator, inferring from code".
2. **Explore for facts.** Dispatch read-only sub-agents with the concern checklist below. Every claim needs file path plus a short excerpt, and frequency counts where a convention is claimed ("142 of 153 controllers extend `BaseController`"). Demand a closing section of **candidate standards**, each tagged high or low confidence, each naming its source: `template` (generator), `majority`, `recency`, `stability`, or `absent`.
3. **Draft.** One section per concern: skeleton and layering, data and DDL, migrations, testing and verification, config and secrets, docs and decisions. High-confidence items become proposed rules. Low-confidence items become proposed rules **with both variants named and counted**. Gaps become ⚠️ items.
4. **Confirm with the human, section by section.** Give a recommendation per item. For low-confidence items recommend the variant that matches the newest code, and say why. For a template-vs-standard conflict, present the ruling as a decision the human makes, with the template's behaviour as the default. Only confirmed text enters the document.
5. **Write** `docs/agents/project-standards.md`, then add one pointer block to `AGENTS.md` (create the file if absent; never overwrite its existing sections):

```markdown
### Project standards
本仓库的强制工程规范见 `docs/agents/project-standards.md`。实现、测试与评审必须逐条对照;`/code-review` 的 Standards 轴与 `/implement` 的收口验收以该文件为准。
```

### What to explore

- **Skeleton**: package layout, base classes, return types, DI style, exception handling, permission annotation pattern. With a generator: read the templates first, then count how many existing classes match and list the outliers by name.
- **Data and DDL**: every `.sql` file and its directory. Audit columns and their frequency, primary-key strategy, logical-delete semantics as written in comments, physical foreign keys, index habits. With a generator: what the data template emits versus what the DDL files contain.
- **Migrations**: baseline versus incremental script directories, naming, idempotency guards, how fresh-environment and existing-environment installs differ.
- **Testing and verification**: frameworks, counts, tags, whether the default build runs them, what "done" verifiably means today.
- **Config and secrets**: profile files and their split, `${ENV:default}` usage versus hardcoded values, plaintext secrets (report location only, never the value).
- **Docs**: existing `AGENTS.md` rules, `docs/adr`, contract docs referenced from code comments.

## Document structure

- **Header**: what enforces the file, how it was generated, that ⚠️ items are not enforced, and that **only humans may loosen a rule** — agents never edit this file on their own.
- **One section per concern.** Each rule states the rule, its source (template file, directory, or count evidence), and the correction principle for disagreeing old code: **touch-and-fix** unless the human chose full migration.
- **Generator contract section, mandatory when a generator exists.** The per-generation override procedure, the input fields that must be set explicitly, the template categories and their boundary, the artifact self-check list, and the rule that changing a template requires a re-scan of existing output plus an update to this section.
- **Verification floor**: the exact commands that must pass before delivery, named per repo.
- **Upkeep**: periodic audit, and "either fix the code or have a human amend this file — silent drift is not allowed".

## update

1. Read the current doc; diff the request against it.
2. Explore only the affected concern to refresh facts — including re-running the generator config audit when the change touches generation.
3. Propose the delta as an edit list: rule added / amended / moved to ⚠️ / removed. Agents may propose **tightening** from evidence; **loosening requires the human to state it**, and the reason gets recorded in one line under the affected section.
4. Confirm, then edit in place.

## audit

1. Read the doc; skip ⚠️ items — they are not enforceable.
2. Check each rule against code: sample broadly, deep-dive where the first violations appear. Every finding needs file and line. Sub-agents are fine.
3. Re-run the **generator config audit** and the **template drift check**: does generated output still match the templates, and is the config still aligned with the repo?
4. Report per rule: **compliant / non-compliant (with evidence) / not machine-decidable (needs human sampling)**. Quantify. Fix nothing.
5. Route: systemic violations (a rule dead in practice) → open a ticket and flag the rule for human review, fix code or amend rule. Scattered violations → fix candidates for `/to-tickets` or `/implement`.
6. Read `docs/skill-friction-log.md` when the repo keeps one. Friction repeating across receipts is a defect in a skill or in this standards document, not user error — turn each high-frequency point into a revision issue against the named file rather than silently rewriting either.

## Boundaries

- Never implements features, never reformats a repo wholesale, never edits the standards document without a confirmed item behind the edit.
- Exploration sub-agents are read-only. If a probe would write — e.g. run the generator to inspect output — ask first, and prefer reading the templates.
- Secrets found during exploration are reported as location plus line, never value, and routed to a security ticket rather than copied into the standards doc.
