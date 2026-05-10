---
summary: "ftue-and-flow UX establishes the Cicadas CLI interaction language for guidance and onboarding: ANSI-colored next-step hint blocks after every lifecycle command, a fully interactive tutorial mode that creates real artifacts, and a status command that always tells you what to do next. All hints are togglable; all output degrades gracefully in non-TTY environments."
phase: "ux"
when_to_load:
  - "When designing or reviewing hint output format, tutorial flow, status improvements, or copy tone."
  - "When implementing any new CLI output for this initiative."
depends_on:
  - "prd.md"
modules:
  - "src/cicadas/scripts/init.py"
  - "src/cicadas/scripts/tutorial.py"
  - "src/cicadas/scripts/status.py"
  - "src/cicadas/scripts/utils.py"
  - "src/cicadas/scripts/cicadas.py"
index:
  design_goals: "## Design Goals & Constraints"
  journeys: "## User Journeys & Touchpoints"
  flows: "## Key User Flows"
  ui_states: "## UI States"
  copy_tone: "## Copy & Tone"
  visual_direction: "## Visual Design Direction"
  consistency_patterns: "## UX Consistency Patterns"
  accessibility: "## Responsive & Accessibility"
next_section: "Design Goals & Constraints"
---

# UX Design: ftue-and-flow

## Progress

- [x] Design Goals & Constraints
- [x] User Journeys & Touchpoints
- [x] Key User Flows
- [x] UI States
- [x] Copy & Tone
- [x] Visual Design Direction
- [x] UX Consistency Patterns
- [x] Responsive & Accessibility

---

## Design Goals & Constraints

### Emotional Goal

Users should feel **guided, not lectured**. The experience must communicate: "I know where I am, I know what comes next, and I'm in control." Confidence, not hand-holding. The hints are a compass, not a GPS that makes decisions for you.

### Practical Constraints

- **CLI only** — no browser, no TUI framework. Output is printed to stdout/stderr using Python's stdlib only. No third-party dependencies (rich, click, etc.).
- **ANSI color** — used for hint blocks. Must degrade gracefully: detect TTY and strip colors when stdout is piped or redirected.
- **Additive only** — existing command output must be completely unchanged when hints are suppressed. No reformatting, no reordering.
- **Per-initiative config** — hints toggled via `hints` boolean in `.cicadas/config.json`. Default: `true`.
- **`--no-hints` flag** — per-invocation override, available on all lifecycle commands.
- **Tutorial is real** — no mocked steps. Tutorial output must look and feel exactly like real Cicadas output, because it *is* real Cicadas output.

---

## User Journeys & Touchpoints

### Alex — First-Timer: From Zero to First Branch

**Moment of arrival:** Alex runs `cicadas init` for the first time. The terminal is blank. They have no mental model.

**Moment of first value:** The tutorial offer appears. Alex says yes. Within minutes they see a real initiative branch created, a real draft folder, and a clear explanation of why each step exists. The concepts snap into place because they're watching them happen.

