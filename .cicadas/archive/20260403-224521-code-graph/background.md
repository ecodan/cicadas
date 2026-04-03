# Code Graph Requirements

## Background

Traditional canon is strong at top-down orientation:

- what the product is
- how the architecture is organized
- what the major modules are
- what the high-level boundaries mean

That is necessary, but it is often insufficient for brownfield work in large repositories and mega-repos.

Real maintenance work often begins “inside-out” from:

- a failing test
- a symbol or class name
- an endpoint
- a UI component
- a config key
- a log or event name
- a module or package name

From there, the agent needs to traverse the codebase:

- who calls this
- where is this implemented
- what depends on it
- what tests cover it
- what packaging/runtime path turns it into shipped behavior
- what nearby areas usually change with it

A graph representation of the codebase can support that kind of traversal much better than prose-only canon.

## Problem To Be Solved

For large repositories and mega-repos, a top-down canon alone is not enough to support efficient brownfield work.

The core problems are:

- agents lose time routing from a local symptom to the owning area
- similar concerns may appear in multiple layers or product families
- package/module hierarchies do not always reveal operational relationships
- the “next best file to open” is often determined by graph neighbors, not by directory structure
- existing canon may explain the map but not support traversing it

The problem is not to replace canon. The problem is to augment canon with a code graph and graph-derived operational guidance.

## Goal

Create a code-graph capability that allows Cicadas to support inside-out traversal in large repos and mega-repos, and to use that graph to generate more operational canon.

The code graph should help answer:

- what area likely owns this symbol/file/test/endpoint
- what neighboring areas are most likely relevant
- what tests should be inspected first
- what packaging/runtime path matters
- what interfaces or modules are upstream/downstream

## Recommended Approach

### 1. Treat graph as a supplement to canon, not a replacement

The system should combine:

- canon for meaning, intent, boundaries, and judgments
- code graph for structure, traversal, and routing

Canon remains the human-readable explanation layer.
The graph becomes the navigation substrate.

### 2. Start with a simple stack

Recommended initial implementation stack:

- extractor: `Python`
- language parsing: `tree-sitter` for core repo languages
- structural parsing: XML/manifest parsing for build and package metadata
- graph storage: `Neo4j Community` for the initial experiment
- query surface: `Python CLI` using `Typer` and `Rich`

This is recommended because it is relatively quick to build, inspect, and iterate on.

The first goal is not platform perfection. The first goal is to test whether graph-backed routing improves brownfield task performance.

### 3. Start with a routing graph, not a full semantic graph

The initial graph should model only the relationships that are most useful for routing and local traversal.

Recommended initial node types:

- `Repo`
- `Area`
- `Module`
- `File`
- `Symbol`
- `Test`
- `BuildTarget`

Recommended initial edge types:

- `CONTAINS`
- `DEPENDS_ON`
- `IMPORTS`
- `DECLARES`
- `CALLS`
- `TESTED_BY`
- `PACKAGED_INTO`
- `IMPLEMENTS`

Do not attempt to model every possible semantic relationship in the first version.

### 4. Support graph-backed operational queries

The initial system should expose opinionated operations rather than raw graph exploration only.

Recommended operations:

- `find-owning-area(symbol|file|endpoint|test)`
- `find-adjacent-areas(area)`
- `find-first-tests(area|symbol|file)`
- `trace-callers(symbol)`
- `trace-implementations(interface|api)`
- `trace-runtime-path(symbol|module)`
- `trace-packaging-path(file|module)`
- `route-change(description|artifact)`

These can exist first as CLI commands, then later as Cicadas internal capabilities.

### 5. Use the graph to improve canon generation

The graph should not only be queried directly. It should also support better canon generation.

Graph-derived canon should include:

- likely entrypoints for an area
- most central files or symbols
- strongest neighboring areas
- likely tests
- likely packaging/runtime path
- likely API/interface boundaries
- common “start here” paths

Area docs should become partly graph-backed rather than purely narrative.

### 6. Limit early scope

For very large repos, do not index the entire codebase at full symbol depth initially.

