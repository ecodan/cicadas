# Cicadas Core Flows

Below are the three confirmed primary flows. They were traced through `src/cicadas/scripts/cicadas.py`, `src/cicadas/scripts/command_registry.py`, and the concrete script/util implementations.

## 1. Initiative Kickoff

Promotes draft specs into active state, registers the initiative, creates the initiative branch, and optionally creates a linked worktree.

```mermaid
sequenceDiagram
    autonumber
    box rgb(245,245,245) Client
      participant Client as "Agent / Operator"
    end
    box rgb(232,244,255) CLI Dispatch Unit
      participant CLI as "cicadas.py"
      participant Registry as "command_registry.py"
    end
    box rgb(238,248,240) Lifecycle Script Unit
      participant Kickoff as "kickoff.py"
      participant Check as "check.py"
      participant Utils as "utils.py"
      participant Tokens as "tokens.py"
      participant Events as "emit_event.py"
    end
    box rgb(255,246,230) Local State
      participant FS as ".cicadas filesystem"
      participant Git as "Local Git"
    end
    box rgb(255,238,238) External Boundary
      participant Remote as "Git Remote origin"
    end

    Client->>CLI: python cicadas.py kickoff {name} --intent ...
    CLI->>Registry: resolve aliases, parse command
    Registry->>Kickoff: subprocess python kickoff.py ...

    Kickoff->>Utils: get_project_root(), get_registry_dir(), load_config()
    Utils->>FS: locate .cicadas / .git, read config.json
    Kickoff->>FS: read registry.json

    alt initiative already registered
      Kickoff-->>Client: [ERR] Initiative already exists
    else new initiative
      Kickoff->>FS: mkdir .cicadas/active/{name}

      alt drafts exist
        Kickoff->>FS: move drafts/{name}/* -> active/{name}/
        Kickoff->>FS: remove empty drafts/{name}
      else no drafts
        Kickoff-->>Client: [WARN] No drafts found
      end

      Kickoff->>FS: write registry.json initiatives[name]
      Kickoff->>Utils: emit(name, "initiative.kicked_off")
      Utils->>Events: emit_event(...)
      Events->>Git: git branch --show-current
      Events->>FS: append active/{name}/events.jsonl
      Note over Utils,Events: Event emission is synchronous but best-effort; failures are swallowed.

      Kickoff->>Tokens: append_entry(active/{name}/tokens.json)
      Tokens->>FS: lock, read, atomic write tokens.json

      Kickoff->>Utils: parse_partitions_dag(active/{name}/approach.md)
      Utils->>FS: read approach.md

      opt parallel partitions detected
        Kickoff->>Check: check_conflicts(initiative_name=name)
        Check->>FS: read registry.json
        Check->>Git: detect default branch
        Check->>FS: inspect registered branch modules and stale worktree paths
        alt module conflicts found
          Check-->>Kickoff: true
          Kickoff-->>Client: [WARN] Resolve module conflicts
        else no conflicts
          Check-->>Kickoff: false
          Kickoff-->>Client: [OK] No module conflicts
        end
      end

      Kickoff->>Git: git branch initiative/{name}
      alt branch creation fails
        Kickoff-->>Client: [WARN] Could not create git branch
      else branch created
        Kickoff-->>Client: [OK] Created initiative branch
      end

      Kickoff->>Remote: git push -u origin initiative/{name}
      alt push fails
        Kickoff-->>Client: [WARN] Push manually
      else push succeeds
        Kickoff-->>Client: [INFO] Pushed branch
      end

      alt worktree requested or enabled by config
        Kickoff->>Utils: worktree_path(), create_worktree()
        Utils->>Git: git --version; git worktree add
        alt worktree creation succeeds
          Kickoff->>FS: update registry.json worktree_path
          Kickoff-->>Client: [OK] Worktree created
        else worktree creation fails
          Kickoff-->>Client: [WARN] Could not create worktree
        end
      else worktree disabled
        Kickoff-->>Client: continue in current workspace
      end

      Kickoff-->>Client: [OK] Initiative kicked off
    end

    Note over CLI,Remote: No HTTP gateway, auth service, DB, cache, or async queue exists in this flow.
```

The kickoff flow is file-and-git centered: `.cicadas/registry.json` is the durable registry, active specs are plain directories, and git branches/remotes are the system boundary. The only gate comparable to auth is registry existence and conflict validation. Event emission is deliberately non-fatal, while token accounting is stricter about locking and atomic writes. Remote push failure does not abort kickoff; it degrades to manual push guidance.

## 2. Branch Start

Creates and registers a feature, fix, tweak, or skill branch, deciding whether to use the current workspace or a linked worktree.

