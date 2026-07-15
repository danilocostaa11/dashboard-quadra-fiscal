# AGENTS Instructions

<!-- fable-harness:start -->

## Fable Harness

These instructions install the local Fable Harness for any. Use it for non-trivial, mutating, complex, multidisciplinary, or audit-sensitive work.

### Boot Sequence

1. Read this project instruction file first.
2. Run `.agents/scripts/release-notice.py check` once at boot when available. It checks at most once every 24 hours and only prints a notice if a newer GitHub release exists; it never downloads or applies updates.
3. Read `.agents/notes/_index.md` when it exists.
4. Read only the compact notes relevant to the task.
5. Open decision traces only when audit or continuation requires the decision path.
6. Read the real project files before editing them.

### Project-Local Harness Scope

- When the user asks to save, memorize, remember, store, register, persist, or update project context, use `.agents/` first.
- Do not satisfy those requests only through global model memory, external notes, chat summary, or user-level agent storage; those may be extra mirrors, but `.agents/` is mandatory.
- Use `.agents/scripts/new-note.py`, `.agents/scripts/promote-trace.py`, `.agents/scripts/rebuild-memory.py`, and `.agents/scripts/memory-touch.py` for local durable memory work.
- Use `.agents/decision-traces/` for audit evidence and `.agents/notes/` for compact semantic memory before any model-native memory mirror.
- When any Fable Harness feature exists locally, prefer the local `.agents/scripts/` tool over an equivalent global or model-native memory action.
- If higher-priority runtime policy also requires global/model memory, do both: first write or update the project-local harness artifact, then mirror or summarize globally with the local artifact path as the source.
- If the local harness tool is missing or fails, record the blocker in the trace and use the nearest local artifact path manually rather than silently switching only to global memory.

### Recall Ladder

Use this order for non-trivial recall, from fastest and most compact memory toward deeper and slower evidence:

1. Run `.agents/scripts/memory-search.py` with a concise query derived from the task, unless the task is clearly self-contained.
2. For memory-heavy answers or plans, run `.agents/scripts/rag-pipeline.py --query "<task>"` and inspect the cited source lines before answering or planning.
3. When RAG informs work that may change project code or docs, run a lightweight source-arbitration check against the real project files before planning or editing.
4. Read `.agents/notes/_index.md` to identify canonical compact notes.
5. Read the compact semantic notes that match the task; prefer active canonical notes over trace summaries.
6. Record every loaded note, trace, or dormant item with `.agents/scripts/memory-touch.py`.
7. Use `.agents/scripts/graph-query.py --q` when relationships, decisions, sources, or prior verification paths matter.
8. Use `.agents/scripts/memory-dream.py search-dormant` before declaring old context unavailable.
9. Open decision traces only for audit, continuation, disputed decisions, or missing evidence.
10. Read project docs and source files before editing; source files remain stronger operational evidence than generated memory.
11. At closure, promote durable decisions, rebuild memory, run strict maintenance, and run agent-reviewed dream maintenance when memory-heavy.

### Source Escalation

- Do not create a plan from an empty evidence base.
- Before planning non-trivial or unfamiliar work, verify whether memory, notes, decision traces, project docs, source files, or other local artifacts provide a structured and checkable basis.
- A source is strong enough when it has clear ownership, stable location, current relevance, and enough detail to support concrete planning.
- If memory, notes, traces, docs, and source files do not provide a verifiable structured source, research the web before planning.
- Use primary or official sources when available, and record links or citations in the trace.
- Treat web results as planning evidence only when they are relevant, credible, and specific enough to reduce uncertainty.
- If the task is completely new and neither project sources nor strong web references provide enough planning ground, interview the user before creating a plan.
- Keep the interview focused on project-specific intent, constraints, success criteria, examples, non-goals, and verification.
- After the interview, repeat source discovery with the new terms before committing to an implementation plan.

### Programming Recall

- For non-trivial programming work, combine semantic recall with Code Graph orientation before planning edits.
- Use semantic recall to understand prior decisions, architecture intent, constraints, and verification history.
- Use Code Graph to map files, symbols, dependencies, callers, tests, and static impact; semantic recall explains why; Code Graph maps where and what may break.
- Run `.agents/scripts/code-graph-build.py` and `.agents/scripts/code-graph-query.py` before broad source-code edits when symbol, import, call, test, or static impact orientation would reduce risk.
- Read the real source files identified by the graph before editing; source files remain the final operational authority.
- Treat Code Graph output as orientation evidence only. If Code Graph output conflicts with source files, source files win.
- After source edits that change public symbols, rebuild the code graph with `.agents/scripts/code-graph-build.py` or state why it was not needed.

### User Change Arbitration

- Treat files changed by the user after prior agent work as new task context, not as regressions by default.
- Before repairing, reverting, reformatting, normalizing, or rewriting a file that differs from prior agent expectations, inspect the current diff and decide whether the difference may be user-authored.
- Do not rewrite, revert, reformat, normalize, or otherwise alter a user-modified file just to satisfy stale tests, snapshots, generated expectations, or prior agent preferences without asking the user first.
- If tests fail after user edits, report the failing expectation and ask whether the user wants to preserve the new behavior, update the tests, or restore the old behavior.
- Explicit user constraints such as `do not edit`, `preserve`, `only change`, `leave untouched`, or named file/path limits override stale plans and prior harness expectations unless the user approves changing them.
- Tests are evidence, not ownership. Protected TDD tests still must not be weakened silently; when protected tests conflict with user changes, pause and ask which contract should now govern.

