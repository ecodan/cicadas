---
summary: "Code Graph extends Cicadas' terminal-first experience with optional graph commands that help builders and agents route work from a symptom or changed symbol to the right area, neighbors, callers, and tests. The UX prioritizes explicit availability, compact ranked summaries, clear fallback guidance when the graph is absent or partial, and low-friction observability for whether graph use is helping."
phase: "ux"
when_to_load:
  - "When designing or reviewing graph command flows, fallback messaging, and graph-related interaction states."
  - "When implementation questions depend on how graph-backed routing should feel to builders and agents in the terminal."
depends_on:
  - "prd.md"
modules:
  - "src/cicadas/scripts"
  - "src/cicadas/emergence"
  - ".cicadas/graph"
index:
  design_goals: "## Design Goals & Constraints"
  journeys: "## User Journeys & Touchpoints"
  information_architecture: "## Information Architecture"
  key_flows: "## Key User Flows"
  ui_states: "## UI States"
  copy_tone: "## Copy & Tone"
  visual_design: "## Visual Design Direction"
  consistency: "## UX Consistency Patterns"
  accessibility: "## Responsive & Accessibility"
next_section: "Responsive & Accessibility"
---

# UX Design: Code Graph

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

**Primary goal:** Make graph-backed routing feel like a natural extension of Cicadas' existing terminal workflow: explicit, trustworthy, compact, and helpful when the user starts from a symptom rather than from top-down repo knowledge.

**Design constraints:**
- Terminal / CLI-first interaction only; no new graphical UI is required for v1.
- Must fit existing Cicadas command and script patterns rather than inventing a separate graph console.
- Graph support is optional, so every graph-facing interaction must explain absence, staleness, or partial coverage cleanly.
- Outputs must be concise enough for agent consumption while still including evidence and confidence clues.

**Skip condition:** Not applicable. This initiative changes the user-facing CLI experience directly even though the surface is terminal-first.

---

## User Journeys & Touchpoints

### Builder in a Mega-Repo — Route Before Planning

**Entry point:** A failing test name, a changed symbol, or a vague bug report arrives before the Builder knows the right owning area.  
**First touchpoint:** `cicadas.py graph area ...` or `cicadas.py graph signature-impact ...` from the repo root.  
**Key moment:** The Builder sees a compact ranked result that identifies the likely owning slice, adjacent areas, and first tests worth checking.  
**Exit state:** They move into Clarify with a better-scoped understanding of the work and can reference graph-backed routing in the draft spec.  
**Pain points to design around:** Hidden graph absence, noisy result lists, ambiguity about whether results are structural-only or semantically grounded.

---

### Implementation Agent — Contain Blast Radius Quickly

**Entry point:** The agent is on a branch with a changed method signature or a failing test and needs to understand likely fallout fast.  
**First touchpoint:** `cicadas.py graph callers ...`, `graph tests ...`, or `graph signature-impact ...`.  
**Key moment:** The agent gets a ranked working set instead of a raw dump and understands what to open first, what nearby areas to inspect second, and which tests likely matter.  
**Exit state:** The agent starts implementation with a smaller, more confident working set and fewer wrong-area file opens.  
**Pain points to design around:** Overly verbose outputs, false sense of completeness, and unclear distinction between graph findings and canon meaning.

---

### Maintainer — Check If Graph Use Is Worth It

**Entry point:** After several graph-assisted workflows, the maintainer wants to see whether the graph is being used and where it helps.  
**First touchpoint:** `cicadas.py graph usage` with optional initiative or time filters.  
**Key moment:** The summary shows which graph commands are used, how long they take end-to-end, and whether predicted areas/tests/callers overlap with the work actually performed.  
**Exit state:** The maintainer can decide whether graph support is earning its complexity and which commands deserve deeper investment.  
**Pain points to design around:** Reports that are too raw, lack initiative/work-type filters, or confuse usage with proven value.

---

## Information Architecture

### Site/App Map

