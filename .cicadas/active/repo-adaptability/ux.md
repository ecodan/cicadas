---
summary: "Design the adaptive-canon experience as a CLI-first workflow that helps Builders and agents trust repo classification, start from compact orientation, and then load the smallest useful seeded slice pack for the next local change."
phase: "ux"
when_to_load:
  - "When designing or reviewing journeys, flows, states, copy, and interaction constraints."
  - "When implementation questions depend on experience details rather than product goals alone."
depends_on:
  - "prd.md"
modules:
  - "src/cicadas/emergence"
  - "src/cicadas/templates"
  - "src/cicadas/scripts"
  - ".cicadas/canon"
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
next_section: "Builder review"
---

# UX Design: Repo Adaptability

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

**Primary goal:** Make adaptive canon feel trustworthy and action-oriented so a Builder or agent quickly understands why Cicadas chose a repo mode, what canon shape follows from that choice, and where to go next for a real brownfield task.

**Design constraints:**
- Primary surface is CLI-first workflow output plus generated markdown canon artifacts.
- There is no existing dedicated UX canon for Cicadas, so this initiative should extend current terminal-and-filesystem patterns rather than inventing a GUI mental model.
- The experience must work for brownfield discovery where evidence is incomplete, classification may be ambiguous, and the Builder may need to challenge or refine the result.
- The canon should stay human-centric enough to remain useful even if a later graph-backed routing layer takes over mechanical traversal.

**Skip condition:** N/A — This initiative has workflow and artifact UX impact even though it is not a graphical UI feature.

---

## User Journeys & Touchpoints

### Builder on a Large Repo — Trust the Classification

**Entry point:** Builder starts bootstrap on a brownfield repo and wants confidence that Cicadas understands the repo’s operational shape.
**First touchpoint:** CLI or generated bootstrap summary reports the selected scale, evidence, and expected canon outputs.
**Key moment:** The Builder sees a classification explanation that sounds grounded in repo structure and maintenance reality, not just vague size language.
**Exit state:** The Builder can accept the mode, understand what artifacts will be created, and use the first seeded slice pack as the next step.
**Pain points to design around:** Opaque heuristics, overconfident classification, too much prose before actionable next steps, and uncertainty about what to read first.

---

### Implementation Agent on a Mega Repo — Start Safely from Symptoms

**Entry point:** Agent is asked to fix or change something from the inside out, starting from a symptom, endpoint, package, or failing test.
**First touchpoint:** Compact canon summary points the agent to the most likely slice pack instead of a broad narrative overview.
**Key moment:** The agent can identify a plausible owning slice and nearby risk boundaries before opening many files.
**Exit state:** The agent has a safe first-hop path through the canon and understands which artifacts are authoritative for routing versus judgment.
**Pain points to design around:** Wrong-area starts, duplicated routing advice across docs, unclear “do not touch casually” warnings, and confusion between canon guidance and future graph-derived navigation.

---

### Cicadas Maintainer — Keep the System Evolvable

**Entry point:** Maintainer updates templates, bootstrap guidance, or synthesis behavior after observing real-world maintenance work.
**First touchpoint:** The canon model and workflow docs clearly separate orientation, routing, area guidance, and parking-lot graph-dependent ideas.
**Key moment:** The maintainer can evolve the canon structure without feeling forced to encode every machine-navigation detail in prose.
**Exit state:** The maintainer has a clean seam between durable human-centric canon and potential future graph-backed traversal.
**Pain points to design around:** Scope creep, duplicated semantics across artifacts, inability to tell which parts are MVP versus dependent follow-on work.

---

## Information Architecture

### Site/App Map

```text
Adaptive Bootstrap Output
├── Classification Summary
│   ├── Selected mode
│   ├── Evidence
│   └── Expected canon shape
├── Orientation Canon
│   ├── product-overview.md
│   └── tech-overview.md
├── Routing Canon
├── Slice Canon
│   └── slices/{slice-name}/
│       ├── summary.md
│       ├── boundaries.md
│       ├── architecture.md
│       ├── invariants.md
│       └── change-guide.md
└── Compact Reload Artifacts
    ├── canon summary
    └── slice-level summaries
```

