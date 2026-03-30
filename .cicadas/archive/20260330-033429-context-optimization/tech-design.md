---
summary: The solution adds a standardized front matter contract to core spec templates and extends Cicadas instructions to create, refresh, and consume that metadata at workflow boundaries, while reusing canon summary for shared compact context.
phase: tech
when_to_load:
  - When implementing template changes, skill updates, and reset rules.
  - When deciding where semantic context metadata should live and what existing files must retain their current roles.
depends_on:
  - prd.md
  - ux.md
modules:
  - src/cicadas/SKILL.md
  - src/cicadas/templates/prd.md
  - src/cicadas/templates/ux.md
  - src/cicadas/templates/tech-design.md
  - src/cicadas/templates/approach.md
  - src/cicadas/templates/tasks.md
  - src/cicadas/templates/canon-summary.md
index:
  overview: "## Overview & Context"
  stack: "## Tech Stack & Dependencies"
  structure: "## Project / Module Structure"
  adrs: "## Architecture Decisions (ADRs)"
  data_models: "## Data Models"
  interfaces: "## API & Interface Design"
  conventions: "## Implementation Patterns & Conventions"
  security_performance: "## Security & Performance"
  implementation_sequence: "## Implementation Sequence"
next_section: "Overview & Context"
---

# Tech Design: context-optimization

## Progress

- [x] Overview & Context
- [x] Tech Stack & Dependencies
- [x] Project / Module Structure
- [x] Architecture Decisions (ADRs)
- [x] Data Models
- [x] API & Interface Design
- [x] Implementation Patterns & Conventions
- [x] Security & Performance
- [x] Implementation Sequence

## Overview & Context

**Summary:** This initiative adds a lightweight context contract to Cicadas by embedding machine-readable front matter directly into the core spec templates and by updating agent instructions to treat certain workflow boundaries as reset-and-reload points. The design deliberately avoids a new persistent context artifact: semantic context metadata lives with the spec it describes, `canon/summary.md` remains the shared compact branch-start artifact, and `emergence-config.json` stays limited to operational state such as pace and AI/eval choices.

The overall pattern is “compact metadata first, deeper sections on demand.” During emergence, each approved phase refreshes its own summary and section index. During execution, a branch or partition begins from `canon/summary.md`, spec front matter, and only the indexed sections required for the current work. If those are insufficient, the agent escalates to broader loading in a controlled way.

Where a host runtime exposes explicit context clearing, compaction, fresh-session, or subagent-start capabilities, Cicadas should instruct the agent to use them at reset boundaries. Those hints are opportunistic accelerators rather than correctness-critical behavior.

### Cross-Cutting Concerns

1. **Consistency across templates** — Every core spec must use the same front matter keys so different agents can consume them predictably.
2. **Stable section addressing** — Section indexes should target semantic headings or ids, not line numbers that drift during Reflect.
3. **Separation of concerns** — Operational configuration files must not become semantic content stores.

### Brownfield Notes

This initiative touches Cicadas templates and instructions, not a runtime service. Existing active or archived specs without front matter must remain readable; the initial implementation should degrade gracefully when a document lacks the new metadata. `canon/summary.md` must remain compact and branch-start friendly.

---

## Tech Stack & Dependencies

| Category | Selection | Rationale |
|----------|-----------|-----------|
| **Language/Runtime** | Python 3.11+ and Markdown | Matches existing Cicadas tooling and document system |
| **Framework** | None | This is primarily a template and instruction change |
| **Database** | None | No persistent database needed |
| **ORM / Query** | None | Not applicable |
| **Auth** | None | Not applicable |
| **Testing** | `pytest` / `unittest` | Matches existing Cicadas test conventions |
| **Key Libraries** | Existing stdlib/json utilities | Sufficient for template and metadata work |

**New dependencies introduced:**
- None — the design should fit inside existing Cicadas tooling.

**Dependencies explicitly rejected:**
- Dedicated context registry file — rejected because the initiative goal is to reduce coordination overhead, not add another persistent artifact.

