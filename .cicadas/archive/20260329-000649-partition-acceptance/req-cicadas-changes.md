# Requirements: Cicadas Changes for Partition-Level QA

## Context

Chorus is adopting a partition-level execution model: one partition at a time, fresh agent session per partition, with an evaluator QA agent grading each partition before its feature branch is merged. For this to work, Cicadas must generate partition specs that are machine-testable, not just human-readable.

---

## Requirements

### 1. Acceptance Criteria Section

Every partition spec must include an `## Acceptance Criteria` section containing a checklist of testable, specific pass/fail statements.

**Rules for criteria:**
- Each criterion must be independently verifiable by an automated agent
- Criteria must be falsifiable — "the API returns a 201" not "the API works correctly"
- Avoid subjective criteria ("looks good", "is intuitive") — if a UI behavior needs testing, describe the interaction and expected outcome
- Use checkbox format (`- [ ]`) so the evaluator can report pass/fail per item

**Examples of good criteria:**
```markdown
## Acceptance Criteria
- [ ] POST /api/items returns 201 with `{id, name, createdAt}` when given valid payload
- [ ] POST /api/items returns 422 when `name` is missing
- [ ] GET /api/items returns paginated results with `X-Total-Count` response header
- [ ] Submitting the form with an empty required field displays an inline validation error without a page reload
- [ ] The items list re-renders within 500ms of a successful POST without a full page refresh
```

**Examples of bad criteria (rewrite these):**
```markdown
- [ ] The API is robust              ← not falsifiable
- [ ] The UI is responsive           ← not specific
- [ ] Error handling works           ← not observable
```

---

### 2. Artifact Type Annotation

Every partition spec must declare what kind of artifact it produces. This tells the evaluator what harness to set up.

**Format:**

```markdown
## Artifact Type
web-ui | rest-api | cli | library | background-service | full-stack
```

For `full-stack`, the evaluator will start both server and client and test via browser.

---

### 3. How to Run Section

Every partition spec must include a `## How to Run` section with the exact command(s) needed to start the artifact for testing. The evaluator uses this verbatim.

**Format:**

```markdown
## How to Run
- start: `npm run dev -- --port 3000`
- ready-check: `GET http://localhost:3000/health` returns 200
- teardown: `Ctrl+C` (process group kill)
```

For libraries and CLIs, `start` may be omitted if there is no persistent process.

For `ready-check`: the evaluator will poll this endpoint/condition before beginning test execution. Required for any artifact that starts a server.

---

### 4. Skill Generation Behavior

The Cicadas spec-writing skill must:

1. **Infer artifact type** from the partition description and initiative context. When ambiguous, ask.
2. **Generate acceptance criteria** that match the artifact type — API criteria for APIs, interaction criteria for UIs, output criteria for CLIs.
3. **Generate the How to Run section** based on the project's build tooling (detect from `package.json`, `pyproject.toml`, `Makefile`, `Dockerfile`, etc.).
4. **Flag untestable criteria** with a `<!-- NEEDS MANUAL REVIEW -->` comment so the human author can revise before execution.

---

### 5. Partition Completion Signal Convention

The coding agent signals partition completion by writing a sentinel file:

```
.cicadas/active/{initiative}/supervisor/partition-{partition-name}-complete.md
```

**Contents:**
```markdown
# Partition Complete: {partition-name}

## Summary
{1-3 sentences describing what was built}

## Canon Entry
{what should be written to canon — key decisions, APIs, file locations}

## Notes for Evaluator
{anything the evaluator should know: known limitations, test data needed, env vars}
```

The supervisor watches for this file and triggers the evaluator when it appears. Cicadas should document this convention so the coding agent's prompt includes it.

---

## Out of Scope

- Cicadas does not run the evaluator — that is Chorus's responsibility
- Cicadas does not define retry behavior — that is the supervisor's job
- Criteria for subjective design quality (aesthetics, UX feel) are explicitly out of scope for automated evaluation; these remain human review items
