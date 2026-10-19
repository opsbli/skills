# Generators

Per-stack markers for the **generator test** in `SKILL.md`, and the config defects worth probing once one is found. A generator is evidence about what code *should* look like; its configuration is evidence about whether it currently agrees with this repo.

Two of the three signals (template directory, config, generated-output marker) make a generator real. One signal alone is usually a leftover.

## RuoYi-Vue-Plus / ruoyi-generator (Velocity)

**Signals**

- Templates: `<module>/src/main/resources/vm/` with `java/`, `vue/`, `ts/`, `xml/`, `sql/<dialect>/` subdirectories, all `*.vm`.
- Config: `src/main/resources/generator.yml` read by a `GenConfig` class through `@PropertySource`.
- Runtime model: a `GenTable` / `GenTableColumn` pair persisted in `gen_table` / `gen_table_column`, so the generator's real input is **database rows**, not a file.

**What the templates decide** — read them before writing any skeleton rule:

- Layering: `controller / service / service.impl / mapper / domain{/bo,/vo}`.
- Base classes and return types: `BaseController`, `BaseMapperPlus`, `R<T>`, `TableDataInfo<T>`, `PageQuery`.
- Annotations: `@SaCheckPermission("module:business:action")`, `@Validated(AddGroup/EditGroup.class)`, `@Log(BusinessType.×)`, `@RepeatSubmit`.
- Entity base: `TenantEntity` when a `tenant_id` column exists, otherwise `BaseEntity`; audit fields excluded from BO/VO by fixed name lists in the generator's constants.
- Template categories: a CRUD variant and a tree variant, selected by a category field; the tree variant consumes tree-code / tree-parent-code / tree-name fields.

**Config defects to probe**

- `packageName` and `tablePrefix` shipped with upstream defaults (a different company's package, a prefix like `sys_`). In a multi-module repo one global `packageName` cannot be right for every module, so the standard must state the **per-generation override** and which `GenTable` fields are mandatory every time.
- `author` still set to the upstream maintainer, which stamps a foreign name into every generated header.
- No `generator.yml` per module: confirm whether overrides live in the generation UI only, because that means the procedure is undocumented and lives in one person's head.
- Generated output landing in a **separate frontend repository**. The ts/vue templates write API paths and types assuming a directory layout the other repo may not use; check the real `src/api` depth against what the template emits, and state the relocation step if they differ.

**Cross-cutting check**: the permission prefix is usually composed as `module:business`, used by the controller template, the frontend permission directive, and the menu SQL alike. Verify all three are generated from the same value, and check the SQL template's menu rows against the permission strings in the code.

## MyBatis-Plus generator

**Signals**: `mybatis-plus-generator` in the build, an `AutoGenerator` / `FastAutoGenerator` class, `templates/` under test resources. **Probe**: output package, entity base class, whether Lombok is enabled, `@TableId` strategy, controller template presence (this generator often stops at the data layer, which makes the web layer a "no generator, infer from code" concern).

## JHipster

**Signals**: `.yo-rc.json`, `.jhipster/` entity JSON files. **Probe**: entity JSON is the executable source for fields, relationships, and validation; the generated layout (`web/rest`, `service`, `repository`) is authoritative over handwritten deviations. Config defect: entity JSON missing fields that the database already has, so regeneration would erase them.

## NestJS CLI / Angular CLI

**Signals**: `nest-cli.json` with a `schematics` section, `@nestjs/schematics`, `.angular.json` schematics. **Probe**: naming convention for files and classes, module wiring style. These scaffolds are thin — they decide file shape, not architecture, so treat the skeleton concern as generator-sourced and the rest as inference.

## Prisma / Drizzle

**Signals**: `prisma/schema.prisma`, `drizzle.config.ts`. **Probe**: the schema is the single source for types and migrations; hand-written SQL that bypasses `prisma migrate` is an outlier. Config defect: schema drift from the actual database (check whether a migration directory backs every model change).

## Django / Rails

**Signals**: Django app `apps.py` + `templates/`, custom `startapp`/`startproject` templates, `manage.py` custom commands; Rails `lib/templates/`, generator overrides under `lib/generators/`. **Probe**: app layout, model conventions, whether view/template generation is in use or hand-written. Rails' `scaffold` is a generator only if the team still runs it — check the git history for scaffold-shaped commits.

## OpenAPI / contract generators

**Signals**: `openapi-generator` config, `swagger-codegen`, generated client directories with "do not edit" headers. **Probe**: the spec file is the standard for the API surface; hand-edited generated clients are an outlier and are usually erased on the next run. Config defect: spec and running server disagree.

## No generator found

Fall back to the inference rule in `SKILL.md`: majority, recency, stability, two of three for high confidence. Two extra probes matter here:

- **Two-generation coexistence** is the normal state. Count both variants and name them ("44 pages use `SearchForm`, 56 hand-write `el-form`") rather than reporting only the winner.
- **The newest directory is the tell.** When the last few features all took one shape, that shape is the emerging standard even if the count still favors the old one — recommend it, and say the count is lagging.

## When the stack is unfamiliar

Probe for the four invariants before anything else: where the build is defined, where a new module is added, where tests live, and how a new endpoint or page gets created. The last one is the generator question in disguise — if the team has an answer that is a command, that command is the generator.