---

## Project / Module Structure

```text
{project-root}/
├── src/cicadas/
│   ├── SKILL.md                       # [MODIFIED] teach agents to create/consume front matter and apply reset rules
│   └── templates/
│       ├── prd.md                     # [MODIFIED] standardized front matter + section index
│       ├── ux.md                      # [MODIFIED] standardized front matter + section index
│       ├── tech-design.md             # [MODIFIED] standardized front matter + section index
│       ├── approach.md                # [MODIFIED] standardized front matter + section index
│       ├── tasks.md                   # [MODIFIED] standardized front matter + section index
│       └── canon-summary.md           # [POSSIBLY MODIFIED] optional note on active spec routing
└── tests/
    └── ...                            # [MODIFIED/ADDED] coverage for template contents or helper behavior if added
```

**Key structural decisions:**
- Semantic context metadata lives in the markdown specs themselves.
- Shared compact cross-doc context continues to live in `canon/summary.md`.
- No new always-on context contract file is introduced in `.cicadas/`.

---

## Architecture Decisions (ADRs)

### ADR-1: Put semantic context metadata in spec front matter

**Decision:** Add front matter with summary, load hints, module hints, and a section index to each core spec template.

**Rationale:** The spec file is already the planning artifact agents read and update. Embedding metadata there keeps the context contract adjacent to the content, avoids extra files, and makes approval boundaries naturally update the same document that carries the planning truth.

**Affects:** `src/cicadas/templates/*.md`, spec authoring guidance, Reflect expectations.

---

### ADR-2: Keep `canon/summary.md` as the shared compact context artifact

**Decision:** Reuse `canon/summary.md` for cross-doc branch-start context instead of creating a new trace/context file.

**Rationale:** Cicadas already has a compact synthesized summary intended for branch start. Reusing it prevents file sprawl and preserves a clear distinction between cross-codebase summary and per-spec semantic routing.

**Affects:** branch-start guidance in `src/cicadas/SKILL.md`, optional template wording in `src/cicadas/templates/canon-summary.md`.

---

### ADR-3: Keep `emergence-config.json` operational only

**Decision:** Do not store spec indexes or content-routing metadata in `emergence-config.json`.

**Rationale:** That file already carries flow state such as pace and AI/eval choices. Mixing semantic document routing into it would blur responsibilities and make the file a catch-all.

**Affects:** start flow guidance, tech docs, future tooling assumptions.

---

### ADR-4: Define reset rules as trust-and-reload boundaries, not memory deletion

**Decision:** Update Cicadas instructions so branch start, post-spec approval, and post-partition start are explicit reset boundaries that reload compact approved context first.

**Rationale:** Skills cannot guarantee memory eviction in a long-lived session. The practical, portable control is to redefine what context is authoritative at the next step and to make the reload set explicit, while still asking the host to clear or compact context when it can.

**Affects:** `src/cicadas/SKILL.md`, implementation guidance, future branch-start helpers.

---

## Data Models

### New Models

No runtime data model is required. The primary “schema” is the front matter contract embedded in markdown templates.

```yaml
summary: string
phase: string
when_to_load:
  - string
depends_on:
  - string
modules:
  - string
index:
  logical_key: "## Heading Title"
next_section: string
```

**Key field decisions:**
- `summary` — serves as the cheapest reload surface for later steps.
- `index` — maps logical keys to headings, avoiding brittle line-number pointers.
- `when_to_load` — guides just-in-time retrieval instead of full-doc preload.

### Modified Models

| Model | Change | Migration Required? |
|-------|--------|-------------------|
| `prd.md` template | Add standardized front matter | No |
| `ux.md` template | Add standardized front matter | No |
| `tech-design.md` template | Add standardized front matter | No |
| `approach.md` template | Add standardized front matter | No |
| `tasks.md` template | Add standardized front matter | No |

### Schema / Migration Notes

