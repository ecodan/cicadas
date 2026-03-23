
# Tweaklet: ai-clarification

## Intent
The phrase "building on ai" is not common and may be unclear to builders. This tweak replaces it with a more descriptive and professional phrase: "will this feature or change be powered by LLMs and may require ML evals to ensure quality?"

## Proposed Change
Update the following files to replace "building on ai" (and its variations like "Building on AI") with the new phrase, while keeping the internal configuration key `building_on_ai` intact for compatibility:

- `src/cicadas/SKILL.md`
- `src/cicadas/README.md`
- `src/cicadas/emergence/skill-create.md`
- `src/cicadas/emergence/start-flow.md`
- `src/cicadas/emergence/approach.md`
- `src/cicadas/emergence/eval-spec.md`
- `src/cicadas/emergence/bug-fix.md`
- `src/cicadas/emergence/tweak.md`
- `src/cicadas/emergence/clarify.md`

## Tasks
- [x] Update documentation and instruction modules <!-- id: 10 -->
- [x] Verify functionality (ensure start-flow still works) <!-- id: 11 -->
- [x] Significance Check: Does this warrant a Canon update? <!-- id: 12 -->