### Decision Loop

1. Orient: restate the task operationally and identify the smallest relevant surface.
2. Inspect: read the files, logs, docs, or state that govern that surface.
3. Decide: name the intended change or conclusion before the first mutating action.
4. Act: make the smallest coherent mutation or produce the narrowest requested artifact.
5. Verify: run the real gate when it exists; otherwise run the strongest available structural check.
6. Report: give files, numbers, verification, and limits without inflating certainty.

### Workflow Patterns

- Treat workflow patterns as composable recipes, not exclusive modes.
- Start with `classify-and-act` for non-trivial tasks to route the work.
- Use `generate-and-filter` when multiple viable solutions should be compared against explicit criteria.
- Use `tournament` only when relative pairwise comparison is safer than absolute scoring.
- Use `fan-out-and-synthesize` when independent domains can run in simultaneous subagent waves.
- Use `adversarial-verification` before accepting high-risk decisions or mutations.
- Use `loop-until-done` for iterative debugging, investigation, repair, or quality closure, bounded by budgets and stop conditions.
- Record the selected recipe in loop state or trace evidence; update it when inspection changes the task shape.

### Parallel Agent Dispatch And Safety

- During Orient/Classify, automatically evaluate whether the task has independent domains that should be delegated to subagents.
- Treat this Fable Harness block as standing project-level user authorization to invoke available subagent or parallel-agent tools automatically when the independence check passes.
- Do not ask for per-prompt permission before dispatching subagents when these conditions are met.
- Do not wait for the user to say `Dispatching Parallel Agents` or any other trigger phrase.
- If the platform exposes a subagent or parallel-agent tool and the independence check passes, invoke it.
- If a higher-priority runtime or tool policy blocks dispatch despite this standing authorization, record that as a platform limitation in the trace, then create the dispatch briefs and execute them sequentially.
- Parallelize independent tasks or independent loop runs, not dependent steps inside one loop.
- Default to subagent dispatch for complex or multidisciplinary work when at least two domains can progress independently.
- Sequential loop order applies inside one domain or dependency chain; it is not a reason to collapse independent domains back into the orchestrator.
- The independence check is a dispatch test, not a prohibition. If domains have separate inputs, outputs, and responsibility boundaries, create a simultaneous subagent wave.
- A single loop run is sequential by default. Orient before inspect, inspect before decide, decide before act, act before verify, verify before report or repair.
- Synchronize each subagent wave before integration, verification, memory promotion, or closure.
- Do not run `.agents/scripts/loop-event.py`, `.agents/scripts/loop-transition.py`, or `.agents/scripts/loop-check.py` concurrently for the same run.
- Do not run `.agents/scripts/rebuild-memory.py` concurrently with `.agents/scripts/memory-maintenance.py`, `.agents/scripts/graph-check.py`, `.agents/scripts/memory-dream.py plan`, or `.agents/scripts/memory-dream.py maintain`.
- Generated state is one-writer by default: loop runs, memory shards, graph files, dream runs, rollback plans, and instruction installs must be written in ordered steps.
- Verification happens after mutation; closure happens after verification and memory rebuild.
- If parallel work creates out-of-order evidence or a race, stop, record a repair event, and continue sequentially until the loop is healthy again.

### Harness Rules

