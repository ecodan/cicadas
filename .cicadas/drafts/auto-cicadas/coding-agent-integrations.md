Tool

Primary Form Factor

Core Capabilities

Ecosystem / Integrations

Agentic / Orchestration Features

How a Supervisor Would “Drive” That Agent

Claude Code

Terminal CLI, Desktop, Web, VS Code, JetBrains, CI, browser

Repo‑wide understanding; multi‑file edits; runs tests/commands; git branches/commits/PRs; CI code review; log analysis; web search; custom commands/hooks

MCP (Jira, Slack, GDrive, custom HTTP/MCP servers); CI (GitHub/GitLab); IDEs; Chrome; Slack; local/cloud/remote

Agentic loop (gather → act → verify); subagents; multi‑agent teams; auto memory; CLAUDE.md; permissions/checkpoints; Agent SDK

Supervisor spins up Claude Code sessions via CLI or Agent SDK, hands them tasks plus constraints, and then: inspects tool calls and diffs; configures hooks/permissions as guardrails; feeds new “interrupts” (tests failing, monitoring alerts, Jira updates) as structured context into subsequent turns; kills/forks sessions when they drift. Claude is a controllable sub‑agent, not the top‑level brain.

Cursor

Full AI IDE (VS Code‑like) plus cloud/mobile agents

Autocomplete and tab; inline edits; chat over full codebase; code search/refactor; doc + web lookup; image‑to‑code; per‑project rules and models

Git/GitHub; Slack; PR bots; extension marketplace; multiple LLMs (OpenAI, Anthropic, Gemini, Cursor models)

Task‑level agents that can plan/implement; cloud agents on remote compute; multi‑agent collaboration; automations; “shadow workspaces”; rules and autonomy slider

Supervisor doesn’t micromanage Cursor internals; it drives via artifacts: opens tasks that humans/agents pull, watches git and PRs as telemetry, configures Cursor rules/models, and wires CI/bots to emit structured feedback. Essentially: supervisor owns the queue and policies, while Cursor agents (and humans) churn through those tasks inside the IDE.

Google Antigravity

AI IDE (VS Code‑based) with central mission control across editor, terminal, browser

Tab completion; NL commands; browser‑in‑loop coding; verification artifacts (plans, tests, screenshots); context‑aware suggestions

VS Code lineage (settings/extensions import); supports Gemini 3 Pro, Claude Sonnet 4.5, GPT‑OSS; cross‑surface dev (editor/terminal/browser)

Agent‑first UX; multi‑agent orchestration via Agent Manager; autonomous agents across surfaces; task groups; async user feedback on artifacts; self‑improving knowledge base

Supervisor treats Antigravity as an agent farm: programmatically or manually creates task groups; defines policies and review criteria; lets Agent Manager run multiple agents; ingests artifacts as the agent’s “state”; and pushes feedback (approval, corrections, new constraints) back as comments or updated tasks. If/when APIs mature, the supervisor loop calls those directly to spawn/stop agents and harvest artifact metadata.

Rovo Dev

Agent layer spanning CLI, VS Code, Jira, Bitbucket, GitHub

Turns Jira items into plans + code; AI PR review; build failure analysis; deployment summaries; multi‑step code workflows

Deep Atlassian integration (Jira, Bitbucket Cloud, Teamwork Graph); GitHub; Rovo Dev CLI; uses OpenAI + Anthropic models

Context‑aware SDLC agent: automates planning → coding → review; PR reviewer with Jira acceptance‑criteria awareness; configurable review standards; background automations

Supervisor acts as SDLC conductor: shapes work as Jira issues and workflows that Rovo Dev consumes; configures review standards and automation playbooks; triggers Rovo Dev via CLI or Jira/PR hooks; listens to its outputs (plans, comments, status) as events; then decides when to escalate to humans, spin follow‑up tasks, or adjust acceptance criteria. Driving is mostly via Jira/PR state, not direct tool‑call steering.

