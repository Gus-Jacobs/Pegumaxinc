# Git & Version Control for Internships

*A DevOps-grade, command-line-first course that gets you contributing confidently to a real team's codebase on day one. No GUI crutches—just the Git skills professional workspaces actually expect.*

---

## Module 1: Git Fundamentals & Mental Model
**Build the correct mental model of how Git works so every command afterward makes sense instead of feeling like magic.**

- The three areas: working directory, staging area, and repository (and what `add`/`commit` really do)
- How Git stores history: commits, trees, blobs, and the role of the HEAD pointer
- Configuring your identity, default editor, and global settings on a fresh machine

---

## Module 2: Daily Command-Line Workflow
**Master the everyday commands you'll run dozens of times a day without breaking your flow.**

- The core loop: `status`, `add`, `commit`, `log`, and reading the output fluently
- Inspecting changes with `diff`, `show`, and staged vs. unstaged comparisons
- Undoing safely: `restore`, `reset`, and the difference between discarding and unstaging

---

## Module 3: Clean Branching Workflows
**Use branches the way professional teams do so your work stays isolated, reviewable, and easy to integrate.**

- Branch hygiene: naming conventions, short-lived feature branches, and tracking remotes
- Trunk-based development vs. Git Flow and why most teams favor small, frequent merges
- Keeping a branch current and the lifecycle from creation to merge to cleanup

---

## Module 4: Remote Collaboration & Pull Requests
**Work with shared remotes and the PR process that every team uses to ship code together.**

- `clone`, `fetch`, `pull`, and `push`—and the crucial difference between fetch and pull
- Forks vs. shared-repo workflows and setting upstream tracking branches
- Opening a clean pull request: scope, description, and responding to review feedback

---

## Module 5: Rebase Operations
**Use rebase to keep history linear and readable—the skill that separates interns from contributors.**

- `rebase` vs. `merge`: when each is appropriate and what actually happens to commits
- Interactive rebase (`rebase -i`) to squash, reorder, edit, and drop commits before review
- The golden rule of rebasing shared branches and recovering with `--abort` and reflog

---

## Module 6: Advanced Merge Conflict Resolution
**Resolve conflicts calmly and correctly so an integration mess never blocks you or your team.**

- Anatomy of a conflict: reading conflict markers and understanding the three-way merge
- Resolving from the command line and with merge tools, then verifying the result builds
- Tactics for big conflicts: `rerere`, aborting cleanly, and conflict-minimizing habits

---

## Module 7: Committing Secure Code
**Keep secrets, credentials, and junk out of history—because a leaked key in Git is a real-world incident.**

- Preventing leaks: `.gitignore`, environment files, and never committing secrets or credentials
- Pre-commit hooks and secret-scanning tools that catch mistakes before they're pushed
- Purging sensitive data from history and rotating any credential that was ever committed

---

## Module 8: History Surgery & Recovery
**Rewrite, inspect, and rescue history with confidence so a mistake is never permanent.**

- Fixing commits with `commit --amend`, and moving work with `cherry-pick`
- Finding and recovering "lost" work using `reflog` and resetting to a known-good state
- Hunting regressions efficiently with `git bisect`

---

## Module 9: Stashing, Tagging & Release Hygiene
**Manage in-progress work and mark versions the way professional release workflows require.**

- `stash` for context-switching without losing or committing half-done work
- Semantic versioning with annotated tags and pushing tags to the remote
- Reading and writing useful commit messages and a clean, navigable history

---

## Module 10: Git in the CI/CD Workflow
**See how your commits trigger the automated pipelines that build, test, and deploy real software.**

- How pushes and PRs trigger CI: status checks, required reviews, and branch protection rules
- Reading a failing pipeline and tracing it back to the commit that broke it
- Professional etiquette: keeping `main` green, small reviewable diffs, and good teammate habits

---
