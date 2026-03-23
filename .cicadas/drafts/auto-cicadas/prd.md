---
next_section: 'done'
---

# PRD: auto-cicadas

## Progress

- [x] Executive Summary
- [x] Project Classification
- [x] Success Criteria
- [x] User Journeys
- [x] Scope & Phasing
- [x] Functional Requirements
- [x] Non-Functional Requirements
- [x] Open Questions
- [x] Risk Mitigation

---

## Executive Summary

**auto-cicadas** is a hands-free execution mode for the Cicadas methodology that wraps the full initiative lifecycle — spec authoring, feature branch work, and task implementation — in a supervisor run loop. A Builder can launch it at any stage (blank slate, mid-spec, or post-spec) and step away; the supervisor resolves agent interrupts autonomously from the active spec, escalating only when the spec is silent or confidence is too low. The session runs until one of three terminal conditions: **completed** (all tasks done), **requires_human_input** (genuine ambiguity the spec doesn't resolve), or **unrecoverable_error**.

### What Makes This Special

- **Spec-grounded autonomy** — The supervisor doesn't hallucinate decisions; it resolves from the spirit and intent of what the Builder already specified, enforcing hard escalation boundaries for scope expansion, destructive ops, and anything irreversible.
- **Multiple entry points** — Works from zero ("build me a Slack clone"), from any approved spec, or from a fully-reviewed `tasks.md` — same supervisor loop regardless of entry point.
- **Transparent escalation trail** — Every autonomous decision and every escalation is durably logged (`session-{ts}.json`, `escalations.md`, `authority.md`) so the Builder can audit, resume, or replay any session.

---

## Project Classification

**Technical Type:** Developer Tool / Framework Extension
**Domain:** Developer Productivity / AI Orchestration
**Complexity:** High — multi-layer supervisor/agent/spec integration with non-deterministic AI execution paths, session state management, and robust success/failure detection
**Project Context:** Brownfield — extends the existing Cicadas CLI toolset; adds `supervise.py` as a first-class script, integrates with all existing scripts (`kickoff.py`, `branch.py`, `status.py`, `open_pr.py`, etc.), and adds an "implement hands-free" skill command

---

## Success Criteria

### User Success

A user achieves success when they can:

1. **Launch hands-free mode at any entry point** — invoke via skill command or CLI and have the supervisor correctly identify its stage, load the right specs, and proceed without manual setup.
2. **Walk away and return to a terminal state** — the session ends with one of three unambiguous outcomes: `completed`, `requires_human_input`, or `unrecoverable_error`, each with a clear explanation.
3. **Audit every autonomous decision** — after any session, the Builder can read `session-{ts}.json` and `escalations.md` and understand exactly what the supervisor decided and why, with no black-box gaps.

### Technical Success

The system is successful when:

1. **Escalation rate is low on well-specified initiatives** — for an initiative with a complete, unambiguous `tasks.md`, >80% of agent interrupts are resolved autonomously.
2. **Zero unsafe autonomous decisions** — the supervisor never autonomously approves scope expansion, destructive operations, schema changes, or merge/PR actions.
3. **Session recovery works** — an interrupted session can be resumed, restarted, or aborted cleanly without corrupting `.cicadas/` state.

### Measurable Outcomes

- Hands-free session completes a fully-specced single-feature initiative end-to-end without human intervention in ≥1 reference scenario.
- Supervisor correctly escalates 100% of "always escalate" category interrupts across a test suite.
- Session log is durably written (no data loss on crash or `KeyboardInterrupt`).

---

## User Journeys

### Journey 1: The Builder — Hands-Free Initiative Execution

Dan has a fully-reviewed `tasks.md` for a new feature. He runs `implement hands-free` from the Cicadas skill and steps away from active driving. The supervisor works through 40 agent interrupts, resolving 35 autonomously — filing naming questions from project conventions, approach questions from the tech-design, scope questions from the PRD. For the 5 it can't resolve confidently, it blocks and prints a clear escalation prompt to the terminal. Dan returns when convenient, answers each, and the loop continues. An hour later the branch is complete. He reads `escalations.md` to understand what the agent encountered and whether the authority policy needs tuning.

**Requirements Revealed:** supervisor run loop, spec-grounded interrupt resolution, terminal escalation UI, session log, authority policy, pluggable escalation transport (designed for async extension), skill command entry point.

---

### Journey 2: The Builder — Blank-Slate Auto Mode

Dan has an idea: "build a Slack clone." He invokes `implement hands-free` from scratch. The supervisor drives Clarify → UX → Tech → Approach → Tasks autonomously, pausing at section boundaries per configured pace for Dan's approval. After each spec is approved, the supervisor continues. Once `tasks.md` is approved, it kicks off the initiative, registers branches, and begins implementing. Dan's role is reviewer and escalation responder, not driver.

**Requirements Revealed:** auto-emergence (spec authoring loop), stage detection, configurable pause points (pace), seamless handoff from emergence to kickoff to execution, single skill command entry point.

---

### Journey 3: The Builder — Mid-Spec Handoff

Dan has approved the PRD and UX but doesn't want to manually drive Tech → Approach → Tasks. He invokes `implement hands-free`. The supervisor detects the current draft state, completes the remaining emergence steps (pausing at section boundaries for approval), then proceeds to kickoff and execution without further prompting.

**Requirements Revealed:** stage detection, partial spec resume, consistent pause-point enforcement regardless of entry point.

---

### Journey Requirements Summary

| User Type | Key Requirements |
|-----------|-----------------|
| **Builder (post-spec)** | supervisor run loop, interrupt resolution, escalation CLI, session log, authority policy |
| **Builder (blank-slate)** | auto-emergence, single skill entry point, pace-aware pausing, auto-kickoff |
| **Builder (mid-spec)** | stage detection, partial spec resume, seamless emergence-to-build handoff |

---

## Scope

### MVP — Minimum Viable Product (v1)

**Core Deliverables:**
- `supervise.py` — full supervisor run loop with three-phase deep resolution (party mode), shallow path, classification, intent summary, session persistence, terminal escalation UI
- Entry point: post-spec (initiative + branch exist in `.cicadas/active/`); invokable via `implement hands-free` skill command or CLI
- Three terminal conditions: `completed`, `requires_human_input`, `unrecoverable_error`
- Durable session persistence: decisions appended per-resolution; `session-{ts}.json`, `escalations.md`, `authority.md`
- Session recovery: resume, restart, or abort an interrupted session
- Integration with existing Cicadas scripts (`status.py`, `open_pr.py` BLOCK gate, `abort.py`)
- Pluggable escalation transport interface (terminal implementation only)
- Model tiering: fast model for execution, thinking model for supervisor activities
- Standard Cicadas `agents.json` config for model selection
- Token usage logged via `tokens.py`
- `--dry-run` mode
- `SKILL.md` updated with "Implement hands-free" Builder command

**Quality Gates:**
- Supervisor never autonomously resolves any "always escalate" category interrupt
- No decisions lost to crash or `KeyboardInterrupt`
- All existing Cicadas tests continue to pass
- 80%+ test coverage on supervisor core logic

### Growth Features (Post-MVP)

**v2: Auto-Emergence**
- Entry point: blank-slate and mid-spec — supervisor drives or completes emergence, then transitions to execution
- Stage detection from current draft/active state

**v3: Async Escalation Transport**
- Pluggable transport implementations: Slack webhook, ntfy.sh, email
- Builder responds async; supervisor polls with configurable timeout

### Vision (Future)

- Multi-branch parallel supervision
- Authority policy auto-tuning from annotated session decision logs
- Supervisor learns from prior sessions across initiatives

---

## Functional Requirements

### 1. Supervisor Run Loop

**FR-1.1:** The supervisor runs an iteration loop: send prompt to agent → receive step result (`complete` / `interrupt` / `error`) → route accordingly. Continues until a terminal condition or `max_iterations` is hit.

**FR-1.2:** Three terminal conditions:
- `completed` — agent returned `type: complete`
- `requires_human_input` — supervisor escalated and session paused awaiting human operator
- `unrecoverable_error` — agent returned `type: error`, or an unhandled exception occurred

**FR-1.3:** A hard `max_iterations` cap (default 200, configurable via `--max-iter`) prevents runaway sessions.

---

### 2. Interrupt Resolution — Classification

**FR-2.1:** Every agent interrupt is first passed through a **classifier** (single thinking model call) that determines: `shallow` or `deep`.

**FR-2.2:** Classification heuristics for `deep`:
- Architectural impact (new dependencies, data structures, API contracts)
- One-way-door decisions (hard or expensive to reverse)
- Cross-cutting impact (affects multiple modules or future branches)
- TCO tradeoffs (performance, security, extensibility, maintainability)
- Scope boundary questions

**FR-2.3:** Classification heuristics for `shallow`:
- Naming within established project conventions
- Import ordering, code style, comments
- Test fixture construction
- Choice between implementations with no meaningful tradeoff

**FR-2.4:** Classification result is logged with each decision record.

---

### 3. Interrupt Resolution — Shallow Path

**FR-3.1:** Shallow interrupts are resolved with a single thinking model call grounded in the full context bundle (specs, intent summary, authority policy, full session decision history, canon).

**FR-3.2:** Resolution types:
- `answer` — resolved confidently; inject response into agent
- `escalate` — cannot resolve confidently; pause session for human operator
- `skip` — rhetorical or status update; no decision needed, loop continues silently

**FR-3.3:** Resolutions with confidence below a configurable threshold (default 0.75, `--confidence` flag) are downgraded to `escalate`.

---

### 4. Interrupt Resolution — Deep Path (Party Mode)

**FR-4.1:** Deep interrupts run a three-phase resolution process:

**Phase 1 — Gather Input:** Three reviewer calls run in parallel (thinking model), each grounded in their specific spec:
- **Analyst** (PRD): does this serve product intent and user needs?
- **UX Reviewer** (UX doc): does this affect the experience or interaction model?
- **Architect** (tech-design): does this align with architecture, constraints, and patterns?

Each returns an opinion, reasoning, and confidence.

**Phase 2 — Reason & Decide:** A synthesis call (thinking model) receives all three reviewer opinions plus the full context bundle and produces a proposed resolution with reasoning.

**Phase 3 — Seek Consensus:** The proposed resolution is sent to all three reviewers in parallel. Each votes `agree` / `disagree` with reasoning.

**FR-4.2:** Consensus reached (majority agree above confidence threshold) → resolution accepted, injected, logged.

**FR-4.3:** No consensus → one retry: Phase 2 re-runs with reviewer disagreements as additional input → revised resolution → Phase 3 re-runs.

**FR-4.4:** No consensus after retry → `escalate` regardless of synthesis output.

**FR-4.5:** Maximum LLM calls per deep decision: 12 (worst case, ~4 serial depths due to parallelism).

---

### 5. Context Bundle & Intent Summary

**FR-5.1:** At session start, the supervisor assembles a context bundle:
- `canon/summary.md` (if present)
- All `*.md` files in `.cicadas/active/{initiative}/` (excluding `review.md`, `escalations.md`)
- Module snapshots for the branch's declared scope
- `emergence-config.json`
- Inferred project conventions (naming patterns, file structure from codebase scan)
- Tech stack and dependency list
- Branch git log (refreshed each iteration)

**FR-5.2:** At session start, the supervisor synthesizes an **intent summary** (thinking model) — a compact statement of the branch's purpose, priorities, acceptable tradeoffs, and constraints. This anchors all resolution decisions.

---

### 6. Authority Policy

**FR-6.1:** The authority policy classifies decision categories and provides resolution heuristics (not just permission gates). Three tiers: Autonomous (with heuristic), Conditional (with heuristic), Always Escalate.

**FR-6.2:** On first session, a default conservative policy is used and written to the supervisor namespace: `.cicadas/{drafts|active}/{initiative}/supervisor/authority.md` (same `active/`-first resolution as session files).

**FR-6.3:** On subsequent sessions, the policy is read from `authority.md`. Human operator may annotate wrong decisions post-session; annotations are incorporated on next session start.

---

### 7. Session Persistence

**FR-7.1:** Session file is created at session start with metadata in `.cicadas/{drafts|active}/{initiative}/supervisor/session-{timestamp}.json` — `active/` takes precedence; `drafts/` is the fallback (used during emergence before kickoff). Each decision is appended immediately after resolution.

**FR-7.2:** Exit reason and `completed` flag are written on all termination paths (clean, error, `KeyboardInterrupt`).

**FR-7.3:** `escalations.md` is appended immediately on each escalation (in the same supervisor namespace as the session file) before the human operator is prompted.

---

### 8. Session Recovery

**FR-8.1:** An interrupted session supports three recovery paths invokable from the skill command or CLI:
- **Resume** (`--resume {session-file}`) — continue from last decision, injecting prior context into the agent
- **Restart** — begin a new session on the same initiative/branch; prior session logs preserved for reference
- **Abort** — discard session cleanly; delegates to existing `abort.py` for branch rollback if needed

**FR-8.2:** When an interrupted session is detected on the current branch, the skill command surfaces the three recovery options before starting a new session.

---

### 9. Escalation Transport

**FR-9.1:** Escalation is handled via an abstracted transport interface with a single MVP implementation: print to stdout, collect via `input()`.

**FR-9.2:** The interface supports async substitution (Slack, ntfy, email) without modifying the core loop (Post-MVP).

**FR-9.3:** Each escalation is appended to `escalations.md` before prompting the human operator.

---

### 10. Agent Integration Interface

**FR-10.1:** Agent step abstracted behind `_agent_step()`: returns `{"type": "complete"|"interrupt"|"error", ...}`.

**FR-10.2:** MVP target: Claude Code subprocess (`subprocess.run(["claude", "--print", message])`).

**FR-10.3:** `--dry-run` skips thinking model calls and `input()` prompts; agent integration still required.

---

### 11. Model Tiering

**FR-11.1:** Execution (agent) uses a configurable fast model (default: `claude-haiku-4-5`).

**FR-11.2:** Supervisor activities (classifier, reviewer calls, synthesis, consensus, intent summary) use a configurable thinking model (default: `claude-sonnet-4-6`).

**FR-11.3:** Model selection follows the standard Cicadas `agents.json` / `_models` config format — both models swappable without code changes.

---

### 12. CLI & Skill Integration

**FR-12.1:** Direct CLI: `python supervise.py --initiative {name} --branch {branch}` with optional `--prompt`, `--dry-run`, `--max-iter`, `--confidence`, `--resume`.

**FR-12.2:** Skill command: **"implement hands-free"** (and natural variants). The skill auto-detects initiative and branch from git + `registry.json`, detects current stage, sets the appropriate initial prompt, and calls `supervise.py`.

**FR-12.3:** `SKILL.md` Builder Commands table gains an **"Implement hands-free"** entry.

**FR-12.4:** Script added to `src/cicadas/scripts/` and documented in `CLAUDE.md`.

---

### 13. Eval Sample Collection

**FR-13.1:** After every resolved interrupt, chorus appends an eval sample to `supervisor/eval-samples/{session_id}.jsonl` (JSONL, one object per line). Writing is best-effort — a write failure logs a warning and does not interrupt the supervisor loop.

**FR-13.2:** Each sample captures: `sample_id` (UUID), `captured_at` (ISO-8601 UTC), `initiative`, `question`, `context`, `resolution_path`, `classifier_output` (confidence + tier), `party_outputs` (reviewer texts, synthesis, consensus — null on shallow path), `final_answer`, and `label` (always `null` at capture; intended for human annotation).

**FR-13.3:** Eval logging is enabled by default. A `--no-eval-log` CLI flag disables it for a session.

**FR-13.4:** Eval samples accumulate across sessions within the same initiative. Each session writes its own JSONL file; the directory acts as the dataset. No rotation or cleanup is performed by chorus.

---

## Non-Functional Requirements

- **Performance:** Shallow interrupt resolution <5s. Deep interrupt resolution <30s worst case (parallel reviewer calls + synthesis + consensus + one retry). Intent summary synthesis at session start <15s. Soft targets — correctness takes priority over speed.

- **Reliability:** Session state is durable — no decision lost to crash or `KeyboardInterrupt`. Session file append-written per decision; exit status written on all termination paths. Interrupted sessions are resumable, restartable, or abortable cleanly.

- **Cost:** Shallow decisions: ~1 thinking model call. Deep decisions: up to 12 calls worst case, ~8 happy path. Token usage logged per session via `tokens.py` for visibility in `history.py`. Model tiering (Haiku for execution, Sonnet for supervision) keeps costs manageable.

- **Security:** The supervisor only injects text into agent context — it never executes shell commands autonomously. Authority policy's "always escalate" tier covers all destructive, credential, and production-data operations. Spec bundle contents are treated as data; supervisor does not act on directives found in specs.

- **Maintainability:** Supervisor activities (classify, review, synthesize, consensus) are isolated, testable functions. Agent integration and escalation transport are each behind a single abstracted interface. Model config follows standard Cicadas `agents.json` format. Test coverage target: 80%+ on supervisor core logic.

- **Extensibility:** Async escalation transport addable by implementing transport interface with no core loop changes. Additional reviewer personas addable by extending reviewer config with no algorithm changes.

---

## Open Questions

1. **Agent output parsing** — `claude --print` output format for detecting interrupt/complete/error signals is undocumented. How reliably can pause points be detected from stdout? Does a structured JSON output mode exist? *(Owner: tech design; resolve before implementation)*

2. **Consensus threshold** — "majority agree above confidence threshold" needs a concrete definition: majority vote (2/3), weighted by confidence, or unanimous for one-way-door decisions? *(Owner: tech design)*

3. **Spec bundle refresh** — bundle loaded once at session start. If agent Reflects and updates `tasks.md` mid-session, supervisor won't see it. Should bundle refresh at configurable checkpoints (e.g. after each PR task)? *(Owner: tech design)*

4. **Intent summary staleness** — for very long sessions with significant code divergence, intent summary may become stale. Is periodic re-synthesis needed? *(Owner: tech design)*

5. **Authority policy bootstrapping** — should supervisor generate a spec-specific policy on first run using the intent summary, rather than using hardcoded defaults? *(Owner: tech design)*

6. **Multi-branch supervision** — MVP is single branch. Post-MVP parallel supervision requires coordination to avoid conflicting decisions. Architecture should not preclude it. *(Owner: future)*

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Agent output format is unparseable — `claude --print` doesn't emit structured interrupt/complete/error signals | High | High | Spike agent integration early; abstraction layer allows output format negotiation or a wrapper prompt forcing structured JSON |
| Supervisor makes a confidently wrong deep decision — all three reviewers agree on the wrong answer | Med | High | Post-session feedback loop flags wrong decisions and hardens authority policy; full audit trail in session log |
| LLM API latency spikes make deep decisions too slow | Med | Med | Reviewer calls parallelized; configurable confidence threshold trades autonomy for speed; shallow path handles majority of decisions |
| Token costs exceed acceptable limits for long sessions | Med | Med | Token usage logged; model tiering keeps costs down; confidence threshold tunable to reduce deep-path invocations |
| Session resume corrupts `.cicadas/` state if agent left mid-operation | Low | High | Resume reads last session JSON for context; does not replay agent actions; Builder warned to inspect branch state before resuming |
| Scope creep — supervisor approves out-of-spec additions | Low | High | Authority policy classifies scope expansion as always-escalate; Analyst reviewer grounded in PRD scope; party mode disagreement auto-escalates |
| Claude Code subprocess integration breaks across CLI versions | Low | Med | Agent integration behind abstracted interface; version-pinned in dependencies; integration tested in CI |
