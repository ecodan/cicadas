
---
summary: "{One tight paragraph summarizing the technical approach, core architectural decisions, and the most important constraints. Keep it compact enough to serve as a low-cost reload artifact.}"
phase: "tech"
when_to_load:
  - "When implementing or reviewing architecture, interfaces, data models, conventions, and sequencing."
  - "When checking whether changes still conform to the agreed technical approach."
depends_on:
  - "prd.md"
  - "ux.md"
modules:
  - "{Primary module, package, or code path shaped by this design}"
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

# Tech Design: {Initiative Name}

## Progress

- [ ] Overview & Context
- [ ] Tech Stack & Dependencies
- [ ] Project / Module Structure
- [ ] Architecture Decisions (ADRs)
- [ ] Data Models
- [ ] API & Interface Design
- [ ] Implementation Patterns & Conventions
- [ ] Security & Performance
- [ ] Implementation Sequence

---

## Overview & Context

**Summary:** {1–2 paragraph description of the technical solution — what architectural pattern is used and why it's the right choice for this problem.}

### Cross-Cutting Concerns

{Concerns that affect every component — identify them here so they aren't rediscovered during implementation.}

1. **{Concern 1}** — {e.g., Auth must be enforced at every API boundary}
2. **{Concern 2}** — {e.g., All state mutations must be logged}
3. **{Concern 3}** — {e.g., Provider abstraction layer must be transparent to business logic}

### Brownfield Notes

{On brownfield projects: what parts of the existing system does this initiative touch? What must NOT change? What existing patterns must this design follow?}

---

## Tech Stack & Dependencies

| Category | Selection | Rationale |
|----------|-----------|-----------|
| **Language/Runtime** | {e.g., Python 3.10+} | {Why} |
| **Framework** | {e.g., FastAPI / Django / None} | {Why} |
| **Database** | {e.g., PostgreSQL / SQLite / None} | {Why} |
| **ORM / Query** | {e.g., SQLAlchemy / Prisma} | {Why} |
| **Auth** | {e.g., JWT / OAuth2 / Session} | {Why} |
| **Testing** | {e.g., pytest / Jest} | {Why} |
| **Key Libraries** | {List significant ones} | {Why} |

**New dependencies introduced:**
- `{package}=={version}` — {what it does, why chosen over alternatives}

**Dependencies explicitly rejected:**
- `{package}` — {why not used}

---

## Project / Module Structure

{Show the directory tree for new or changed areas. Only show what this initiative adds or modifies — don't reproduce the entire repo unless it's greenfield.}

```
{project-root}/
├── {new-module}/
│   ├── {file}.{ext}          # {one-line purpose}
│   ├── {file}.{ext}          # {one-line purpose}
│   └── {subdir}/
│       └── {file}.{ext}      # {one-line purpose}
└── {modified-file}.{ext}     # [MODIFIED] {what changes}
```

**Key structural decisions:**
- {e.g., "Business logic separated from API layer — handlers only call service functions"}
- {e.g., "All new code lives in `src/features/{name}` following existing module pattern"}

---

## Architecture Decisions (ADRs)

{For each significant decision where two reasonable implementors might choose differently, write an ADR. Aim for 3–7. Trivial choices don't need one.}

### ADR-1: {Decision Title}

**Decision:** {The specific choice made — be concrete, not vague}

**Rationale:** {Why this is right for this context — 1–3 sentences. What constraint or trade-off made alternatives worse?}

**Affects:** {Which components or files are shaped by this decision}

---

### ADR-2: {Decision Title}

**Decision:** {The specific choice}

**Rationale:** {Why}

**Affects:** {Components affected}

---

## Data Models

### New Models

{Define schemas for new entities. Use the language-appropriate format (Pydantic, TypeScript interface, JSON schema, SQL DDL, etc.)}

```{language}
{Schema definition}
```

**Key field decisions:**
- `{field}` — {Why this type/constraint, alternatives considered}

### Modified Models

{For brownfield: what existing models change? Be explicit about additive vs. breaking changes.}

| Model | Change | Migration Required? |
|-------|--------|-------------------|
| `{ModelName}` | {Add field `foo`} | Yes — default `null` |
| `{ModelName}` | {Rename field `bar` → `baz`} | Yes — data migration |

### Schema / Migration Notes

{Any migration strategy, rollback plan, or ordering constraints.}

---

## API & Interface Design

### New Endpoints / Commands

{REST, CLI commands, RPC methods, event contracts — whatever is relevant to this initiative.}

```
{METHOD} {path}
Request:  {schema or example}
Response: {schema or example}
Errors:   {error codes and meanings}
```

### Interface Contracts

{Shared interfaces, abstract base classes, or event schemas that define the boundaries between components.}

```{language}
{Interface definition}
```

### Backward Compatibility

{For brownfield: are any existing API consumers affected? What's the migration path?}

---

## Implementation Patterns & Conventions

{Coding standards and patterns that ALL contributors to this initiative must follow for consistency. These prevent divergence across parallel implementation work.}

### Naming Conventions

| Construct | Convention | Example |
|-----------|-----------|---------|
| {Functions} | {snake_case} | `get_user_by_id()` |
| {Classes} | {PascalCase} | `UserRepository` |
| {Constants} | {UPPER_SNAKE} | `MAX_RETRIES` |
| {Files} | {kebab-case} | `user-service.ts` |

### Error Handling Pattern

```{language}
{Standard error handling pattern for this codebase}
```

**Rules:**
- {e.g., "Never swallow exceptions silently — log + rethrow or convert to domain error"}
- {e.g., "All user-facing errors must include an actionable message"}

### Testing Pattern

```{language}
{Minimal test structure example}
```

**Coverage expectations:** {e.g., "70%+ on non-trivial logic; 100% on critical paths"}
**Mocking strategy:** {e.g., "Mock at the service boundary, not DB layer"}

---

## Security & Performance

### Security

| Concern | Mitigation |
|---------|-----------|
| {Input validation} | {e.g., Pydantic strict mode on all API inputs} |
| {Auth/Authz} | {e.g., JWT verified at middleware, RBAC in service} |
| {Secrets} | {e.g., Environment variables only, never logged} |
| {SQL injection} | {e.g., ORM parameterized queries throughout} |

### Performance

| Concern | Target | Approach |
|---------|--------|---------|
| {Latency} | {e.g., p99 < 200ms} | {e.g., DB indexes on `user_id`, caching layer} |
| {Throughput} | {e.g., 1000 req/s} | {e.g., Async handlers, connection pooling} |
| {Memory} | {e.g., < 256MB} | {e.g., Streaming responses, lazy loading} |

### Observability

{What logging, metrics, or tracing does this initiative add?}
- **Logs:** {Key events that must be logged — level, format, fields}
- **Metrics:** {Any new metrics or counters}
- **Traces:** {Span boundaries or trace propagation strategy}

---

## Implementation Sequence

{Order matters — list which pieces must be built first because others depend on them. This feeds directly into task breakdown.}

1. **Foundation** *(blocking)* — {e.g., DB schema migration, base interfaces, shared types}
2. **Core logic** *(depends on 1)* — {e.g., Service layer, business rules}
3. **API layer** *(depends on 2)* — {e.g., Endpoints, CLI commands}
4. **Integrations** *(depends on 2)* — {e.g., Third-party service adapters}
5. **Testing** *(parallel with 2–4)* — {e.g., Unit tests, integration tests, mocks}
6. **Polish** *(depends on 3–4)* — {e.g., Error messages, logging, observability}

**Parallel work opportunities:** {What can be built concurrently by separate developers/agents?}

**Known implementation risks:**
- {Risk: e.g., "Third-party API rate limits may require backpressure design" — explore in spike before committing to approach}
