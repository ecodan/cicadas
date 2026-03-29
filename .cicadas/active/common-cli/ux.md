---
next_section: "Tech Design"
---

# UX Design: common-cli

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

**Primary goal:** Make Cicadas feel legible and queryable to development agents by giving them one stable, self-describing command surface they can inspect at runtime.

**Design constraints:**
- Primary target is terminal-based, agent-operated workflows inside a repo-local environment.
- There is no formal UX canon file to extend, so the design should preserve current CLI conventions and existing lifecycle terminology.
- MVP must wrap existing deterministic behaviors rather than redesign workflow semantics.
- The interface should remain repo-local and should not assume a global installation.

**Skip condition:** Not applicable. This initiative changes the interaction surface directly, even though it is terminal-first instead of graphical.

---

## User Journeys & Touchpoints

### Development Agent — Runtime Discovery and Execution

**Entry point:** The agent starts in a Cicadas-managed repository and needs to perform a lifecycle action without relying on memorized script paths.
**First touchpoint:** The agent invokes the common CLI with top-level help.
**Key moment:** The agent recognizes the available subcommands, chooses one, and can inspect subcommand help without leaving the terminal.
**Exit state:** The agent completes the requested lifecycle action through the common CLI and can cite the same interface in future steps.
**Pain points to design around:** Hidden command names, ambiguous argument shapes, help text that is too sparse for autonomous use, and mixed old/new invocation patterns in docs.

---

### Cicadas Maintainer — Consistent Public Interface

**Entry point:** The maintainer updates documentation, skills, or scripts and wants one public interface to teach and preserve.
**First touchpoint:** The maintainer adds or updates a subcommand in the common CLI instead of exposing another standalone script as the primary surface.
**Key moment:** Documentation, agent instructions, and deterministic implementation all align on the same command contract.
**Exit state:** Maintainers can evolve internals while keeping the public invocation model stable and repo-local.
**Pain points to design around:** Duplication across wrappers, drift between help text and docs, and unclear rules for when direct script invocation is still acceptable.

---

## Information Architecture

The product structure should shift from “many standalone scripts” to “one command with grouped lifecycle capabilities.” The CLI should be shallow enough for agents to scan quickly, with lifecycle verbs exposed as top-level subcommands rather than hidden in deep nesting.

### Site/App Map

```text
python {cicadas-dir}/scripts/cicadas.py
├── help
├── init
├── status
├── check
├── kickoff
├── branch
├── create-lifecycle
├── open-pr
├── signal
├── archive
├── update-index
├── prune
├── abort
├── history
├── validate-skill
├── skill-publish
├── emit-event
├── get-events
├── review
├── synthesize
├── tokens
├── register-existing
└── unarchive
```

### Navigation Model

**Primary nav:** command-line subcommands from a single entrypoint
**Secondary nav:** subcommand-specific help via `--help`
**Key entry points:** top-level `--help`, direct subcommand invocation, documentation snippets that teach the common command shape

---

## Key User Flows

### Flow 1: Discover a Capability and Run It

1. The agent invokes the common Cicadas command with `--help`.
2. The CLI prints a concise summary of available lifecycle operations and how to inspect each one further.
3. The agent identifies the needed subcommand, for example `status` or `kickoff`.
4. The agent invokes that subcommand with `--help` if argument details are needed.
5. The agent runs the fully specified command.
6. The CLI delegates to the existing deterministic implementation and returns output and exit status.

**Alternate path A:** If the agent provides an unknown subcommand, the CLI shows a clear error and points back to top-level help.
**Alternate path B:** If the underlying command fails, the CLI preserves actionable stderr and exit code so the agent can recover.

---

### Flow 2: Follow Documentation Without Script-Level Knowledge

1. A maintainer or agent reads a Cicadas doc or skill instruction.
2. The doc references the common CLI entrypoint and a subcommand instead of a direct script path.
3. The user runs the documented command as written.
4. If they need more detail, they use subcommand help instead of opening implementation files.
5. The command succeeds, and the docs remain aligned with the public interface.

**Alternate path A:** If legacy docs are encountered, they should be interpreted as migration debt and updated to point at the common CLI.
**Alternate path B:** If compatibility shims remain, they should reinforce the new interface rather than compete with it.

---

## UI States

### Top-Level Help

| State | Trigger | What the User Sees |
|-------|---------|-------------------|
| **Empty** | Invoked with no args and no default action | Concise usage summary plus visible list of subcommands |
| **Loading** | Not applicable for normal help | Immediate output; no spinner state expected |
| **Populated** | `--help` requested | Command description, available subcommands, and how to inspect deeper help |
| **Error** | Parsing fails before dispatch | Unknown command or invalid arguments with usage hint |
| **Success** | Help shown correctly | Exit 0 and enough information to continue autonomously |
| **Disabled** | Command unavailable in current environment | Clear explanation that the subcommand is unsupported or not enabled |

