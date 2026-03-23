# Tweaklet: initiative-scope-gate

## Intent
Add a scope gate early in the initiative Clarify flow that detects when proposed work fits tweak criteria (< 100 LOC, no new dependencies, no architectural impact) and offers the Builder the option to switch to the lightweight tweak path before any heavy documentation begins.

## Proposed Change
In `src/cicadas/emergence/clarify.md`, insert a new step between the Standard Start Flow (step 0) and Ingest (step 1):

**New step — "Scope Gate":**
> Before proceeding with the full initiative spec process, briefly assess whether the Builder's described work fits the tweak criteria: fewer than ~100 lines of code, no new dependencies, and no architectural impact. If it does, ask: *"Based on what you've described, this sounds like it could be handled as a lightweight tweak rather than a full initiative — which would mean less documentation and a faster path to implementation. Would you like to switch to the tweak path instead? (yes / no)"*. If the Builder says yes, switch to the tweak flow (`tweak.md`). If no, continue with the full initiative.

No other files need to change.

## Tasks
- [x] Add the Scope Gate step to `clarify.md` between step 0 and step 1 <!-- id: 10 -->
- [x] Verify the instruction reads clearly and fits the existing flow <!-- id: 11 -->
- [x] Significance Check: Does this warrant a Canon update? No — behavioral instruction only, no architectural impact. <!-- id: 12 -->
