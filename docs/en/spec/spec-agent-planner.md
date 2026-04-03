<a href="../../ja/spec/spec-agent-planner.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# AI Agent Operations Specification — For Planners

This document defines the rules for AI agents responsible for filing TODOs, creating planning documents, and managing tasks.

## 1. TODO Filing Rules

- Each task requires an `ID` and a context file (`docs/ja/plans/*.md`).
- **Do not write details directly in TODOs. Create the planning document (plans/) first, then link to it from the TODO.**
- The work target is fixed to "the highest-priority incomplete ID (smallest `P<number>`; within the same priority, the first from the top)"; do not proceed to lower priorities without an explicit override instruction.
- If even one `P0` task is incomplete, do not start on `P1` or lower.
- Progress notes and commit messages must always include the same `ID`.
- **When a task is complete, change `[ ]` to `[x]` and add a completion note (e.g., count), then commit.**
- Completed tasks are periodically moved to `docs/ja/todo/archive/`.
- **The completion condition for emitter parity tests is "emit + compile + run + stdout match", not just "emit succeeds".**

## 2. Introducing New Features and Removing Old Ones

- **When creating a task to introduce a new feature, always include a corresponding task to remove the old feature.** Forgetting to remove the old mechanism after introducing a new one leaves the old code behind, causing dual-maintenance and bugs.
- Place the removal task as a sub-task immediately following the introduction task.

## 3. How to Write Planning Documents

- Create under `docs/ja/plans/` with the format `p<N>-<slug>.md`.
- Required sections: Background, Sub-tasks (with IDs), Acceptance criteria, Decision log.
- Explicitly state the target backend (C++, Go, etc.). Vague descriptions like "each emitter" are prohibited.
- Do not forget to add fixtures to `test/`.

## 4. Updating Spec Documents

- After making a design decision, append it to the corresponding `spec/` file before filing a task.
- Rules not written in the spec must not be operated implicitly via TODO comments or code comments.

## 5. Archive Management

- Only incomplete tasks are kept in `docs/ja/todo/index.md`.
- Content that is complete section-by-section is transferred to `docs/ja/todo/archive/index.md` (index) and `docs/ja/todo/archive/YYYYMMDD.md` (content).

## 6. Version Management

- The internal version gate (`transpiler_versions.json`) is obsolete.
- The public release version is managed in `docs/VERSION`. Agents may update `PATCH`. `MAJOR` / `MINOR` updates require an explicit user instruction.
