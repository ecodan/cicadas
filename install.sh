#!/usr/bin/env bash
# Cicadas installer
# Usage: bash install.sh [--dir <path>] [--agent <list>] [--update]
# Or:    curl -fsSL https://raw.githubusercontent.com/ecodan/cicadas/master/install.sh | bash

set -euo pipefail

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
INSTALL_DIR=".cicadas-skill/cicadas"
AGENTS=""
UPDATE_ONLY=false
ARCHIVE_URL="https://github.com/ecodan/cicadas/archive/refs/heads/master.zip"

# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------
log()  { echo "[cicadas] $*"; }
ok()   { echo "[cicadas] ✓ $*"; }
err()  { echo "[cicadas] ✗ $*" >&2; }
blank(){ echo "[cicadas]"; }

# ---------------------------------------------------------------------------
# Arg parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dir)    INSTALL_DIR="$2"; shift 2 ;;
    --agent)  AGENTS="$2";      shift 2 ;;
    --update) UPDATE_ONLY=true; shift   ;;
    *)        err "Unknown option: $1"; exit 1 ;;
  esac
done

# ---------------------------------------------------------------------------
# Python 3.11+ check
# ---------------------------------------------------------------------------
PYTHON_BIN=""

check_python() {
  for candidate in python3 python; do
    if command -v "$candidate" > /dev/null 2>&1; then
      PYTHON_BIN="$candidate"
      break
    fi
  done

  if [ -z "$PYTHON_BIN" ]; then
    err "Python 3.11+ is required but Python was not found."
    blank
    print_python_install_guidance
    exit 1
  fi

  local version
  version=$("$PYTHON_BIN" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1)
  local major minor
  major=$(echo "$version" | cut -d. -f1)
  minor=$(echo "$version" | cut -d. -f2)

  if [ "$major" -lt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -lt 11 ]; }; then
    err "Python 3.11+ required (found: $version)"
    blank
    print_python_install_guidance
    exit 1
  fi

  ok "Python $version found"
}

print_python_install_guidance() {
  log "Install Python 3.11 or newer:"
  case "$(uname -s)" in
    Darwin) log "  macOS:   brew install python@3.11" ;;
    Linux)  log "  Ubuntu:  sudo apt install python3.11" ;;
    *)      log "  Windows: winget install Python.Python.3.11 (or use WSL)" ;;
  esac
  blank
  log "Then re-run this installer."
}

# ---------------------------------------------------------------------------
# unzip check
# ---------------------------------------------------------------------------
check_unzip() {
  if ! command -v unzip > /dev/null 2>&1; then
    err "'unzip' is required but not found."
    case "$(uname -s)" in
      Linux) log "  Install with: sudo apt install unzip" ;;
      Darwin) log "  Install with: brew install unzip" ;;
      *) log "  Please install unzip for your platform." ;;
    esac
    exit 1
  fi
}

# ---------------------------------------------------------------------------
# Download and extract
# ---------------------------------------------------------------------------
download_and_extract() {
  local target_dir="$1"
  log "Downloading Cicadas from GitHub..."

  local tmp_dir
  tmp_dir=$(mktemp -d)
  # shellcheck disable=SC2064
  trap "rm -rf '$tmp_dir'" EXIT

  if ! curl -fsSL "$ARCHIVE_URL" -o "$tmp_dir/cicadas.zip"; then
    err "Download failed. Check your internet connection and try again."
    exit 1
  fi

  unzip -q "$tmp_dir/cicadas.zip" -d "$tmp_dir"

  # The archive extracts to cicadas-master/
  local extracted="$tmp_dir/cicadas-master"
  if [ ! -d "$extracted" ]; then
    err "Unexpected archive structure. Expected '$extracted'."
    exit 1
  fi

  mkdir -p "$target_dir"
  # Copy the skill files from src/cicadas/ inside the archive
  cp -r "$extracted/src/cicadas/." "$target_dir/"

  ok "Downloaded and extracted to $target_dir/"
}

