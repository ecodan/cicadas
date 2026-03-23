
---
next_section: 'done'
---

# UX Design: auto-cicadas

## Progress

- [x] Design Goals & Constraints
- [x] User Journeys & Touchpoints
- [x] Information Architecture
- [x] Key User Flows
- [x] UI States
- [x] Copy & Tone
- [x] Visual Design Direction
- [x] UX Consistency Patterns
- [x] Responsive & Accessibility

---

## Design Goals & Constraints

**Primary goal:** The Builder should feel *in control without being in the driver's seat* — confident that something purposeful is happening, clear on what it decided and why, and never surprised by what it did. The emotional arc is: **calm trust** during execution, **clear orientation** at status updates, and **zero ambiguity** at escalation moments.

**Design constraints:**
- **Platform:** Terminal/CLI only (macOS, Linux). No web UI, no TUI framework. Plain stdout + `input()` stdin. All output must degrade gracefully to plain text.
- **Design system:** Extend existing Cicadas CLI conventions — status output follows `status.py` style (labeled sections, no color dependencies). Establish new patterns only where genuinely needed.
- **Technical limits:** No real-time streaming display (stdout is line-buffered). No cursor positioning or ANSI animation. Long-running phases (LLM calls) must surface progress with simple log lines, not spinners.
- **Async constraint (MVP):** Escalation blocks on `input()`. Design must be honest about this — copy must signal "the session is waiting here" not "come back later."
- **Observability over aesthetics:** The primary design value is *legibility of decisions* — every output line the Builder sees should help them answer "what happened?" and "why?", not impress them.

---

## User Journeys & Touchpoints

### Builder (post-spec) — Hands-Free Execution

**Entry point:** Skill command `implement hands-free` while on a registered feature branch with an approved `tasks.md`
**First touchpoint:** Session banner — initiative name, branch, stage detected, context loaded, intent summary printed
**Key moment:** First iteration log line — seeing the supervisor resolve an interrupt autonomously and the agent continue: *"that thing I would have had to answer, it got it right."*
**Exit state:** Terminal condition printed with a clear exit reason + path to `session-{ts}.json` for audit
**Pain points to design around:**
- Builder doesn't know if it's "stuck" or just thinking — long LLM calls must emit a "working…" heartbeat
- Builder can't tell what the agent is doing between interrupts — iteration counter and last action must be visible
- Escalation prompt must not be dismissable by accident — requires explicit answer, not just Enter

---

### Builder (mid-spec) — Partial Handoff

**Entry point:** Skill command `implement hands-free` with a draft folder that has some (but not all) specs complete
**First touchpoint:** Stage detection output — "Detected: PRD ✓, UX ✓, Tech ✗. Resuming from Tech Design."
**Key moment:** Watching the supervisor draft and present a spec section without any prompting — first time the user sees auto-emergence working
**Exit state:** Session hands off from emergence to execution seamlessly; no mode-switch ceremony
**Pain points to design around:**
- Builder must be able to confirm spec sections without losing context of what the supervisor is doing next
- Pause-and-wait at spec boundaries must be unambiguous — must not look like the session is stuck

---

### Builder — Interrupted Session Recovery

**Entry point:** Running `implement hands-free` when the previous session was interrupted
**First touchpoint:** Recovery prompt — lists interrupted session details (timestamp, last decision, terminal state) and offers three options: resume / restart / abort
**Key moment:** After resume: seeing the iteration counter pick up where it left off, prior decision log referenced
**Exit state:** Either normal completion or a new escalation/terminal condition
**Pain points to design around:**
- Builder must not accidentally start a fresh session when they meant to resume
- Must clearly communicate what state the branch is in (mid-operation vs clean) before resuming

---

## Information Architecture

The CLI has no navigation — it is a linear, sequential output stream. IA is about the *structure of output*, not navigation hierarchy.