```
Cicadas CLI
├── Core lifecycle
│   ├── kickoff
│   ├── branch
│   ├── status
│   └── check
├── Repo orientation
│   ├── scan-repo
│   ├── canon/summary.md
│   └── canon/repo-context.md
└── Graph (optional)
    ├── build
    ├── status
    ├── area
    ├── neighbors
    ├── tests
    ├── callers
    ├── callees
    ├── signature-impact
    ├── route
    └── usage
```

### Navigation Model

**Primary nav:** CLI subcommands under `cicadas.py graph`  
**Secondary nav:** Existing repo-context, routing guides, and slice docs as fallback or interpretation layers  
**Key entry points:** symptom-led work during Clarify, branch-start routing, implementation blast-radius analysis, and post-hoc usage review

---

## Key User Flows

### Flow 1: Build Graph and Confirm Availability

1. User runs `cicadas.py graph build`.
2. Cicadas scans the repo, detects available analyzers, and writes graph artifacts under `.cicadas/graph/`.
3. Build output summarizes indexed languages, partial coverage, and where graph data was written.
4. User runs `cicadas.py graph status`.
5. Cicadas reports freshness, build ID, schema version, indexed languages, and readiness for graph-backed queries.

**Alternate path A:** If optional analyzers are missing, build still succeeds with partial coverage and explains what was unavailable.  
**Alternate path B:** If build fails, Cicadas reports the failure clearly and reminds the user that normal non-graph Cicadas workflows remain available.

---

### Flow 2: Route from a Symptom During Clarify

1. Builder starts from a failing test or symbol.
2. They run `cicadas.py graph area <artifact>` or `cicadas.py graph signature-impact <symbol>`.
3. Cicadas returns a ranked result with owning area, neighbors, likely tests, and coverage/freshness context.
4. Builder uses that result to scope the PRD or buglet and decide whether the work is isolated or cross-area.
5. If graph is missing, the command explains how to fall back to `repo-context.md`, routing guides, or slice docs.

**Alternate path A:** If results are partial because language support is structural-only, the output says so explicitly.  
**Alternate path B:** If multiple plausible areas exist, results show ranked candidates instead of a fake certainty.

---

### Flow 3: Analyze Signature Blast Radius During Implementation

1. Agent changes or inspects a symbol signature.
2. They run `cicadas.py graph signature-impact <symbol>`.
3. Cicadas returns likely callers, nearby tests, adjacent areas, and impacted files/packages.
4. Agent uses the result to choose files to inspect, tests to run, and whether to signal neighboring partitions.
5. Query usage is logged with the initiative/work type and end-to-end operation time.

**Alternate path A:** If the symbol cannot be resolved semantically, Cicadas falls back to structural hints and says the result is limited.  
**Alternate path B:** If the graph is stale, the command warns and suggests rebuilding before trusting the result.

---

### Flow 4: Review Whether Graph Use Helped

1. Maintainer runs `cicadas.py graph usage --initiative code-graph`.
2. Cicadas summarizes command frequency, end-to-end timings, coverage, and usefulness signals.
3. If requested, an HTML or structured report is generated for easier inspection.
4. Maintainer uses the report to decide whether graph commands are earning more investment.

---

## UI States

### Graph Query Command

| State | Trigger | What the User Sees |
|-------|---------|-------------------|
| **Empty** | No matching area/caller/test found | A clear “no results” summary plus the input target and suggested next commands or fallback artifacts |
| **Loading** | Query or build in progress | Short progress messages suitable for terminal use; no noisy spinner requirement |
| **Populated** | Ranked results returned | Compact summary, top candidates, coverage/freshness context, and why each candidate was included |
| **Error** | Invalid target, unreadable graph, or command failure | Explicit error reason plus recovery action such as rebuild or fallback to canon routing docs |
| **Success** | Build or usage report generated | Confirmation with artifact path, build ID, or report location |
| **Disabled** | Graph not initialized | Message that graph support is optional, how to build it, and what non-graph artifact to use instead |

