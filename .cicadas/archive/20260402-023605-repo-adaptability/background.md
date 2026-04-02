# Canon Adaptability Requirements

## Background

Cicadas bootstrap and canon generation were originally designed around a repo shape where one agent can discover the codebase, synthesize a small set of durable canon artifacts, and use those artifacts to drive future feature work. That model works well for normal-sized repositories where the main problem is understanding product intent and top-level architecture.

It does not scale cleanly to very large repositories and mega-repos. In those environments:

- the hardest problem is often not understanding the product at a high level
- the hardest problem is routing a brownfield task to the correct area quickly and safely
- multiple architectural layers may overlap for one user-visible behavior
- similar concepts may exist in multiple product, platform, infrastructure, packaging, or plugin areas
- a single uniform canon depth produces documents that are too broad to be operationally useful

This means Cicadas needs an adaptive canon model that changes with repository scale.

## Problem To Be Solved

Cicadas currently risks generating canon that is:

- too shallow for brownfield work in large repos
- too uniform across areas with very different operational importance
- too narrative when a reference or routing system is needed
- too product-summary-oriented when real work begins from a symptom, failing test, endpoint, symbol, or module

The problem is not simply “make canon more detailed.” The problem is to generate the right canon shape for the repo class.

Cicadas must determine whether the repo needs:

- a traditional canon
- a layered canon
- or a routing-first operational canon

and then bootstrap accordingly.

## Goals

The adaptive canon system must ensure that generated canon is useful for the most common future tasks in that codebase, especially:

- brownfield feature changes
- bug fixes
- local refactors
- routing a change to the correct area
- identifying nearby modules, tests, and packaging/runtime paths

Canon must be judged by whether it helps an agent act safely, not just whether it reads well.

## Recommended Approach

### 1. Add explicit repo-scale modes

Cicadas must support three canon modes:

- `normal-repo`
- `large-repo`
- `mega-repo`

Bootstrap must classify the repo into one of these modes before canon synthesis begins.

### 2. Add scale-detection heuristics

Scale detection must consider:

- number of top-level modules/packages
- number of second- and third-layer aggregators
- number of meaningful change-owning areas
- diversity of build, test, package, and runtime paths
- presence of multiple architectural layers
- presence of multiple product families or plugin ecosystems
- whether most brownfield work requires routing before coding
- whether one linear canon could plausibly be read front-to-back and remain useful

Scale detection must not rely on line count alone.

Bootstrap must record:

- the selected scale
- the evidence for that choice
- the expected canon shape for that scale

### 3. Define canon by scale

#### Normal repo canon

Use when:

- the repo has a small number of meaningful subsystems
- one canon set can plausibly be read front-to-back
- most changes can be localized after reading product and tech overviews plus a modest set of module docs

Required outputs:

- `product-overview.md`
- `tech-overview.md`
- optional `ux-overview.md` if needed
- `modules/*.md`
- compact canon summary

Normal-repo canon should stay mostly narrative and explanatory.

#### Large repo canon

Use when:

- routing matters, but a curated set of area docs can still cover most work
- multiple architectural layers exist
- the repo is too large for uniform module snapshots to be enough
- the repo is still small enough that a bounded set of area canons can cover common work

Required outputs:

- `product-overview.md`
- `tech-overview.md`
- `routing-guide.md`
- `areas/*.md`
- optional `modules/*.md` for stable broad structures
- compact canon summary

Large-repo canon must be layered:

- top-level orientation
- routing guidance
- operational area docs

#### Mega-repo canon

Use when:

- the hardest part of brownfield work is finding the owning area
- similar concepts appear in multiple layers or product families
- packaging, runtime, and testing paths vary materially by area
- there are many meaningful change-owning areas
- a linear canon would be too shallow to be operationally useful

Required outputs:

- `product-overview.md`
- `tech-overview.md`
- `routing-guide.md`
- `area-map.md`
- `areas/*.md`
- `playbooks/*.md`
- compact reload artifacts for area-level work

Mega-repo canon must be routing-first and operational, not just descriptive.

### 4. Distinguish canon layers