```
supervise.py output stream
├── Session header (banner)
│   ├── Initiative / branch / stage
│   ├── Context bundle summary (files loaded, conventions inferred)
│   └── Intent summary (synthesized)
├── Iteration loop output (repeating)
│   ├── Iteration N header
│   ├── Agent step result (complete / interrupt / error)
│   ├── [if interrupt] Classification result (shallow / deep)
│   ├── [if shallow] Resolution (answer / escalate / skip) + reasoning
│   ├── [if deep] Phase 1 / Phase 2 / Phase 3 logs + resolution
│   └── [if escalate] Escalation prompt → awaiting input
├── Terminal condition banner
│   ├── Exit reason (completed / requires_human_input / unrecoverable_error)
│   ├── Stats summary (iterations, decisions, escalations, tokens)
│   └── Artifacts path (session log, escalations.md)
└── [if recovery needed] Recovery prompt (resume / restart / abort)
```

**Navigation model:** None — linear output stream. The Builder navigates backward by reading the session log file, not by re-running the CLI.

**Key entry points:**
- `python supervise.py --initiative {name} --branch {branch}` (direct CLI)
- `implement hands-free` skill command (auto-detects context)

---

## Key User Flows

### Flow 1: Successful Hands-Free Session (Happy Path)

1. Builder runs `implement hands-free` on a feature branch with approved `tasks.md`
2. Supervisor prints session banner: initiative, branch, context files loaded, intent summary
3. Supervisor sends first agent prompt; prints "Iteration 1 — agent running…"
4. Agent returns interrupt; supervisor classifies as shallow
5. Supervisor prints: "Interrupt: [question]. Classification: shallow. Resolved: answer — [reasoning]."
6. Agent prompt resumes with answer injected; loop continues
7. Steps 3–6 repeat across N iterations; deep interrupts print Phase 1/2/3 logs
8. Agent returns `complete`; supervisor prints terminal banner: "Completed. 40 iterations, 35 resolved, 5 escalated. Session: session-2026-03-22T14:00.json"

**Alternate path A (escalation):** Interrupt cannot be resolved → supervisor prints escalation block, prompts Builder for input, injects answer, resumes loop
**Alternate path B (max iterations):** 200 iterations hit → terminal condition `unrecoverable_error` with message explaining the cap

---

### Flow 2: Interrupted Session Recovery

1. Builder runs `implement hands-free` on a branch with an existing interrupted session
2. Supervisor detects interrupted session, prints recovery prompt:
   ```
   Interrupted session detected:
     Session: session-2026-03-21T09:30.json
     Last decision: Iteration 17, resolved (answer)
     Status: requires_human_input (awaiting escalation response)

   Options:
     [R] Resume — continue from last decision
     [S] Restart — new session, prior log preserved
     [A] Abort — clean up; run abort.py for branch rollback
   ```
3. Builder enters `R`; supervisor re-loads prior session context, injects resumption note into agent prompt
4. Execution continues from iteration 18

**Alternate path:** Builder enters `A` → supervisor delegates to `abort.py`, prompts whether to keep or delete interrupted session log

---

### Flow 3: Escalation Interaction

1. Supervisor cannot resolve interrupt confidently (or hits always-escalate rule)
2. Prints escalation block:
   ```
   ── ESCALATION ──────────────────────────────────────────────
   Iteration 23 | Deep decision | No consensus after retry

   Question: Should the auth module use JWT or session cookies?
   Context: Tech-design specifies "stateless where possible" but
            did not specify the token format for the API layer.
   Options the reviewers considered: JWT (Architect), cookies (UX)
   Recommendation: JWT — aligns with stateless constraint

   Your answer (or press Enter to accept recommendation):
   ──────────────────────────────────────────────────────────────
   ```
3. Builder types answer or presses Enter to accept recommendation
4. Response injected; session resumes; escalation written to `escalations.md`

---

### Flow 4: Dry-Run Mode