### Navigation Model

**Primary nav:** Command output plus file-path handoff to the next best artifact  
**Secondary nav:** Cross-links inside generated markdown artifacts, especially from orientation to slices and between neighboring slices  
**Key entry points:** Bootstrap result summary, `canon/summary.md`, `canon/repo-context.md`, and the seeded slice docs surfaced for the current task type

---

## Key User Flows

### Flow 1: Bootstrap a Repo and Review Classification (Happy Path)

1. Builder starts bootstrap or canon-generation flow.
2. Cicadas analyzes repo structure and operational signals.
3. Cicadas emits a classification summary with selected mode, evidence, and expected canon shape.
4. Builder reviews the explanation and sees which artifacts will be generated.
5. Cicadas generates the mode-appropriate canon set.
6. Builder is pointed to the highest-value next artifact for future brownfield work.

**Alternate path A:** If the evidence is mixed, Cicadas marks the case as ambiguous and frames the decision around which canon shape best supports likely future maintenance tasks.
**Alternate path B:** If graph-backed routing does not exist, Cicadas keeps routing guidance in canon and clearly avoids promising graph-derived traversal features.

---

### Flow 2: Route an Inside-Out Brownfield Change

1. Builder or agent starts from a symptom, failing test, endpoint, module, or package.
2. They open the compact canon summary or bootstrap handoff artifact.
3. Cicadas points them to the most likely seeded slice before broad narrative docs when routing risk is high.
4. They follow the recommended first slice and inspect neighboring slices, risky boundaries, and likely tests.
5. They arrive at a plausible starting slice with a short list of first files and first checks.

**Alternate path A:** If no graph-backed layer exists, seeded slice packs carry more of the routing burden.
**Alternate path B:** If graph-backed routing exists later, canon redirects mechanically derivable adjacency questions toward the graph while keeping human judgment in the docs.

---

### Flow 3: Decide What Belongs in Canon vs Parking Lot

1. Maintainer proposes adding richer routing or dependency-oriented detail.
2. They check whether the detail is durable human guidance or future machine-navigation logic.
3. If it is human judgment, it is added to canon artifacts such as orientation docs or slice packs.
4. If it is mainly mechanical traversal and the graph project is not available, it is recorded as parking-lot follow-on scope rather than bloating MVP canon.
5. If the graph project later lands, the navigation detail moves to that layer and canon stays concise and judgment-rich.

---

## UI States

### Bootstrap Classification Experience

| State | Trigger | What the User Sees |
|-------|---------|-------------------|
| **Empty** | Bootstrap has not yet classified the repo | A short explanation that adaptive canon begins with repo-scale classification and will report evidence before synthesis. |
| **Loading** | Discovery and heuristic evaluation are in progress | Progress-oriented messaging that classification is inspecting repo structure, ownership shape, and routing complexity. |
| **Populated** | Classification completed successfully | Selected mode, key evidence bullets, expected canon artifacts, and the recommended first artifact to read next. |
| **Error** | Discovery or classification fails | Clear failure message, what signal could not be collected, and the safest fallback path. |
| **Success** | Canon artifacts were generated | Confirmation plus a prioritized handoff such as “Start with the seeded slice pack for your likely change area.” |
| **Disabled** | A graph-backed feature is referenced before it exists | An explicit note that graph-assisted routing is a follow-on capability and that the current canon is using the non-graph fallback. |

### Routing Artifact Experience

| State | Trigger | What the User Sees |
|-------|---------|-------------------|
| **Empty** | No routing artifact is needed for `normal-repo` | A brief explanation that the repo is small enough for orientation plus module docs. |
| **Loading** | Agent is deciding which artifact to surface | A lightweight handoff message naming the candidate artifact and why it is being chosen. |
| **Populated** | Slice artifacts exist | A concise artifact index showing where to start, what to inspect second, and which neighboring slices may matter. |
| **Error** | Expected slice artifact is missing or stale | A warning that the artifact is unavailable and a fallback path through orientation or neighboring slices. |
| **Success** | User confirms the starting slice was useful | Encouragement to continue with the recommended slice docs, tests, or neighboring slice references. |
| **Disabled** | Parked graph-dependent feature is requested | A reminder that this navigation depth is intentionally parked pending the graph follow-on. |

