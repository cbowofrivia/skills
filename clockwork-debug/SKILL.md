---
name: clockwork-debug
description: 'Analyzes Clockwork request profiling data to find N+1 queries, slow queries, and performance issues for a specific route or controller.'
---

# Clockwork Request Debugger

## When to Activate

Use this skill when:

- The user asks to debug N+1 queries, slow queries, or performance issues for a route
- The user mentions Clockwork profiling data
- The user says "have a look at" or "debug" performance for a specific URL path or controller
- The user provides a URI (e.g., `/codex/charles-8797`) or controller FQCN (e.g., `App\Http\Controllers\Codex\CodexIndexController`)

## How Clockwork Data is Stored

- **Index file:** `storage/clockwork/index` — one line per request, comma-separated fields
- **Request files:** `storage/clockwork/{id}.json` — full profiling data per request (~400-500KB each)
- **Analyze script:** `.claude/skills/clockwork-debug/analyze.py` — extracts and summarizes a single request file

### Index Line Format

```
{id},{timestamp},{method},{uri},{controller},{status},{duration_ms},{type}
```

Example:

```
1773766973-3035-1977356974,1773766973.2629,GET,/codex/charles-8797,App\Http\Controllers\Codex\CodexIndexController,200,480.61,request
```

Fields:

1. `id` — filename stem (e.g., `1773766973-3035-1977356974`)
2. `timestamp` — Unix timestamp with decimals (use to find the most recent request)
3. `method` — HTTP method
4. `uri` — request URI path
5. `controller` — FQCN of the controller (may include `@method`)
6. `status` — HTTP status code
7. `duration_ms` — response time in milliseconds
8. `type` — usually `request`

## Step-by-Step Procedure

### 1. Search the Index

Read `storage/clockwork/index` and find matching lines. Match against the user's input:

- If the user gave a **URI path** (e.g., `/codex/charles-8797`), match field 4
- If the user gave a **controller** (e.g., `CodexIndexController`), match field 5 (substring match is fine)
- If the user gave both, match both

From all matches, pick the **most recent** one (highest timestamp in field 2).

### 2. Run the Analyze Script

The JSON files are ~400-500KB. **Do NOT read the full file with the Read tool.** Instead, run the bundled analysis script:

```bash
# Default — compact output
python3 .claude/skills/clockwork-debug/analyze.py storage/clockwork/{id}.json

# With full stack traces for each N+1 and slow query
python3 .claude/skills/clockwork-debug/analyze.py --trace storage/clockwork/{id}.json
```

Use `--trace` when the first-frame origin isn't enough to understand the call path (e.g., relationship accessors called in loops).

This outputs:

- Request summary (URL, controller, response time, DB time, memory, query count)
- Models retrieved breakdown
- N+1 query candidates with repeat counts, model names, originating file:line, and estimated time waste
- Top 10 slowest individual queries with originating file:line
- Cache hit/miss summary

### 3. Analyze and Report

Present findings in this order:

1. **Request overview** — URL, controller, response time, query count, memory
2. **N+1 queries** — The primary target. For each repeated pattern:
   - How many times it repeats
   - Which model it loads
   - The originating app code (file + line from the script output)
   - The estimated total time wasted
3. **Slow queries** — Any individual query taking >10ms
4. **Models retrieved** — Which models are being loaded and how many
5. **Recommendations** — Concrete fixes:
   - Which relationships to eager-load and where (e.g., "Add `->with('world')` to the query in `CodexIndexController@show`")
   - Whether to use `select()` to limit columns
   - Whether queries can be eliminated entirely

### 4. Trace Back to Code

The script output includes the originating file and line for each N+1 and slow query (first non-vendor stack frame).

Read those source files to understand the code path and suggest specific fixes (eager loading, query optimization, caching).

## Important Notes

- **Never read the full JSON file with the Read tool** — it's too large. Always use the analyze script.
- The index file may be small or large. Read it fully, then filter.
- Timestamps in the index are Unix timestamps — higher = more recent.
- A query appearing 50+ times with the same normalized pattern is a strong N+1 signal.
- The `model` field on each query tells you which Eloquent model is being loaded.
- Focus on **app-originating** trace frames, not vendor/framework frames.