**Moment of first failure:** Alex skips a step (e.g., tries to run `kickoff` before there's a draft). The error message now includes a hint pointing to what they should do first, not just what went wrong.

**Touchpoints:** `cicadas init` (tutorial prompt) → tutorial walkthrough (step-by-step output) → "You're ready!" summary → first real `status` run.

---

### Jordan — Returning User: Back in Flow After a Break

**Moment of arrival:** Jordan runs `cicadas status` after weeks away. They see initiative names and branch states — familiar — but can't remember what step comes after branch creation.

**Moment of first value:** The "Next:" block at the bottom of `status` output shows the exact command. Jordan copies it and is implementing within 30 seconds.

**Moment of first failure:** Jordan runs a command in the wrong order (e.g., tries to `archive` before `update-index`). The hint block on the error explains the correct sequence.

**Touchpoints:** `cicadas status` → Next block → lifecycle commands with hints.

---

## Key User Flows

### Flow 1: First-Time Init with Tutorial (Happy Path)

```
User runs: cicadas init
───────────────────────────────────────────────────────────────
System:  ✓ Initialized .cicadas/ structure.

         🎓 First time here? Run the interactive tutorial to
            learn the Cicadas flow by doing.

         Would you like to run the tutorial now? [Y/n]:
───────────────────────────────────────────────────────────────
User: Y (or Enter)
───────────────────────────────────────────────────────────────
System:  [launches tutorial.py — see Flow 2]
```

**Alternate: `cicadas init --no-tutorial`**
```
System:  ✓ Initialized .cicadas/ structure.

         ╔══════════════════════════════════════════════════╗
         ║  Next: start your first initiative               ║
         ║  cicadas kickoff <name> --intent "..."           ║
         ║  Or run: cicadas init --tutorial  to learn first ║
         ╚══════════════════════════════════════════════════╝
```

---

### Flow 2: Tutorial Walkthrough (Happy Path)

Each tutorial step follows the same pattern:
1. **Concept banner** — colored header with the step name, the agent prompt to use, and what it does
2. **Agent prompt sample** — the exact natural-language prompt the user gives their AI agent
3. **Mock output** — pre-scripted output that mirrors exactly what real Cicadas produces
4. **What just happened** — one-line confirmation of what changed
5. **Press Enter to continue** — paced by the user, not auto-scrolling

> **Design principle**: Users interact with Cicadas through their AI agent using natural language. The tutorial teaches *what to say to the agent*, not which CLI flags to memorize. The underlying scripts are the agent's responsibility. The tutorial is purely display — no real git or filesystem changes occur.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 STEP 1 of 7 — Start the Initiative
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Every piece of work in Cicadas begins with a name.
 Tell your agent what you want to build and Cicadas
 creates a draft folder ready for your specs.

   💬 "Start an initiative called my-project"

 [mock output]
───────────────────────────────────────────────────────
 Created draft folder: .cicadas/drafts/my-project/
───────────────────────────────────────────────────────
 ✓ Draft folder ready — your specs will live here

 Press Enter to continue...
```

**The canonical 7-step Cicadas flow (tutorial mirrors this exactly):**

| Step | Name | Agent Prompt | Ends With |
|------|------|-------------|-----------|
| 1 | **Start** | 💬 "Start an initiative called my-project" | Draft folder created |
| 2 | **Define specs** | *(Cicadas guides this — no prompt needed)* | PRD, UX, tech-design, approach, tasks in drafts/ |
| 3 | **Kickoff** | 💬 "Kickoff the initiative" | Specs move to active/; initiative branch created |
| 4 | **Build** | 💬 "Implement partition 1" | Code implemented on feature branch |
| 5 | **Complete partition** | 💬 "Code review and complete partition" | Feature branch merged to initiative branch |
| 4-5 | *(repeat for each partition)* | | |
| 6 | **PR** | 💬 "Create a PR" | Initiative branch pushed; PR opened |
| 7 | **Complete** | 💬 "Complete the initiative" | Merged to main; specs archived; canon updated |

**Tutorial completion:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 🎉 You're ready!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 You've seen the full Cicadas flow. Here's the playbook:

   1. 💬 "Start an initiative called <name>"
   2.    Cicadas guides you through specs
   3. 💬 "Kickoff the initiative"
   4. 💬 "Implement partition <name>"
   5. 💬 "Code review and complete partition"
      (repeat 4-5 for each partition)
   6. 💬 "Create a PR"
   7. 💬 "Complete the initiative"

 Ready to build something real? Start with step 1.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Flow 3: Normal Command with Hints (Happy Path)

After `cicadas kickoff my-feature --intent "..."`:

```
✓ Promoted drafts to .cicadas/active/my-feature/
✓ Registered initiative: my-feature
✓ Created branch: initiative/my-feature
✓ Pushed to remote: origin/initiative/my-feature

╔══════════════════════════════════════════════════════════════╗
║  Next: start your first feature branch                       ║
║  Tell your agent:                                            ║
║    💬 "Start a feature branch for <partition name>"          ║
║                                                              ║
║  Tip: one branch per logical partition in approach.md        ║
╚══════════════════════════════════════════════════════════════╝
```

After `cicadas branch feat/my-partition --intent "..." --initiative my-feature`:

```
✓ Registered branch: feat/my-partition
✓ Created and pushed branch: feat/my-partition

╔══════════════════════════════════════════════════════════════╗
║  Next: implement on this branch                              ║
║  Tell your agent:                                            ║
║    💬 "Implement task 1" (or whichever task is next)         ║
║    💬 "Open a PR for this feature" when done                 ║
╚══════════════════════════════════════════════════════════════╝
```

---

### Flow 4: Status with Inferred Next Step

When no lifecycle.json is present but an initiative is registered with no branches:

```
Project: my-project

Active Initiatives (1):
  - my-feature: My first initiative.

Active Feature Branches (0):
  (none)

╔══════════════════════════════════════════════════════════════╗
║  Next: create your first feature branch                      ║
║  Tell your agent:                                            ║
║    💬 "Start a feature branch for <partition name>"          ║
╚══════════════════════════════════════════════════════════════╝
```

When no `.cicadas/` at all:

```
╔══════════════════════════════════════════════════════════════╗
║  No Cicadas project found.                                   ║
║  Tell your agent:                                            ║
║    💬 "Initialize cicadas"                                   ║
╚══════════════════════════════════════════════════════════════╝
```

---

## UI States

### Hint Block

| State | Appearance |
|-------|-----------|
| **Default (TTY)** | ANSI cyan box with `╔══╗` border, `║` sides, `╚══╝` bottom; "Next:" header in bold |
| **Non-TTY / piped** | No output (hints suppressed entirely when stdout is not a TTY) |
| **`--no-hints`** | No output |
| **`hints: false` in config** | No output |

### Tutorial Step

| State | Appearance |
|-------|-----------|
| **Step banner** | Bold white `━━━` divider, step number in cyan, concept title |
| **Running command** | Dim gray "Running: ..." line before real output |
| **What happened** | Green `✓` checkmark with artifact path |
| **Waiting** | "Press Enter to continue..." in dim gray |
| **Completion** | Full-width `━━━` divider, green `🎉 You're ready!` header, artifact list, cleanup commands |

### Status Command

| State | Appearance |
|-------|-----------|
| **Normal (with lifecycle)** | Existing output + Next block (already implemented) |
| **No lifecycle, has initiatives** | Existing output + inferred Next block |
| **No initiatives** | Existing empty state message + Next block pointing to kickoff |
| **No `.cicadas/`** | Single-line "No Cicadas project found" + Next block pointing to init |

### Error States

| Scenario | Hint behavior |
|----------|--------------|
| Command fails with usage error | Hint block shows the correct usage and what to do instead |
| Script exits non-zero | No hint block (don't guide after an unrecoverable failure) |

---

## Copy & Tone

### Voice

**Guides, doesn't lecture.** The copy assumes the user is competent and just needs orientation. Avoid "You must..." — prefer "Next:". Avoid long explanations mid-flow — save those for the tutorial.

**Active, present tense.** "Create your first branch" not "A branch should be created."

**Exact commands, not descriptions.** Every hint includes the actual command, not a paraphrase. The user should be able to copy-paste.

### Key Copy Samples

**Tutorial offer (first run):**
> `🎓 First time here? Run the interactive tutorial to learn the Cicadas flow by doing.`
> `Would you like to run the tutorial now? [Y/n]:`

**Tutorial step concept (example — Kickoff):**
> `Kickoff promotes your draft specs to 'active' and creates the initiative branch in git.`
> `Nothing is implemented yet — kickoff is a planning gate, not a code gate.`

**Tutorial completion:**
> `🎉 You're ready! You've seen the full Cicadas flow. Your next step is your first real initiative.`

**Next-step hint (after kickoff):**
> `Next: start your first feature branch`
> `Tell your agent: 💬 "Start a feature branch for <partition name>"`

**Next-step hint (after branch):**
> `Next: implement on this branch`
> `Tell your agent: 💬 "Implement task 1" (or whichever task is next)`
> `Tell your agent: 💬 "Open a PR for this feature" when done`

**Status — no project:**
> `No Cicadas project found.`
> `Tell your agent: 💬 "Initialize cicadas"`

**Hint suppression confirmation (when `hints: false` is written to config):**
> `✓ Hints disabled. Re-enable with: hints: true in .cicadas/config.json`

### Tone Rules
- No em-dashes in CLI output (terminal rendering varies).
- No markdown in CLI output (no `**bold**` — use ANSI or plain text).
- Checkmarks (`✓`) for success, `╔╗` box for hints, `━━━` for tutorial dividers.
- Max hint block width: 66 characters (fits 80-column terminals with margin).

---

## Visual Design Direction

This is a CLI product — visual design means **output formatting conventions**, not pixels.

### Color Palette (ANSI)

| Element | Color | Code |
|---------|-------|------|
| Hint box border & "Next:" label | Cyan | `\033[36m` |
| Tutorial step banner | Bold white | `\033[1;37m` |
| Tutorial concept text | Default (no color) | — |
| Success checkmark (`✓`) | Green | `\033[32m` |
| "Running: ..." lines | Dim | `\033[2m` |
| "Press Enter..." prompt | Dim | `\033[2m` |
| Tutorial completion header | Bold green | `\033[1;32m` |
| Error context in hints | Yellow | `\033[33m` |
| Reset | — | `\033[0m` |

### Density
- Hint block: max 8 lines. If the next step needs more explanation, trim — hints are orientation, not docs.
- Tutorial steps: max 6 lines of concept text before the command runs.
- One blank line before hint block; one blank line after. Never two blank lines.

### TTY Detection
```python
import sys
HINTS_ENABLED = sys.stdout.isatty()  # base check; overridden by config/flag
```
When not a TTY, all hint and tutorial color output is suppressed. Plain-text content (tutorial step explanations) still prints.

---

## UX Consistency Patterns

### Hint Block Pattern
All hints use the same box-drawing pattern. Never use ad-hoc print statements for guidance:

```
╔══════════════════════════════════════════════════════════════╗
║  Next: <one-line description>                                ║
║  <exact command>                                             ║
║  [optional: one tip line]                                    ║
╚══════════════════════════════════════════════════════════════╝
```

Rules:
- Always starts with "Next:" on the first content line.
- Exact command on the second line.
- Optional tip on a third line (never more than three content lines).
- Box width: 66 chars including borders.

### Tutorial Step Pattern
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 STEP N of M — <Concept Title>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 <2-3 sentence explanation>

 Running: <command>
───────────────────────────────────────────────────────
 [real command output]
───────────────────────────────────────────────────────
 ✓ <What was created/changed>

 Press Enter to continue...
```

### Suppression Pattern
A centralized `hints_enabled(config, args)` utility function determines hint state:
1. If `--no-hints` in args → False
2. If `hints: false` in `.cicadas/config.json` → False
3. If `not sys.stdout.isatty()` → False (suppress colors; tutorial text still prints)
4. Otherwise → True

All lifecycle scripts call this function before printing any hint block. Never inline the logic.

### Config Toggle UX
When a user sets `hints: false` in config, the next command confirms it with a single green line. No repeated reminders.

---

## Responsive & Accessibility

**CLI-only product — no responsive design required.**

### Terminal Compatibility
- All output must render correctly in 80-column terminals (minimum).
- Box-drawing characters (`╔`, `║`, `╚`, `━`, `─`) are UTF-8; assume modern terminals. No fallback to ASCII boxes in MVP (can add in v2 if reported).
- ANSI escape codes: standard 16-color codes only (no 256-color or true-color). Compatible with macOS Terminal, iTerm2, VS Code integrated terminal, and standard Linux terminals.

### Accessibility
- All information conveyed by color is also conveyed by structure (e.g., "Next:" label is text, not just color).
- Non-TTY environments (CI, scripts, pipes) see no hint output — hints never pollute machine-readable output.
- Tutorial "Press Enter to continue" is keyboard-only; no mouse required (obviously).