---

## Copy & Tone

**Voice:** Direct, technical, and calm. The system should sound evidence-based and helpful, never mystical or overconfident.

**Key principles:**
- Explain classification in concrete repo-language, not abstract scoring jargon.
- Always pair decisions with the next recommended action or artifact.
- Distinguish clearly between current canon capabilities and graph-dependent future capabilities.

**Critical copy samples:**

| Context | Copy |
|---------|------|
| Primary CTA | `Review classification and generate canon` |
| Empty state headline | `Adaptive canon starts by classifying how this repo should be understood.` |
| Primary error message | `Cicadas couldn’t classify this repo confidently from the available signals. Review the evidence and choose the canon shape that best fits expected maintenance work.` |
| Success confirmation | `Canon generated for large-repo mode. Start with the most likely seeded slice for brownfield routing.` |
| Onboarding headline | `Choose the canon shape that helps future changes start in the right place.` |

---

## Visual Design Direction

**Style:** Terminal-first, data-dense, and evidence-forward  
**Color palette:** Plain text with semantic emphasis if the host supports it; warnings and disabled graph-dependent notes should be visually distinct from normal guidance  
**Typography:** Existing terminal and markdown conventions, with monospace treatment for paths, repo modes, and artifact names  
**Spacing & density:** Compact but clearly sectioned so Builders can scan classification evidence and next steps quickly  
**Existing design system:** Extend current Cicadas CLI and markdown artifact conventions

**Mood reference:** A careful technical copilot that shows its reasoning, points to the next right file, and avoids sounding like a black box.

---

## UX Consistency Patterns

### Button Hierarchy
- **Primary action:** The single “what to read or do next” recommendation after classification or artifact generation.
- **Secondary action:** Supporting artifact options such as orientation docs, neighboring areas, or migration guidance.
- **Destructive action:** Not applicable in this UX slice beyond normal confirmation patterns elsewhere in Cicadas.

### Feedback Patterns
- **Success:** Report the chosen mode, why it was chosen, and the first recommended artifact.
- **Error:** Explain what failed, what evidence is missing, and the safest fallback route.
- **Warning:** Use warnings for ambiguous classification, risky boundaries, and graph-dependent ideas that are parked.
- **Info:** Use short context lines to explain why a particular canon layer is being shown first.

### Form Patterns
- **Validation timing:** On review of classification output rather than per-field input, since this workflow is primarily generated output.
- **Error placement:** Inline with the failed decision or missing artifact, followed by a fallback recommendation.
- **Required fields:** Not applicable as a primary concern for this CLI-and-artifact flow.

### Navigation Patterns
- **Active state:** The current recommended artifact is named explicitly, with file paths and why it is first.
- **Back navigation:** Users can step back from area docs to routing guidance and from routing guidance to orientation docs via explicit cross-links and handoff text.

### Modal & Overlay Patterns
- **When to use modals:** Not applicable in the current CLI-first workflow.
- **Dismissal:** Not applicable; transient messaging should simply return to the shell prompt or artifact list.

---

## Responsive & Accessibility

**Breakpoints:**

| Breakpoint | Width | Layout |
|-----------|-------|--------|
| Terminal / narrow viewport | < 80 cols | Prefer short paragraphs, tight bullet lists, and shallow tables where possible |
| Standard desktop terminal | 80-140 cols | Full markdown sections, compact tables, and file-path handoffs |
| Wide desktop terminal | > 140 cols | Same content model; avoid relying on width for meaning |

**Accessibility standards:** N/A as a graphical UI target, but workflow output should still follow accessible writing practices.

**Key requirements:**
- Keyboard navigation: full, by virtue of terminal and file-based workflow
- Screen reader support: required for markdown artifacts and readable CLI output
- Color contrast: do not rely on color alone to distinguish warnings or parked scope
- Touch targets: N/A
- Reduced motion: N/A
