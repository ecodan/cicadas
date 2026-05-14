---
name: your-skill-name
description: >
  Use when the user asks about ... Describe the trigger condition precisely —
  this text is used by the agent to decide whether to invoke the skill.
  Maximum 1024 characters. Be specific about trigger phrases and use cases.
license: Apache-2.0
# Optional fields:
# argument-hint: "[command] [target]"
# allowed-tools: Read, Write, Edit, Shell, Glob, Grep
---

> Deprecated: This scaffold is retained for compatibility with the legacy
> Cicadas skill-authoring flow. Prefer dedicated skill-authoring tooling for
> new skills.

# Your Skill Name

## Overview

Brief description of what this skill does and the problem it solves.

## Instructions

Step-by-step instructions for the agent. Be explicit — the agent follows
these instructions literally when the skill is invoked.

1. **Step one**: Do this first.
2. **Step two**: Then do this.
3. **Step three**: Finally, do this.

## Scripts

> Remove this section if no scripts are bundled.

This skill includes helper scripts in `scripts/`. To use them:

```bash
python {skill-dir}/scripts/your-script.py [args]
```

## References

> Remove this section if no reference documents are bundled.

Key reference material for this skill is in `references/`. Read the relevant
file before performing the corresponding operation.