```mermaid
sequenceDiagram
    autonumber
    box rgb(245,245,245) Client
      participant Client as "Agent / Operator"
    end
    box rgb(232,244,255) CLI Dispatch Unit
      participant CLI as "cicadas.py"
      participant Registry as "command_registry.py"
    end
    box rgb(238,248,240) Branch Script Unit
      participant Branch as "branch.py"
      participant Utils as "utils.py"
      participant Tokens as "tokens.py"
      participant Events as "emit_event.py"
    end
    box rgb(255,246,230) Local State
      participant FS as ".cicadas filesystem"
      participant Git as "Local Git"
    end
    box rgb(255,238,238) External Boundary
      participant Remote as "Git Remote origin"
    end

    Client->>CLI: python cicadas.py branch {name} --intent ... --modules ... --initiative ...
    CLI->>Registry: resolve aliases, parse command
    Registry->>Branch: subprocess python branch.py ...

    Branch->>Utils: get_project_root(), get_registry_dir(), get_default_branch(), load_config()
    Utils->>FS: locate repo and read config.json
    Branch->>FS: read registry.json

    alt branch already registered
      Branch-->>Client: [ERR] Branch already registered
    else new branch
      Branch->>Branch: parse requested modules
      Branch->>FS: compare modules against registry branches

      Branch->>Branch: choose parent ref
      alt explicit parent branch supplied
        Branch->>Git: resolve explicit parent
      else fix/tweak/skill branch
        Branch->>Git: resolve default branch
      else initiative feature branch
        Branch->>Git: resolve initiative/{initiative}
      else no parent
        Branch->>Branch: create from current HEAD
      end

      Branch->>Utils: parse worktree policy
      Branch->>FS: read active/{initiative}/approach.md when feature partition
      Branch->>Utils: parse_partitions_dag()

      alt worktree forced
        Branch->>Branch: use linked worktree
      else plain branch forced
        Branch->>Branch: use current workspace branch
      else lightweight and config auto_worktrees.lightweight
        Branch->>Branch: use linked worktree
      else parallel feature partition and config auto_worktrees.parallel_features
        Branch->>Branch: use linked worktree
      else sequential/default path
        Branch->>Branch: use current workspace branch
      end

      alt linked worktree path
        Branch->>Git: git branch {name} {parent_ref}
        Branch->>Remote: git push -u origin {name}
        alt push fails
          Branch-->>Client: [WARN] Push manually
        end
        Branch->>Utils: create_worktree(root, name, target)
        Utils->>Git: git --version; git worktree list/add
        alt worktree add fails
          Branch-->>Client: [ERR] git worktree add failed
          Branch-->>Client: exit 1
        else worktree created
          Branch->>Utils: emit(..., "worktree.created")
          Utils->>Events: append event jsonl best-effort
          Branch->>FS: write context.md in worktree
        end
      else current workspace path
        Branch->>Git: git checkout -b {name} {parent_ref}
        Branch->>Remote: git push -u origin {name}
        alt push fails
          Branch-->>Client: [WARN] Push manually
        end
        Branch->>FS: write context.md in project root
      end

      Branch->>FS: update registry.json branches[name]
      alt initiative argument not found in registry
        Branch-->>Client: [WARN] Initiative not found
      else initiative exists
        Branch->>FS: store initiative link
      end

      Branch->>Utils: emit(..., "branch.created")
      Utils->>Events: append active/{initiative}/events.jsonl
      Branch->>FS: mkdir active/{active_name}
      Branch->>Tokens: append_entry(active/{active_name}/tokens.json)
      Tokens->>FS: lock, read, atomic write tokens.json

      alt module overlaps found
        Branch-->>Client: [WARN] Module overlaps detected
      end

      Branch-->>Client: [OK] Branch registered
    end

    Note over CLI,Remote: No auth middleware, cache, DB, or queue is involved; git and local files are the state boundary.
```

Branch creation has the most conditional routing in these flows. The branch type, initiative association, partition DAG, config, and explicit flags decide whether the script creates a normal checked-out branch or a linked worktree. A worktree creation failure is fatal in the worktree path, but remote push failure is only advisory. The context bootstrap file is assembled from canon summary, repo context, module snapshots, approach, and tasks.

## 5. Completion / Canon Reconcile / Archive

Generates or applies canon reconciliation context, then archives active specs and deregisters completed work.