### Graph Usage Report

| State | Trigger | What the User Sees |
|-------|---------|-------------------|
| **Empty** | No graph usage logged yet | “No graph usage recorded yet” plus instructions to run graph commands or build the graph |
| **Loading** | Report generation in progress | Short summary that the log is being aggregated |
| **Populated** | Usage entries exist | Tabular or structured summary by query kind, initiative/work type, timing, and usefulness signals |
| **Error** | Corrupt or unreadable usage log | Warning that the log could not be parsed, plus the file path and safe remediation advice |
| **Success** | HTML report written | Path to the generated report and filter scope used |
| **Disabled** | Graph artifacts absent | Optional-feature message and no-op guidance |

---

## Copy & Tone

**Voice:** Direct, technical, and calm. Graph output should feel trustworthy and operational rather than chatty.

**Key principles:**
- Never imply semantic completeness when the system only has structural evidence.
- Error and absence messaging must tell the user what to do next.
- Use routing language consistently: `owning area`, `neighbors`, `likely tests`, `coverage`, `freshness`.

**Critical copy samples:**

| Context | Copy |
|---------|------|
| Primary CTA | `Build local graph` |
| Empty state headline | `No graph results found for this target.` |
| Primary error message | `Graph support is not initialized for this repo. Run \`cicadas.py graph build\` or use \`canon/repo-context.md\`.` |
| Success confirmation | `Graph build complete. Queries are ready against build {build_id}.` |
| Onboarding headline | `Use graph commands when you need to route from a symptom to the right code.` |

---

## Visual Design Direction

**Style:** Terminal / data-dense / evidence-forward  
**Color palette:** Follow existing terminal output conventions with semantic emphasis for warnings, errors, freshness, and success states  
**Typography:** Monospace only  
**Spacing & density:** Compact, optimized for scanning ranked results and usage tables  
**Existing design system:** Extend Cicadas' current CLI interaction style rather than introducing a new visual language

**Mood reference:** A focused operational CLI that feels like a precise routing assistant, not an exploratory REPL.

---

## UX Consistency Patterns

### Button Hierarchy
- **Primary action:** Not applicable for CLI, but the equivalent primary action is the recommended next command in help or absence states
- **Secondary action:** Additional graph commands or fallback artifact suggestions
- **Destructive action:** None in normal query flow; rebuild or forced rebuild commands should call out overwriting derived graph state explicitly

### Feedback Patterns
- **Success:** One concise confirmation line plus the most important identifier such as build ID or output path
- **Error:** First line states the failure plainly; next line gives the specific next action
- **Warning:** Use warnings for stale graph data, partial language coverage, or heuristic-only results
- **Info:** Include ranked evidence and fallback artifacts when useful

### Form Patterns
- **Validation timing:** On submit
- **Error placement:** Immediate terminal output
- **Required fields:** Command target is required; optional filters or views follow current CLI norms

### Navigation Patterns
- **Active state:** Each command begins by stating the target or scope it is analyzing
- **Back navigation:** No special back model; use adjacent commands and fallback artifact references instead

### Modal & Overlay Patterns
- **When to use modals:** Not applicable
- **Dismissal:** Not applicable

---

## Responsive & Accessibility

**Breakpoints:**

| Breakpoint | Width | Layout |
|-----------|-------|--------|
| Narrow terminal | < 100 cols | One result per block with wrapped evidence lines |
| Standard terminal | 100–160 cols | Compact ranked lists or tables |
| Wide terminal | > 160 cols | Denser tables for usage reports and status summaries |

**Accessibility standards:** Terminal accessibility best practices; WCAG-style color contrast expectations for ANSI color use where present

**Key requirements:**
- Keyboard navigation: full by virtue of CLI interaction
- Screen reader support: required for output that remains understandable without color alone
- Color contrast: warnings and statuses must not rely on color as the sole cue
- Touch targets: N/A
- Reduced motion: no motion dependence or spinner-only progress feedback