### Subcommand Execution

| State | Trigger | What the User Sees |
|-------|---------|-------------------|
| **Empty** | Subcommand has no output on success | Clean exit with no extra noise beyond what the underlying behavior already returns |
| **Loading** | Long-running delegated operation | Existing progress or status output from the underlying implementation |
| **Populated** | Successful operation with output | The same meaningful lifecycle output users already rely on |
| **Error** | Underlying implementation fails | Actionable error details, preserved stderr, non-zero exit code |
| **Success** | Operation completes | Existing success output, ideally with next-step clarity when relevant |
| **Disabled** | Unsupported combination or missing prereq | Immediate explanatory error with recovery guidance |

### Documentation Snippet Experience

| State | Trigger | What the User Sees |
|-------|---------|-------------------|
| **Empty** | User lands on a command reference | A single canonical invocation pattern, not multiple competing options |
| **Loading** | Not applicable | Static markdown |
| **Populated** | Reading docs or skill instructions | CLI-based examples aligned with top-level and subcommand help |
| **Error** | Example is stale or invalid | Should be treated as documentation bug and corrected |
| **Success** | Example works as written | Confidence that docs match executable reality |
| **Disabled** | Command intentionally deferred | Explicit note that the operation is not yet exposed through the CLI |

---

## Copy & Tone

**Voice:** Direct, technical, compact, and agent-readable.

**Key principles:**
- Prefer verbs and nouns already used by Cicadas lifecycle terminology.
- Make errors actionable without being verbose or blaming the caller.
- Optimize help text for runtime scanning by agents, not marketing language.

**Critical copy samples:**

| Context | Copy |
|---------|------|
| Primary CTA | `Run 'python {cicadas-dir}/scripts/cicadas.py --help' to inspect available lifecycle commands.` |
| Empty state headline | `No subcommand provided.` |
| Primary error message | `Unknown subcommand '{name}'. Run 'python {cicadas-dir}/scripts/cicadas.py --help' to see available commands.` |
| Success confirmation | `Command completed successfully.` |
| Onboarding headline | `Cicadas CLI: one entrypoint for deterministic lifecycle operations.` |

---

## Visual Design Direction

**Style:** Terminal-native, utilitarian, command-reference-first
**Color palette:** Rely on standard terminal output and existing success/error conventions; do not require color for comprehension
**Typography:** Monospace, following terminal defaults
**Spacing & density:** Compact, scan-friendly, with clear grouping between usage, commands, and examples
**Existing design system:** Existing CLI conventions in the repo; no separate visual system introduced in MVP

**Mood reference:** Focused and legible, like a well-structured Unix tool help page tuned for autonomous agents

---

## UX Consistency Patterns

### Button Hierarchy
- **Primary action:** Not applicable in a CLI context; the primary action is explicit command invocation
- **Secondary action:** `--help` on the top-level command or any subcommand
- **Destructive action:** Commands that prune, archive, or otherwise change project state should continue to make consequences explicit in copy

### Feedback Patterns
- **Success:** Reuse current script success output and avoid adding celebratory noise
- **Error:** Preserve underlying error details and prepend minimal command-context hints only when needed
- **Warning:** Use concise warning text for deprecated or legacy invocation patterns
- **Info:** Use short help descriptions and examples close to the relevant command

### Form Patterns
- **Validation timing:** On invocation during argument parsing
- **Error placement:** Inline in terminal output immediately after the invalid command or argument context
- **Required fields:** Conveyed through usage and subcommand help

### Navigation Patterns
- **Active state:** The currently addressed capability is expressed by the chosen subcommand
- **Back navigation:** Return to top-level help by running the base command with `--help`

### Modal & Overlay Patterns
- **When to use modals:** Not applicable
- **Dismissal:** Not applicable

---

## Responsive & Accessibility

**Breakpoints:**

| Breakpoint | Width | Layout |
|-----------|-------|--------|
| Narrow terminal | < 80 cols | Keep summaries short and avoid wide tables in help output |
| Standard terminal | 80-120 cols | Default optimized layout |
| Wide terminal | > 120 cols | Same structure; extra width should improve readability, not change meaning |

**Accessibility standards:** CLI accessibility best practices; WCAG-style visual breakpoints are not directly applicable

**Key requirements:**
- Keyboard navigation: full, because the interface is terminal-command-based
- Screen reader support: required insofar as help and output remain plain-text, linear, and semantically simple
- Color contrast: do not rely on ANSI color alone to convey meaning
- Touch targets: not applicable
- Reduced motion: not applicable
