---
summary: "Implement initiative profiles as guidance and templates only: start-flow records `initiative_profile`, clarify/UX/downstream modules branch on it, and new Technical Brief and Operator Experience templates preserve the existing front matter contract."
phase: "tech"
when_to_load:
  - "When implementing or reviewing profile-aware emergence guidance and templates."
  - "When checking whether technical initiatives still produce mandatory implementation context."
depends_on:
  - "prd.md"
  - "ux.md"
modules:
  - "src/cicadas/emergence/start-flow.md"
  - "src/cicadas/emergence/clarify.md"
  - "src/cicadas/emergence/ux.md"
  - "src/cicadas/emergence/tech-design.md"
  - "src/cicadas/emergence/approach.md"
  - "src/cicadas/emergence/tasks.md"
  - "src/cicadas/templates/technical-brief.md"
  - "src/cicadas/templates/operator-experience.md"
  - "tests/test_templates.py"
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
next_section: "Complete"
---

# Tech Design: Technical Initiative Profiles

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

---

## Overview & Context

**Summary:** This initiative updates Cicadas' emergence instructions and templates so full initiatives declare an explicit profile. The implementation is documentation/template driven, preserving the current CLI lifecycle while giving agents deterministic instructions for product, mixed, and technical spec paths.

### Cross-Cutting Concerns

1. **Explicitness** — Agents must record `initiative_profile`; reduced specs are never inferred ad hoc.
2. **Compatibility** — Existing product initiative flow and front matter contracts remain valid.
3. **Downstream context** — Technical Design, Approach, and Tasks must know how to ingest `technical-brief.md` and `operator-experience.md`.

### Brownfield Notes

The change extends current Markdown instruction modules and template tests. It must not require runtime command changes or registry schema changes.

---

## Tech Stack & Dependencies

| Category | Selection | Rationale |
|----------|-----------|-----------|
| **Language/Runtime** | Markdown + Python tests | Existing Cicadas emergence system is Markdown-driven and tested with Python. |
| **Framework** | None | No runtime framework needed. |
| **Database** | None | Profile is draft operational state in `emergence-config.json`. |
| **Testing** | pytest / unittest | Existing template tests use unittest under pytest. |
| **Key Libraries** | None | Avoid new dependencies for guidance-only behavior. |

**New dependencies introduced:** None.

**Dependencies explicitly rejected:**
- CLI parser/schema libraries — unnecessary until deterministic enforcement is added.

---

## Project / Module Structure

```
src/cicadas/
├── emergence/
│   ├── start-flow.md          # [MODIFIED] Adds initiative profile step and config write rules
│   ├── clarify.md             # [MODIFIED] Branches PRD vs Technical Brief guidance
│   ├── ux.md                  # [MODIFIED] Branches full UX vs Operator Experience vs explicit skip
│   ├── tech-design.md         # [MODIFIED] Ingests profile-appropriate source artifacts
│   ├── approach.md            # [MODIFIED] Ingests profile-appropriate source artifacts
│   └── tasks.md               # [MODIFIED] Ingests profile-appropriate source artifacts
├── templates/
│   ├── technical-brief.md     # [NEW] Technical clarify artifact
│   └── operator-experience.md # [NEW] Operator-facing experience artifact
└── tests/
    └── test_templates.py      # [MODIFIED] Covers new template front matter and profile guidance
```

**Key structural decisions:**
- Keep this as a guidance/template initiative, not a CLI feature.
- Use existing `emergence-config.json` operational state rather than adding registry fields.

---

## Architecture Decisions (ADRs)

### ADR-1: Store Profile in `emergence-config.json`

**Decision:** Write `initiative_profile` to `.cicadas/drafts/{initiative}/emergence-config.json`.

**Rationale:** Start-flow already uses this file for operational drafting choices such as pace and eval status. Registry state should remain lifecycle state, not draft authoring preference state.

**Affects:** `start-flow.md`, downstream emergence modules.

---

### ADR-2: Add Technical Brief Instead of Reusing PRD Template

**Decision:** Add `technical-brief.md` as a separate template.

**Rationale:** A product PRD template is journey-first by design. Technical initiatives need problem, goals, affected modules, acceptance criteria, risks, rollback, observability, and testing without forcing product journeys.