```mermaid
sequenceDiagram
    autonumber
    box rgb(245,245,245) Client
      participant Client as "Agent / Operator"
      participant LLM as "External LLM / AI Host"
    end
    box rgb(232,244,255) CLI Dispatch Unit
      participant CLI as "cicadas.py"
      participant Registry as "command_registry.py"
    end
    box rgb(238,248,240) Completion Script Unit
      participant Synth as "synthesize.py"
      participant Scan as "scan_repo.py"
      participant Archive as "archive.py"
      participant Utils as "utils.py"
      participant Events as "emit_event.py"
    end
    box rgb(255,246,230) Local State
      participant FS as ".cicadas filesystem"
      participant Git as "Local Git"
    end

    Client->>CLI: python cicadas.py synthesize {name}
    CLI->>Registry: parse command
    Registry->>Synth: subprocess python synthesize.py ...

    Synth->>Utils: get_project_root(), load registry.json
    Synth->>FS: read .cicadas/registry.json
    Synth->>Utils: load_repo_metadata(), load_repo_tree(), load_repo_context()
    Utils->>FS: read .cicadas/canon/repo.json, repo-tree.jsonl, repo-context.md

    alt repo metadata missing
      Synth->>Scan: run_scan(root)
      Scan->>Git: git check-ignore --stdin
      Scan->>FS: scan repo tree, classify files, write repo-tree.jsonl
      Scan->>FS: write canon/repo.json and canon/repo-context.md
      Synth->>Utils: reload repo metadata/tree/context
    end

    Synth->>Utils: build_canon_plan()
    Synth->>FS: read active specs from active/{initiative-or-branch-owner}/*.md

    alt initiative synthesis mode
      Synth->>Git: git diff --name-only HEAD~1 HEAD
      Synth->>Utils: build_reconcile_scope(metadata, active_docs, changed_paths)
      alt large/mega repo
        Utils-->>Synth: targeted canon_doc_scope and code_scope
      else normal repo
        Utils-->>Synth: full canon reconcile scope
      end
    else branch synthesis
      Synth->>FS: read branch modules from registry.json
    end

    Synth->>Utils: collect_code_context(root, modules/code_scope, repo_tree)
    Utils->>FS: read matched source files
    Synth->>FS: read scoped canon docs and index.json

    alt prompt generation mode
      Synth->>FS: read templates/synthesis-prompt.md
      Synth-->>Client: print synthesis prompt
      Client->>LLM: submit prompt outside Cicadas
      LLM-->>Client: canon file blocks response
      Note over Synth,LLM: synthesize.py does not call an LLM API; external AI use is operator/host-driven.
    else apply response file mode
      Synth->>FS: read response file
      Synth->>Synth: parse File: canon/... fenced blocks
      alt no file content blocks
        Synth-->>Client: No file content blocks found
      else blocks found
        loop each canon block
          alt unsafe path escapes canon/
            Synth-->>Client: Skipped unsafe canon path
          else safe canon path
            Synth->>FS: write .cicadas/canon/{path}
          end
        end
      end
    end

    Client->>CLI: python cicadas.py archive {name}
    CLI->>Registry: parse command
    Registry->>Archive: subprocess python archive.py ...

    Archive->>Utils: get_project_root(), get_registry_dir(), load_json()
    Archive->>FS: read registry.json

    alt name not in registry
      Archive-->>Client: [ERR] not found in registry
    else registered
      alt registry entry has worktree_path
        Archive->>Utils: remove_worktree(root, path, force)
        Utils->>FS: check worktree path exists
        alt worktree missing
          Utils->>Git: git worktree prune
          Archive-->>Client: [WARN] already removed
        else dirty worktree without force
          Utils->>Git: git -C worktree status --porcelain
          Archive-->>Client: [WARN] Worktree has uncommitted changes
          Archive-->>Client: exit 1
        else removable
          Utils->>Git: git worktree remove [--force] path
          Archive-->>Client: [OK] Worktree removed
        end
      end

      Archive->>FS: resolve active spec dir
      alt active specs exist
        Archive->>FS: write active/.cicadas_metadata.json
        alt lightweight fix/tweak/skill branch
          Archive-->>Client: significance check reminder before canon update
        end
        Archive->>Utils: emit(name, "specs.archived")
        Utils->>Events: append active/{name}/events.jsonl best-effort
        Archive->>FS: move active/{name} -> archive/{timestamp}-{name}
      end

      Archive->>FS: delete registry entry
      alt archiving initiative
        loop associated branches
          opt associated branch has worktree
            Archive->>Utils: remove_worktree(...)
          end
          Archive->>FS: delete associated branch registry entry
        end
      end

      Archive->>FS: write registry.json
      Archive-->>Client: [OK] Deregistered
    end

    Note over CLI,Git: No async queue exists. Canon reconciliation is local file I/O; the only external system shown is the optional human/host-driven LLM step.
```

Completion is split across two deterministic commands: `synthesize` prepares or applies canon changes, and `archive` moves the lifecycle state out of active work. The synthesis command intentionally does not call an LLM directly; it either prints a prompt or applies a previously saved response file. Large and mega repos get targeted reconcile scope, while normal repos use full synthesis. Archive is conservative around worktrees: dirty worktrees block unless `--force` is supplied.

## Cross-Cutting Summary

Core dependencies in all three flows are `cicadas.py`, `command_registry.py`, local `.cicadas` JSON/files, shared `utils.py`, and local git. There is no HTTP API gateway, auth service, token validation middleware, DB server, cache, or message queue in the implemented architecture.

The most visible single points of failure are `.cicadas/registry.json`, the primary worktree's `.cicadas` directory, and local git availability. Git remote push is a frequent external boundary, but most push failures are warnings rather than hard stops.

The busiest coupling hotspot is between lifecycle scripts and `utils.py`: root detection, registry path resolution, worktree policy, event emission, canon scope, and git helpers all live there. The most non-obvious implementation detail is that event emission is best-effort and may silently fail, while token logs use locking and atomic writes; those two audit trails have different reliability semantics.