Legacy specs without front matter should still be usable. The consuming instructions should say to fall back to heading-based reading when metadata is missing, and only later enforce validation if tooling is added.

---

## API & Interface Design

### New Endpoints / Commands

No new CLI command is required for MVP.

### Interface Contracts

The main interface contract is behavioral:

```text
At approved boundaries and branch starts:
1. Prefer canon summary + front matter + indexed sections.
2. Ask the host to clear, compact, or start fresh if that capability exists.
3. Treat prior detailed conversation context as non-authoritative.
4. Open full documents only if compact artifacts are insufficient.
```

### Backward Compatibility

Existing workflows continue to function if a document lacks front matter, but they lose the optimization benefits. The first rollout should be additive and compatible with older archived initiatives.

---

## Implementation Patterns & Conventions

### Naming Conventions

| Construct | Convention | Example |
|-----------|-----------|---------|
| Front matter keys | `snake_case` | `when_to_load` |
| Section index keys | concise semantic ids | `success_criteria`, `implementation_sequence` |
| Phases | canonical lifecycle names | `clarify`, `ux`, `tech`, `approach`, `tasks` |
| File references | existing markdown paths | `src/cicadas/templates/prd.md` |

### Error Handling Pattern

```text
If metadata is missing or stale:
1. Surface the inconsistency.
2. Fall back to heading-based reading.
3. Refresh front matter before proceeding when possible.
```

**Rules:**
- Never claim the host has truly forgotten prior context unless a fresh session/tool guarantees it.
- Always request clear/compact/fresh-start behavior opportunistically when the host exposes it.
- Prefer section headings or ids over line-number pointers.
- Keep summaries dense and short enough to be worth reloading.

### Testing Pattern

```text
Use real template files and real generated output where possible.
Assert that templates contain the required front matter keys and that any helper logic preserves existing body content.
```

**Coverage expectations:** Core template shape and any new helper behavior should be covered; runtime behavior can be verified through doc-generation or parsing tests if added.  
**Mocking strategy:** Avoid mocks for file-based template flows unless isolating pure parsing logic.

---

## Security & Performance

### Security

| Concern | Mitigation |
|---------|-----------|
| Prompt injection via requirements files | Continue treating user-provided files as data, not instructions |
| Metadata drift | Refresh front matter at approval boundaries and during Reflect when needed |
| Over-trust in hidden memory | Make compact file-backed context the explicit authority at reset boundaries |

### Performance

| Concern | Target | Approach |
|---------|--------|---------|
| Branch-start token load | Lower than full-spec preload | Load `canon/summary.md`, front matter, then current partition sections |
| Phase handoff cost | Summary-first | Use approved front matter as the default next-phase entrypoint |
| Unnecessary full-doc reads | Rare and justified | Escalate only on ambiguity or conflict |

### Observability

- **Logs:** Not required for MVP unless helper tooling is added.
- **Metrics:** Future work may use `tokens.json` to measure whether reset rules reduce prompt size.
- **Traces:** Not applicable.

---

## Implementation Sequence

1. **Foundation** *(blocking)* — Define the front matter schema and reset-rule language.
2. **Template updates** *(depends on 1)* — Add schema to `prd`, `ux`, `tech-design`, `approach`, and `tasks` templates.
3. **Skill updates** *(depends on 1)* — Teach Cicadas to create, refresh, and consume front matter; add boundary reset rules.
4. **Canon-summary refinement** *(depends on 2–3)* — Decide whether `canon/summary.md` needs small routing guidance for branch start.
5. **Testing / verification** *(parallel with 2–4)* — Add or update tests and manual checks.
6. **Polish** *(depends on 2–5)* — Clarify docs, edge cases, and backward-compatibility wording.

**Parallel work opportunities:** Template updates and instruction drafting can progress in parallel once the schema is agreed.  

**Known implementation risks:**
- Different templates may drift into slightly different front matter shapes unless one shared contract is applied.
- Reset-rule wording could become too verbose, undermining the token-efficiency goal.