1. Builder runs `supervise.py --dry-run`
2. Session banner prints as normal; intent summary synthesized (or skipped if `--dry-run` skips LLM calls entirely — TBD in tech design)
3. Each agent step simulates an interrupt; supervisor prints what it *would* resolve with what reasoning
4. No actual LLM calls for supervisor activities (prints prompts instead)
5. Terminal condition: `dry_run_complete` — prints count of simulated decisions

---

## UI States

### Session Header

| State | Trigger | What the Builder Sees |
|-------|---------|----------------------|
| **Starting** | `supervise.py` launched | Banner: initiative, branch, stage, context loading |
| **Context loaded** | Bundle assembled | "Loaded N spec files, M module snapshots, conventions inferred" |
| **Intent synthesized** | Intent summary ready | Intent summary block printed |
| **Recovery needed** | Interrupted session detected | Recovery prompt with 3 options |

---

### Iteration Output

| State | Trigger | What the Builder Sees |
|-------|---------|----------------------|
| **Running** | Agent step in progress | "Iteration N — agent running…" |
| **Interrupt received** | Agent returned interrupt | Interrupt text + classification |
| **Shallow resolved** | Shallow path completes | Resolution type + one-line reasoning |
| **Deep — Phase 1** | Deep path, gathering input | "Phase 1: consulting reviewers…" + condensed opinions |
| **Deep — Phase 2** | Synthesis in progress | "Phase 2: reasoning…" + proposed resolution |
| **Deep — Phase 3** | Consensus vote | "Phase 3: seeking consensus… [agree/disagree/agree]" |
| **Deep resolved** | Consensus reached | Resolution + final reasoning |
| **Skip** | Rhetorical interrupt | "Iteration N — skip (status update, no decision needed)" |
| **Escalation** | Cannot resolve | Full escalation block; awaiting input |

---

### Terminal Conditions

| State | Trigger | What the Builder Sees |
|-------|---------|----------------------|
| **Completed** | Agent `complete` | "✓ Completed." + stats + session log path |
| **Requires human input** | Escalation session-blocking condition | "⚠ Requires human input." + escalation summary + resume instructions |
| **Unrecoverable error** | Agent `error` / unhandled exception / max iterations | "✗ Unrecoverable error." + error details + session log path |
| **Dry run complete** | `--dry-run` flag + agent step cycle completes | "— Dry run complete." + simulated decision count |

---

## Copy & Tone

**Voice:** Direct, transparent, technical. The supervisor speaks like a capable colleague reporting progress — no marketing language, no hedging, no excessive politeness. It respects the Builder's time and intelligence.

**Key principles:**
- **Narrate decisions, not just actions.** Don't just say "resolved" — say what was decided and why in one line.
- **Never hide uncertainty.** If the supervisor is uncertain, say so. Escalation copy must communicate *why* it couldn't resolve, not just that it couldn't.
- **Active verbs, present tense.** "Resolved: answer — using camelCase per project convention." Not "A resolution was reached."
- **Escalation is not failure.** Escalation copy should frame the pause as the supervisor doing its job — surfacing the right question — not apologizing for interrupting.
- **Stats are for audit, not self-congratulation.** Session summary is factual: iterations, decisions, escalations, tokens. No "great job" or "all done!"

**Critical copy samples:**

| Context | Copy |
|---------|------|
| Session banner | `auto-cicadas / feat/auth-module — post-spec execution` |
| Context loaded | `Context loaded: 5 spec files, 2 module snapshots, conventions inferred from 247 source files` |
| Intent summary header | `Intent: [synthesized summary]` |
| Iteration running | `Iteration 7 — agent running…` |
| Shallow resolved | `Interrupt: [question]. Shallow → answer: [one-line reasoning]` |
| Skip | `Iteration 12 — skip: agent status update, no decision needed` |
| Deep phase log | `Deep decision — Phase 1: Analyst [opinion], UX [opinion], Architect [opinion]` |
| Escalation header | `── ESCALATION ─────────────────────────────────────` |
| No-consensus escalation | `No consensus after retry. Escalating to human operator.` |
| Completed | `✓ Completed. 40 iterations · 35 resolved · 5 escalated · 12,400 tokens` |
| Requires human input | `⚠ Requires human input. Session paused. Resume with: supervise.py --resume session-{ts}.json` |
| Unrecoverable error | `✗ Unrecoverable error: [reason]. Session log: session-{ts}.json` |
| Recovery prompt header | `Interrupted session detected — choose recovery path:` |