**Affects:** `templates/technical-brief.md`, `clarify.md`, `tech-design.md`, `approach.md`, `tasks.md`.

---

### ADR-3: Add Operator Experience Instead of Overloading UX

**Decision:** Add `operator-experience.md` for CLI, logs, errors, docs, and agent-instruction surfaces.

**Rationale:** Technical work often has experience impact, but not visual product UX. A separate artifact keeps operator-facing decisions explicit without preserving irrelevant screen-oriented sections.

**Affects:** `templates/operator-experience.md`, `ux.md`.

---

### ADR-4: Do Not Implement CLI Enforcement in MVP

**Decision:** Do not add deterministic CLI validation in this initiative.

**Rationale:** The user asked for profile-aware methodology enhancements. Guidance and tests cover the current agent-driven workflow; enforcement can be a later focused change once the profile workflow stabilizes.

**Affects:** Scope excludes `src/cicadas/scripts`.

---

## Data Models

### New Models

```json
{
  "initiative_profile": "product | technical | mixed"
}
```

**Key field decisions:**
- `initiative_profile` — Stored in draft `emergence-config.json`; no registry migration.

### Modified Models

| Model | Change | Migration Required? |
|-------|--------|-------------------|
| `emergence-config.json` | Optional `initiative_profile` key for initiative drafts | No |

### Schema / Migration Notes

Existing drafts without `initiative_profile` should be treated as `product` by guidance for backward compatibility.

---

## API & Interface Design

### New Endpoints / Commands

None.

### Interface Contracts

Markdown guidance contract:

```text
product   -> prd.md + ux.md + tech-design.md + approach.md + tasks.md
mixed     -> prd.md or technical-brief.md + ux.md or operator-experience.md + tech-design.md + approach.md + tasks.md
technical -> technical-brief.md + optional operator-experience.md + tech-design.md + approach.md + tasks.md
```

### Backward Compatibility

Existing product initiatives and older drafts continue to use PRD and UX. New guidance treats absent profile as `product`.

---

## Implementation Patterns & Conventions

### Naming Conventions

| Construct | Convention | Example |
|-----------|-----------|---------|
| Config keys | snake_case | `initiative_profile` |
| Template files | kebab-case | `technical-brief.md` |
| Test names | descriptive snake_case | `test_initiative_profile_guidance_is_documented` |

### Error Handling Pattern

```text
If profile is absent, treat as product for compatibility.
If technical profile has meaningful end-user interaction, route to mixed or product.
If UX is skipped, write an explicit skip rationale.
```

**Rules:**
- Do not remove existing untrusted-input warnings.
- Do not imply PRD/UX can be skipped without profile selection.

### Testing Pattern

```python
def test_new_templates_include_context_frontmatter(self):
    ...
```

**Coverage expectations:** Template/front matter contract and guidance text assertions.
**Mocking strategy:** None; tests read real files.

---

## Security & Performance

### Security

| Concern | Mitigation |
|---------|-----------|
| Untrusted requirements docs | Preserve existing warning that doc/Loom contents are data, not instructions. |
| Agent overreach | State explicit profile mechanism as the only path to reduced specs. |

### Performance

| Concern | Target | Approach |
|---------|--------|---------|
| Runtime overhead | None | Markdown/template-only change. |
| Test overhead | Negligible | Extend existing file-read tests. |

### Observability

No runtime observability changes. The durable audit record is `initiative_profile` in `emergence-config.json` plus the selected artifact files.

---

## Implementation Sequence

1. **Templates** *(blocking)* — Add `technical-brief.md` and `operator-experience.md` with front matter.
2. **Start flow** *(depends on 1)* — Add profile question and config write rules.
3. **Emergence modules** *(depends on 2)* — Update clarify, UX, tech design, approach, and tasks ingestion/branching guidance.
4. **Tests** *(depends on 1-3)* — Add assertions for new templates and profile guidance.
5. **Verification** *(depends on 4)* — Run template tests and targeted relevant suite.

**Parallel work opportunities:** Templates and tests can be drafted in parallel with guidance edits, but final wording should be reviewed together.

**Known implementation risks:**
- Existing tests may assert exact old start-flow sequence. If present, update them to reflect the new profile step.