Start with:

- high-value areas only
- a few languages only
- a few edge types only

Recommended first-slice criteria:

- high-churn areas
- routing hubs
- packaging/runtime hubs
- representative product/platform/infrastructure areas

This allows the experiment to prove value before the graph becomes expensive to maintain.

## Testing Approach

### 1. Build a benchmark corpus

Create a benchmark task set using real or representative brownfield tasks.

Task categories should include:

- bug fixes
- small feature edits
- endpoint/REST changes
- frontend/UI regressions
- permissions/workflow/configuration bugs
- packaging/runtime issues
- cross-layer changes

Each task should define a “gold” answer set:

- owning area
- likely neighboring areas
- first files worth reading
- first tests worth checking

### 2. Compare graph-assisted vs canon-only workflows

Run the benchmark in at least two modes:

- canon only
- canon plus graph CLI

Optional:

- graph only
- graph plus graph-derived area canon

### 3. Measure efficacy

Suggested metrics:

- top-1 owning-area accuracy
- top-3 owning-area accuracy
- time to first plausible owning area
- time to first correct file
- number of wrong-area starts
- number of files opened before reaching the correct area
- time to first relevant test
- human-rated usefulness

If measuring agent performance directly, also consider:

- token usage before correct routing
- tool-call count before correct routing
- branch factor of exploration

### 4. Define success criteria

The experiment should be considered promising if graph-assisted workflows materially improve routing and local traversal.

Example success thresholds:

- meaningful improvement in top-3 owner accuracy
- materially fewer wrong-area starts
- faster time to first useful file
- better first-test selection

Exact numeric thresholds can be calibrated later, but the evaluation must be explicit before implementation begins.

## Supporting Details

### Why a graph DB may be necessary

For mega-repos, the graph itself may be large enough that simple in-memory structures or ad hoc JSON files become difficult to query efficiently and inspect operationally.

A graph database is recommended because it supports:

- relationship-heavy traversal
- iterative query design
- ranking and neighborhood inspection
- exploratory analysis during development

This document recommends starting with Neo4j Community because it is easy to adopt locally and is sufficient for an MVP.

### Why a CLI is required

Even if the graph exists, agents need a stable and narrow interface for querying it.

A CLI is recommended because it:

- keeps graph access operational and scriptable
- makes it easy to benchmark graph queries
- avoids forcing agents to emit raw DB queries
- allows Cicadas to wrap graph operations in stable command semantics

The CLI should return ranked summaries, not raw graph dumps.

### Suggested CLI commands

Initial candidate commands:

- `graph area <path-or-symbol>`
- `graph neighbors <area>`
- `graph tests <path-or-symbol>`
- `graph trace <symbol>`
- `graph route "<task description>"`
- `graph package-path <file-or-module>`

### Suggested incremental rollout

#### Phase 1

Index:

- areas
- modules
- files
- build relationships
- imports
- heuristic test associations

This may already be useful for routing.

#### Phase 2

Add:

- symbol declarations
- call relationships
- interface/implementation relationships

#### Phase 3

Add repo-specific operational edges such as:

- packaged into plugin/webapp/runtime image
- endpoint to handler/service relationships
- feature-flag/config links
- curated area adjacency

### Non-goals

This initiative should not attempt:

- a perfect semantic graph for the entire repo on day one
- support for every language before proving value
- replacing canon entirely
- building a distributed or highly optimized production graph platform first

## Initiative Guidance

When Cicadas creates an initiative from this document, the initiative should address:

- graph-backed navigation goals
- MVP schema design
- storage and CLI approach
- ingestion/extraction approach
- limited-scope rollout strategy
- benchmark-driven evaluation
- integration points with canon generation and area docs

Deliverables should include:

- MVP graph schema
- extractor design
- CLI command set
- benchmark corpus format
- evaluation harness
- integration plan for graph-derived canon improvements

## Design Principle

In large repos and mega-repos:

- canon explains the map
- the code graph helps traverse the terrain

The best result is not “graph instead of canon.”
The best result is “canon plus graph-backed routing and area guidance.”