---

## Visual Design Direction

**Style:** Terminal-native. No color requirements (monochrome-safe). Uses ASCII box-drawing characters and separators (`──`) for structure. Indentation and whitespace are the primary layout tools.

**Color palette:** Optional ANSI color for status symbols only (`✓` green, `⚠` yellow, `✗` red) — but all output must be legible without color. No color-only meaning.

**Typography:** Monospace (terminal default). No font choices — the shell font is the font.

**Spacing & density:** Compact during iteration loop (one line per resolved interrupt), comfortable for escalation blocks (padded, with `──` separators to visually isolate the human-interaction zone from the log stream).

**Existing design system:** Extending existing Cicadas CLI output conventions (see `status.py`, `check.py` output style). New pattern: the **escalation block** — bordered, padded, visually distinct from the log stream. This is the only novel visual element.

**Mood reference:** "git log meets a thoughtful colleague's Slack message — structured, dense when scanning, clear when something needs attention."

---

## UX Consistency Patterns

### Output Hierarchy
- **Section headers:** `── SECTION NAME ──────────` (dashes fill to ~60 chars)
- **Key-value pairs:** `Key: value` on one line for compact items
- **Multi-line blocks:** Indented 2 spaces under the header
- **Iteration log:** `Iteration N — [status]: [one-line content]`

### Status Symbols
- `✓` — success / completed
- `⚠` — warning / escalation / requires attention
- `✗` — error / failure
- `—` — neutral / informational (dry-run, skip)

Symbols appear at line-start for terminal conditions and phase headers. Never mid-sentence.

### Escalation Block Pattern
The escalation block is the single most important interaction in the system. It must:
- Be visually isolated from the log stream with `──` borders
- Include: iteration number, classification (shallow/deep), the question, context, options considered (if deep), a recommendation (if any)
- End with a clear input prompt that says what pressing Enter does (accept recommendation vs no default)
- Not be dismissable by accident — Enter with no input either accepts recommendation or re-prompts

### Progress Feedback
- LLM calls in progress: `[phase description]…` (e.g., "Phase 1: consulting reviewers…") — one line, then replaced by result
- Long operations (>5s): a single "still working…" line if no output yet — prevents "is it stuck?" anxiety

### Terminal Condition Block
Always ends the session output stream. Format:
```
── SESSION COMPLETE ──────────────────────────────────
Status:   ✓ Completed
Stats:    40 iterations · 35 resolved · 5 escalated · 12,400 tokens
Session:  .cicadas/active/auto-cicadas/supervisor/session-2026-03-22T14:00.json
Escalations: .cicadas/active/auto-cicadas/supervisor/escalations.md
──────────────────────────────────────────────────────
```

### Error Messages
- Always include: what failed, which iteration/phase, path to session log for debugging
- Never: generic "something went wrong" — always name the component and operation

---

## Responsive & Accessibility

**Breakpoints:** N/A — terminal only. No responsive layout.

**Accessibility standards:** WCAG not applicable (CLI). Terminal accessibility norms:
- All status information conveyed in text, not color alone — symbols (`✓`, `⚠`, `✗`) pair with text labels
- No reliance on cursor positioning or overwrite — output is append-only (screen readers can follow a scrolling log)
- Escalation prompt includes explicit instruction text — not just a bare cursor
- `--no-color` flag (Post-MVP) for environments that can't render ANSI codes

**Key requirements:**
- Keyboard only: all interaction via stdin text input — no mouse, no GUI
- Screen reader: append-only output stream is inherently compatible
- Color contrast: N/A (terminal colors inherit from user's terminal theme)
- No animation or cursor tricks that would confuse assistive tools