- For non-trivial or mutating work, create or continue a trace in `.agents/decision-traces/`.
- Use `.agents/scripts/new-trace.py` to create a trace when practical.
- Use `.agents/scripts/release-notice.py check` at boot to warn about newer Fable Harness releases. It is notification-only, throttled to 24 hours, and leaves manual update decisions to the user.
- Use `.agents/scripts/loop-start.py` to create a native loop governance run for complex, mutating, multidisciplinary, or audit-sensitive work.
- Use `.agents/scripts/loop-event.py` and `.agents/scripts/loop-transition.py` to record inspect, decision, mutation, verification, repair, closure, and subagent-wave evidence in `.agents/loop/runs/`.
- Use `.agents/scripts/loop-check.py --strict` before closing governed work; strict mode fails when the loop mutates before inspect/decide, skips verification after mutation, closes without closure evidence, leaves subagent results unaccepted, or closes with subagent sessions still open.
- Use `.agents/scripts/new-note.py` for compact semantic notes in `category/area/topic.md` layout.
- Use `.agents/scripts/promote-trace.py` to promote durable trace evidence into semantic notes.
- Use `.agents/scripts/subagent-result.py` to record subagent outcomes in the dispatch package and active trace.
- Use `.agents/scripts/subagent-sweep.py --close-completed` near final closure when a subagent plan was used. Close completed sessions unless a domain is explicitly kept open or closure is unavailable with a reason.
- Before broad filesystem exploration or planning a non-trivial task, run `.agents/scripts/memory-search.py` with a concise query derived from the user request, unless the task is clearly self-contained.
- Use `.agents/scripts/rag-pipeline.py` for explicit `retrieve -> inspect sources -> answer/plan with citations` work. Do not answer or plan from retrieval scores alone; inspect the cited source lines first.
- Use `.agents/scripts/source-arbitrate.py` when RAG informs a task that may change project code or docs. Run a lightweight source-arbitration check against the real project files before planning or editing; if material conflict is found, escalate to a full Evidence Dispute and ask the user before replacing project facts with RAG-derived facts.
- Use `.agents/scripts/rag-eval.py` with a local JSON/JSONL evaluation set when tuning retrieval behavior; report precision@k, recall@k, hit-rate@k, and MRR instead of impressions.
- Use `.agents/scripts/rebuild-memory.py` when notes or traces were edited manually.
- Use `.agents/scripts/graph-query.py` to inspect generated semantic knowledge graph entities/relations, including `--q` text lookup; use `.agents/scripts/graph-check.py --strict` after graph-sensitive memory changes.
- Before broad source-code edits, use `.agents/scripts/code-graph-build.py` and `.agents/scripts/code-graph-query.py` when available to orient around symbols, imports, calls, tests, and static impact.
- Treat code graph output as orientation evidence only. Read the real source files before editing; if graph output conflicts with source files, source files win.
- After source edits that change public symbols, rebuild the code graph with `.agents/scripts/code-graph-build.py` or state why it was not needed.
- Use `.agents/scripts/memory-maintenance.py` periodically or after large tasks to report oversized notes, broken sources, stale notes, and archive-ready promoted traces.
- Use `.agents/scripts/memory-maintenance.py --strict` before closing memory-heavy work; strict mode fails on umbrella traces, invalid note schema, duplicate active canonical notes, and other high-severity hygiene issues.
- Use `.agents/scripts/memory-touch.py` when loading a note, trace, or dormant item for task context; it records retrieval use without editing the source memory file.
- Use `.agents/scripts/memory-dream.py maintain --context "<current task>" --auto-safe --agent-review` after memory-heavy work; it applies context-cold safe mechanical actions and writes `agent-review.md` for semantic decisions.
- Use `.agents/scripts/memory-dream.py plan` and `apply --apply` only when a manual two-step review workflow is needed.
- Prefer running `memory-dream.py maintain --auto-safe --agent-review` as a background memory curator/subagent task when the main task should not be blocked by memory hygiene; the orchestrator reviews `agent-review.md`, not the user by default.
- Search dormant memory before declaring old context unavailable. Use `.agents/scripts/memory-dream.py search-dormant`.
- Use `.agents/scripts/memory-dream.py reactivate --apply` to restore compact active notes from dormant evidence, not to dump archives back into active retrieval.
- When the user asks to revert or roll back specific agent changes, use `.agents/scripts/selective-revert.py` to create an auditable plan first; apply only with explicit user intent and `--apply`.
- Keep `.agents/notes/` compact and semantic. Use traces for audit evidence.
- Keep one trace per coherent task. Do not use broad active traces named `misc`, `plus`, or `session`; umbrella traces are only allowed as `session-index` or `migration-trace`.
- Notes must declare `memory_schema`, `type`, `status`, `scope`, `canonical`, `thesis`, `atomic`, `tags`, `properties`, `moc`, `links`, `sources`, `supersedes`, and `last_verified` frontmatter.
- New permanent notes use `memory_schema: atomic-v1`: one idea, title as thesis, explicit connections, unique scope, and queryable metadata.
- Keep only one active canonical decision note per `scope`. Use trace summaries or superseded notes for historical duplicates.
- Keep `.agents/memory/` as generated retrieval state: sharded local embeddings, promotion log, and a rebuildable semantic knowledge graph.
- The main orchestrating agent owns memory coherence.
- Subagents may gather evidence, run checks, and suggest memory updates, but do not silently decide what becomes durable project memory.
- For complex or multidisciplinary tasks, break work into small verifiable subtasks and assign subagents dynamically when they add leverage.
- Use `.agents/scripts/subagent-plan.py` to create dispatchable subagent briefs before broad execution when the task has independent domains; use `--parallel` and `--depends-on dependent:dependency` when domains can run in simultaneous waves.
- Dispatch subagents from the generated briefs: run all domains in the same generated wave simultaneously using the available subagent tool. If no subagent tool exists, execute the briefs sequentially and record that fallback in the trace.
- At final implementation closure, close/archive every completed subagent session. If the runtime exposes no close/archive action, record `close-unavailable` with the platform reason; if a session must remain open, record `keep-open` with the next planned use.
- Pass subagents minimal context: objective, relevant files, active decisions, protected tests, current trace, and verification command.
- TDD tests written before implementation are protected evidence. Do not weaken, skip, rename, delete, or rewrite them just to make the loop pass.
- Update cadence: trace during the work, semantic notes after verified evidence, indexes at closure.
- Before reporting completion, run the memory closure check in `.agents/templates/memory-closure.md`; use `.agents/scripts/check-closure.py` when practical.

<!-- fable-harness:end -->