Cicadas must explicitly distinguish:

- `orientation canon`
- `routing canon`
- `area canon`
- `change-playbook canon`

#### Orientation canon

Explains:

- what the product is
- how the repo is shaped
- major product families
- major architectural layers
- major build, test, package, and runtime paths

#### Routing canon

Explains:

- if the change is about X, start in Y
- nearby areas likely to be involved
- common wrong turns
- packaging, runtime, and test path implications

#### Area canon

Explains:

- when to come here
- when not to come here
- likely entrypoints
- key interfaces/models
- common neighbors
- likely tests
- common change patterns
- local traps

#### Change playbooks

Explain common brownfield tasks such as:

- REST contract change
- frontend packaging regression
- board behavior bug
- workflow/configuration bug
- permission/authz bug
- service-management portal/request issue
- webapp/runtime assembly issue

Each playbook must include:

- likely owning areas
- likely neighboring areas
- first files to inspect
- first tests to run
- common failure modes

### 5. Use depth selectively

Cicadas must not try to document every area at equal depth in large or mega repos.

Bootstrap must choose where to go deep using signals such as:

- likely churn
- architectural centrality
- test richness
- packaging/runtime centrality
- role as a routing hub
- likelihood of future brownfield changes

Bootstrap must explicitly mark:

- deep-canoned areas
- shallow-canoned areas
- deferred areas

### 6. Add a “brownfield usefulness” acceptance bar

Canon must be considered useful only if an agent can use it to answer:

- where should I start for this exact change?
- what should I read second?
- what nearby areas should I inspect?
- what should I not touch casually?
- what tests should I run first?
- what packaging/runtime path matters?

If the canon cannot answer those questions for the repo’s typical work, it is not sufficient.

## Testing Approach

### 1. Create benchmark task sets by repo scale

For each scale class, create a benchmark corpus of real or representative tasks:

- bug fixes
- small brownfield feature edits
- endpoint/contract changes
- frontend regressions
- permission/workflow/configuration changes
- build/package/runtime issues

Each benchmark task should include expected outputs such as:

- likely owning area
- likely neighboring areas
- first files worth opening
- first tests worth inspecting

### 2. Compare canon outcomes by mode

Measure effectiveness of generated canon against benchmark tasks.

Suggested metrics:

- top-1 owning-area accuracy
- top-3 owning-area accuracy
- time to first plausible area
- time to first useful file
- number of wrong-area starts
- number of files opened before correct owner
- time to first relevant test
- human usefulness rating

### 3. Validate by real maintenance work

Canon quality should improve through use on actual initiatives and bug fixes.

Cicadas should support “validated by recent change” style updates where area docs and playbooks get refined from successful real work.

## Supporting Details

### Suggested artifact structure by mode

#### Normal repo

- `canon/product-overview.md`
- `canon/tech-overview.md`
- `canon/modules/*.md`

#### Large repo

- `canon/product-overview.md`
- `canon/tech-overview.md`
- `canon/routing-guide.md`
- `canon/areas/*.md`
- optional `canon/modules/*.md`

#### Mega repo

- `canon/product-overview.md`
- `canon/tech-overview.md`
- `canon/routing-guide.md`
- `canon/area-map.md`
- `canon/areas/*.md`
- `canon/playbooks/*.md`
- compact area summaries for reload

### Non-goals

This work does not require:

- uniform documentation of every leaf module
- full API/schema extraction in the first pass
- exact human ownership metadata for every subtree
- full runtime validation when local environment access is blocked

### Design principle

For small repos, canon is primarily a narrative.

For large repos, canon is primarily a layered reference.

For mega repos, canon is primarily a routing and execution aid.

## Initiative Guidance

When Cicadas creates an initiative from this document, the initiative should address:

- repo-scale detection
- canon mode selection
- canon artifact design by scale
- bootstrap flow changes by scale
- brownfield usefulness evaluation
- update strategy for iterative deepening over time

Deliverables should include:

- updated bootstrap guidance
- updated canon generation guidance
- new templates as needed
- explicit evaluation criteria
- migration guidance from current canon behavior to adaptive canon behavior
