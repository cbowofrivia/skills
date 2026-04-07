---
name: workflow:review
description: Perform exhaustive code reviews using multi-agent analysis and deep inspection
argument-hint: "[PR number, GitHub URL, branch name, or latest]"
---

# Review Command

Perform exhaustive code reviews using multi-agent analysis and deep inspection.

## Introduction

Act as a Senior Code Review Architect with expertise in security, performance, architecture, and quality assurance.

## Prerequisites

- Git repository with GitHub CLI (`gh`) installed and authenticated
- Clean main/master branch
- Proper permissions to access the repository

## Main Tasks

### 1. Determine Review Target & Setup (ALWAYS FIRST)

<review_target> #$ARGUMENTS </review_target>

#### Immediate Actions:

- [ ] Determine review type: PR number (numeric), GitHub URL, file path (.md), or empty (current branch)
- [ ] Check current git branch
- [ ] If ALREADY on the target branch → proceed with analysis on current branch
- [ ] If DIFFERENT branch → use `gh pr checkout` or `git checkout` to switch to it
- [ ] Fetch PR metadata using `gh pr view --json` for title, body, files, linked issues
- [ ] Set up language-specific analysis tools

Ensure that the code is ready for analysis. ONLY then proceed to the next step.

### 2. Run Parallel Review Agents

Discover and run available review agents in the project:

```bash
# Check for project-local agents
find .claude/agents -name "*.md" 2>/dev/null

# Check for user-global agents
find ~/.claude/agents -name "*.md" 2>/dev/null
```

For each discovered agent, read its description and launch it against the PR content in parallel. If no custom agents exist, run the built-in agent types:

- **security-sentinel** — Security vulnerabilities, input validation, auth/authz
- **performance-oracle** — Performance bottlenecks, N+1 queries, memory usage
- **code-simplicity-reviewer** — YAGNI violations, unnecessary complexity

Also search `docs/solutions/` (if it exists) for past issues related to this PR's modules and patterns. Flag relevant learnings as "Known Pattern."

#### Conditional: Database Migration Review

If the PR contains database migrations or schema changes:

- Cross-reference schema changes against included migrations to catch unrelated drift
- Validate ID mappings and enum values for correctness
- Check rollback safety
- Create a pre/post-deploy verification checklist

### 3. Deep Dive Analysis

For each phase below, think step by step. Consider all angles. Question assumptions.

#### Stakeholder Perspective Analysis

1. **Developer** — How easy is this to understand and modify? Can I test it easily?
2. **Operations** — How do I deploy this safely? What metrics and logs are available?
3. **End User** — Is the feature intuitive? Are error messages helpful? Is performance acceptable?
4. **Security** — What's the attack surface? How is data protected?

#### Scenario Exploration

- [ ] **Happy Path**: Normal operation with valid inputs
- [ ] **Invalid Inputs**: Null, empty, malformed data
- [ ] **Boundary Conditions**: Min/max values, empty collections
- [ ] **Concurrent Access**: Race conditions, deadlocks
- [ ] **Network Issues**: Timeouts, partial failures
- [ ] **Resource Exhaustion**: Memory, disk, connections
- [ ] **Security Attacks**: Injection, overflow
- [ ] **Data Corruption**: Partial writes, inconsistency
- [ ] **Cascading Failures**: Downstream service issues

### 4. Multi-Angle Review

#### Technical Excellence
- Code craftsmanship evaluation
- Engineering best practices
- Technical documentation quality

#### Business Value
- Feature completeness validation
- Performance impact on users

#### Risk Management
- Security risk assessment
- Operational risk evaluation
- Technical debt accumulation

### 5. Simplification Review

Review the code for unnecessary complexity. Can anything be simplified without losing functionality? Look for YAGNI violations, premature abstractions, and over-engineering.

### 6. Findings Synthesis and Todo Creation

#### Step 1: Synthesize All Findings

- [ ] Collect findings from all parallel agents
- [ ] Categorize by type: security, performance, architecture, quality, etc.
- [ ] Assign severity levels: P1 (Critical), P2 (Important), P3 (Nice-to-have)
- [ ] Remove duplicate or overlapping findings
- [ ] Estimate effort for each finding (Small/Medium/Large)

#### Step 2: Create Todo Files

Create todo files in `todos/` for ALL findings. Use this structure:

**File naming:** `{id}-pending-{priority}-{description}.md`

Examples:
```
001-pending-p1-path-traversal-vulnerability.md
002-pending-p2-missing-index-on-queries.md
003-pending-p3-unused-parameter.md
```

**Each todo file should include:**

```markdown
---
status: pending
priority: p1|p2|p3
tags: [code-review, security|performance|architecture|quality]
---

# [Finding Title]

## Problem Statement
What's broken/missing and why it matters.

## Findings
Discoveries with evidence and file:line locations.

## Proposed Solutions
2-3 options with pros/cons/effort.

## Acceptance Criteria
- [ ] Testable checklist items
```

**Priority values:**
- `p1` — Critical (blocks merge, security/data issues)
- `p2` — Important (should fix, architectural/performance)
- `p3` — Nice-to-have (enhancements, cleanup)

#### Step 3: Summary Report

After creating all todo files, present a comprehensive summary:

```markdown
## Code Review Complete

**Review Target:** PR #XXXX - [PR Title]
**Branch:** [branch-name]

### Findings Summary:
- **Total Findings:** [X]
- **P1 CRITICAL:** [count] - BLOCKS MERGE
- **P2 IMPORTANT:** [count] - Should Fix
- **P3 NICE-TO-HAVE:** [count] - Enhancements

### Created Todo Files:

**P1 - Critical (BLOCKS MERGE):**
- `001-pending-p1-{finding}.md` - {description}

**P2 - Important:**
- `003-pending-p2-{finding}.md` - {description}

**P3 - Nice-to-Have:**
- `005-pending-p3-{finding}.md` - {description}

### Next Steps:

1. **Address P1 Findings** — CRITICAL, must be fixed before merge
2. **Review P2 Findings** — Should be addressed
3. **Work on todos:**
   ```bash
   ls todos/*-pending-*.md  # View all pending todos
   /resolve_todo_parallel   # Fix all items in parallel
   ```
4. **Track Progress** — Rename files when status changes: pending → complete
```

### Important: P1 Findings Block Merge

Any **P1 (CRITICAL)** findings must be addressed before merging the PR. Present these prominently and ensure they're resolved before accepting the PR.
