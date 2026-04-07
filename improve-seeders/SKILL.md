---
name: improve-seeders
description: "Improves database seeders and factories for development experience. Audits models, factories, and seeders for data integrity, missing fields, idempotency, and test coverage support."
---

# Improve Seeders

## When to Apply

Activate this skill when:

- Auditing or improving database seeders or factories
- A factory is missing fields or states needed for a feature or test
- A seeder fails on re-run (idempotency issue)
- Creating a new model that needs seed data
- Reviewing whether the seeding layer supports the current codebase

## What to Improve

Prioritized checklist — address whatever is relevant to the current context. Read the actual files before deciding what needs doing; do not assume a known issue still exists.

### 1. Idempotency

- Reference data seeders should use `updateOrCreate()` or `firstOrCreate()` so they can run repeatedly without duplicates or errors.
- Check every seeder for bare `create()` calls and replace them.

### 2. Factory Completeness

- Factories should cover all fillable/required fields on the model, not just the minimum to pass validation.
- Factories should have useful states for common variants (e.g. `->npc()`, `->player()`, `->complete()`).
- Check every factory against its model's fillable properties and relationships.

### 3. Seeder Data Integrity

- Reference data seeders should contain accurate D&D 5e data.
- Cross-check seeded data against the model's fields — if a column exists, the seeder should populate it.
- Ensure foreign key relationships are satisfied (e.g. races should reference valid sources).

### 4. Missing Seeders

- Check for lookup/reference tables that have no seeder and should.
- `DatabaseSeeder` should call seeders in dependency order (sources before races, etc.).

### 5. Seeder Robustness

- Seeders that load files from disk should handle missing files gracefully rather than throwing.
- Seeders should use factory states instead of manual relationship wiring where possible.

### 6. Test Support

- Factories should make it easy to create valid models in tests without excessive manual setup.

## How to Work

1. Read the relevant model, factory, and seeder files.
2. Read sibling files to understand existing conventions.
3. Make the smallest meaningful change that addresses the issue.
4. Run `vendor/bin/pint --dirty --format agent` on changed PHP files.
5. Run the affected seeder to verify: `php artisan db:seed --class=TheSeeder --no-interaction` (use `--force` if needed).
6. If you changed a factory, run related tests: `php artisan test --compact --filter=RelevantTest`.
7. Commit with a clear message like `refactor: make CharacterClassSeeder idempotent`.

## Rules

- Do NOT delete existing seed data without approval.
- Do NOT change model code — only seeders and factories.
- Do NOT add new dependencies.
- Follow existing code conventions (check sibling files).
- Use `updateOrCreate()` / `firstOrCreate()` over `create()` for reference data.
- Run Pint before committing.
- Once committed, push the branch to origin so changes are reflected on the remote
