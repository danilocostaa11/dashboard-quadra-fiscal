# Memory Closure Check

Before reporting completion, the orchestrator checks:

- [ ] Did this task create or change a durable decision?
- [ ] Did it verify a command, test, build, lint, typecheck, or runtime behavior worth remembering?
- [ ] Did it create a protected TDD test or change the status of one?
- [ ] Did any existing note become stale, contradicted, or too broad?
- [ ] Are all notes using required frontmatter: memory_schema, type, status, scope, canonical, thesis, atomic, tags, properties, moc, links, sources, supersedes, last_verified?
- [ ] Do new permanent notes pass the five-question gate: atomic, thesis title, connects, unique, metadata?
- [ ] Is there only one active canonical decision note for each scope?
- [ ] Is the current trace scoped to one coherent task rather than an umbrella work log?
- [ ] Is the current decision trace linked from the relevant index or note?
- [ ] Do compact notes point back to the trace that proves them?
- [ ] Did `memory-maintenance.py --strict` pass when this task touched traces, notes, or memory?
- [ ] Are residual risks named in the trace and final answer?