# ---------------------------------------------------------------------------
# Agent integrations
# ---------------------------------------------------------------------------
setup_agents() {
  local install_dir="$1"
  local agents_csv="$2"
  local absolute_install_dir
  absolute_install_dir="$(cd "$install_dir" && pwd)"

  # Determine relative path from project root to install_dir
  local rel_path="$install_dir"

  IFS=',' read -ra agent_list <<< "$agents_csv"
  for agent in "${agent_list[@]}"; do
    agent="${agent// /}"  # trim spaces
    case "$agent" in
      claude-code)
        log "Setting up claude-code integration..."
        mkdir -p .claude/skills
        # Use relative symlink: from .claude/skills/ back to project root, then into install_dir
        local depth
        depth=$(echo ".claude/skills" | tr -cd '/' | wc -c)
        local prefix
        prefix=$(printf '../%.0s' $(seq 1 $((depth + 1))))
        ln -sf "${prefix}${rel_path}" .claude/skills/cicadas
        ok ".claude/skills/cicadas → ${rel_path}"
        ;;
      antigravity)
        log "Setting up antigravity integration..."
        mkdir -p .agents/skills
        local depth
        depth=$(echo ".agents/skills" | tr -cd '/' | wc -c)
        local prefix
        prefix=$(printf '../%.0s' $(seq 1 $((depth + 1))))
        ln -sf "${prefix}${rel_path}" .agents/skills/cicadas
        ok ".agents/skills/cicadas → ${rel_path}"
        ;;
      cursor)
        log "Setting up cursor integration..."
        mkdir -p .cursor/rules
        if [ -f "$install_dir/SKILL.md" ]; then
          cp "$install_dir/SKILL.md" .cursor/rules/cicadas.mdc
          ok ".cursor/rules/cicadas.mdc created"
        else
          err "SKILL.md not found in $install_dir — cursor integration skipped"
        fi
        ;;
      rovodev)
        log "Setting up rovodev integration..."
        mkdir -p .rovodev/skills
        local depth
        depth=$(echo ".rovodev/skills" | tr -cd '/' | wc -c)
        local prefix
        prefix=$(printf '../%.0s' $(seq 1 $((depth + 1))))
        ln -sf "${prefix}${rel_path}" .rovodev/skills/cicadas
        ok ".rovodev/skills/cicadas → ${rel_path}"
        ;;
      codex)
        log "Setting up codex integration..."
        local codex_home="${CODEX_HOME:-$HOME/.codex}"
        mkdir -p "$codex_home/skills"
        ln -sfn "$absolute_install_dir" "$codex_home/skills/cicadas"
        ok "$codex_home/skills/cicadas → $absolute_install_dir"
        log "Restart Codex to pick up the new skill."
        ;;
      none|"")
        ;;
      *)
        err "Unknown agent: $agent (supported: claude-code, antigravity, cursor, rovodev, codex, none)"
        ;;
    esac
  done
}

# ---------------------------------------------------------------------------
# Interactive agent prompt (only when stdin is a tty)
# ---------------------------------------------------------------------------
prompt_for_agents() {
  if [ -t 0 ]; then
    blank
    log "Which AI coding agents are you using? (comma-separated, or 'none')"
    log "  Supported: claude-code, antigravity, cursor, rovodev, codex"
    printf "[cicadas] > "
    read -r AGENTS
  else
    # Running via curl | bash — can't read interactively
    blank
    log "Tip: Re-run with --agent <name> to set up agent integrations."
    log "  Example: bash install.sh --agent claude-code"
  fi
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  blank
  log "Cicadas Installer"
  blank

  if ! git rev-parse --git-dir > /dev/null 2>&1; then
    err "No git repository found. Run 'git init' first."
    exit 1
  fi

  if [ "$UPDATE_ONLY" = true ]; then
    log "Update mode: refreshing skill files in $INSTALL_DIR/..."
    check_unzip
    download_and_extract "$INSTALL_DIR"
    blank
    ok "Update complete. .cicadas/ workspace was not modified."
    blank
    exit 0
  fi

  # Full install
  log "Checking Python version..."
  check_python

  check_unzip
  download_and_extract "$INSTALL_DIR"

  log "Initializing .cicadas/ workspace..."
  if "$PYTHON_BIN" "$INSTALL_DIR/scripts/init.py"; then
    ok "Workspace initialized"
  else
    err "init.py failed — check output above"
    exit 1
  fi

  # Agent setup
  if [ -z "$AGENTS" ]; then
    prompt_for_agents
  fi

  if [ -n "$AGENTS" ] && [ "$AGENTS" != "none" ]; then
    setup_agents "$INSTALL_DIR" "$AGENTS"
  fi

  blank
  ok "Installation complete!"
  blank
  log "Next steps:"
  log "  python $INSTALL_DIR/scripts/status.py"
  blank
}

if [[ "${BASH_SOURCE[0]:-$0}" == "$0" ]]; then
  main
fi
