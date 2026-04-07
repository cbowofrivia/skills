---
name: create-pr
description: Create a GitHub pull request with correct labels, filled template, and consistent formatting
argument-hint: '[optional: base branch, default: main]'
---

# /create-pr

Create a GitHub pull request for the current branch. Analyzes all commits, fills the PR template, selects the correct label, and returns the PR URL.

## Prerequisites

- Must be on a feature/fix branch (not `main`)
- `gh` CLI must be authenticated
- Branch must have commits ahead of the base branch

## Steps

Follow these steps in order. Do not skip any.

### 1. Validate State

<sequential_tasks>

- [ ] Confirm the current branch is NOT `main`. If it is, stop and tell the user.
- [ ] Set `BASE_BRANCH` to `$ARGUMENTS` if provided, otherwise `main`.
- [ ] Check if a PR already exists for this branch: `gh pr view --json url,state 2>/dev/null`. If a PR exists and is open, show the URL and ask if the user wants to update it. If merged/closed, note it and proceed to create a new one if the user confirms.

</sequential_tasks>

### 2. Gather Context

Run these commands to understand what this PR contains. All four are independent — run them in parallel:

- `git log $BASE_BRANCH..HEAD --oneline` — all commits on this branch
- `git diff $BASE_BRANCH...HEAD --stat` — files changed summary
- `git diff $BASE_BRANCH...HEAD` — full diff for analysis
- `cat .github/PULL_REQUEST_TEMPLATE.md` — the PR template (use its sections and HTML comment hints as your guide for what to fill in)

Then check if the branch is pushed: `git rev-parse --abbrev-ref @{upstream} 2>/dev/null`. If not pushed, push with `git push -u origin HEAD`.

### 3. Analyze & Draft

Analyze ALL commits and the full diff (not just the latest commit). Use the PR template from Step 2 as the structure — fill in every section using the HTML comment hints as guidance for what each section expects.

Draft a **Title**: short (under 70 characters), following conventional commit style from the branch commits. Example: `fix(artwork): cancel orphaned generations after account deletion`.

Write **User Impact** from the user's perspective ("Users can now..." / "Players will see..."), not the developer's. For internal-only changes, write "None — internal only."

If a section has nothing meaningful to add (e.g., Notes when there are no migration steps or deployment concerns), omit that section entirely rather than leaving placeholder text.

### 4. Select Labels

<sequential_tasks>

- [ ] Discover available labels: `gh label list --limit 100`
- [ ] Based on the PR's content, select the label(s) that best describe it from the available labels. Apply one or more as appropriate — use your judgment.
- [ ] If no existing label fits well, create one: `gh label create "<name>" --description "<description>" --color "<hex>"`. Use lowercase kebab-case names and pick a color that doesn't clash with existing labels. Only create a label if the PR genuinely represents a category not covered by existing labels.

</sequential_tasks>

**Guidance for label selection:**

- Bug fixes → look for a bug/fix/hotfix label
- New features → look for a feature/enhancement label
- Performance work → look for a performance label
- Breaking changes → should always be labeled as such if a label exists
- Documentation-only → documentation label
- Dependency updates → dependencies label
- Internal refactors, CI, tests → look for an internal/chore label, or no label if none fits

### 5. Create the Pull Request

<sequential_tasks>

- [ ] Build the PR body by filling in the template from Step 2. Replace every HTML comment with real content. Use a HEREDOC for correct formatting.
- [ ] Create the PR with `gh pr create`:
  - `--base "$BASE_BRANCH"`
  - `--title "$TITLE"`
  - `--label "$LABEL1" --label "$LABEL2"` (for each label, or omit `--label` entirely if none apply)
  - `--body` with the filled template via HEREDOC
- [ ] If the Type is a breaking change, make sure this is noted prominently in the body (what breaks and the migration path).

</sequential_tasks>

### 6. Confirm

- [ ] Output the PR URL to the user.
- [ ] Show a brief summary: title, labels applied, base branch.

## Common Mistakes to Avoid

| Mistake                                    | Correct Approach                                                                       |
| ------------------------------------------ | -------------------------------------------------------------------------------------- |
| Only reading the latest commit             | Read ALL commits with `git log $BASE_BRANCH..HEAD`                                     |
| Hardcoding or guessing labels              | Discover labels with `gh label list` first                                             |
| Leaving template sections as HTML comments | Fill in every section with real content                                                |
| Writing User Impact from dev perspective   | Write from the user's perspective: "Users can now..." not "Added a controller that..." |
| Creating PR without pushing branch         | Always check and push first                                                            |
| Hardcoding the PR body structure           | Read `.github/PULL_REQUEST_TEMPLATE.md` and use it as the structure                    |
