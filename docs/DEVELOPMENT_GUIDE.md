# Calibre Semantic Search: Development & Contribution Guide
**Version:** 1.0
**Last Updated:** 2025-06-09

This document contains the core principles, workflows, and patterns for this project. Adherence is mandatory for all contributions.

## 1. The SPARC-V-L³ Development Protocol
Every non-trivial task or bug fix must follow this cycle:
1.  **S - Specification:** Fully understand the goal. Read the task description and any linked documents. If ambiguity exists, ask for clarification *before* proceeding.
2.  **P - Plan:** Create a detailed, step-by-step TDD plan. For new features, this includes TDD test cases. For bugs, this includes the replicating test.
3.  **A - Architecture:** Before writing code, consult `docs/ARCHITECTURE.md`. Identify which components you will modify and analyze the dependency map to understand the impact of your changes. Propose an ADR for any significant changes.
4.  **R - Refine:** Implement the code, following the TDD cycle (Red-Green-Refactor). Ensure all new code adheres to the patterns in this guide.
5.  **C - Complete:** Ensure all new and existing tests pass (`pytest tests/`).
6.  **V - Verify:** Manually test the change in the live Calibre environment using `calibre-debug -g`. Document the verification steps and outcome. This step is mandatory for any user-facing change.
7.  **L¹ - Log Actions:** Update `ACTIVITY_LOG.md` with a detailed record of the work performed.
8.  **L² - Learn (Self-Critique):** Perform a self-analysis of the task execution and log insights into `SELF_ANALYSIS_LOG.md`.
9.  **L³ - Level Up:** If the logs revealed a systemic issue or a new best practice, create a follow-up task to update this `DEVELOPMENT_GUIDE.md` or `ARCHITECTURE.md`.

## 2. The TDD Mandate
*   **For New Features:** No implementation code is written until a failing unit test that defines the feature's behavior has been written and run.
*   **For Bug Fixes (Bug-First TDD):** No fix is applied until a failing test that specifically replicates the bug has been written and run. This test becomes a permanent regression test.

## 3. UI Presentation Patterns (MVP)
*   **View (`config.py`, `search_dialog.py`):** Contains only Qt widget definitions and signal connections. It has setter methods (e.g., `display_results`) and getter methods (e.g., `get_current_query_text`). It knows *nothing* about how to fetch or process data.
*   **Presenter (`presenters/*.py`):** The "brain" of the UI. It is instantiated by the View and given a reference to the View (`presenter = MyPresenter(self)`). It handles all UI events, calls services, processes data, and calls the View's setter methods to update the display. **It must not contain any Qt imports.**

## 4. Version Control: GitFlow & Commit Messages
*   **Branches:**
    *   `main`: Production releases only.
    *   `develop`: Main integration branch. All feature branches merge into `develop`.
    *   `feature/TICKET-123-short-desc`: All new work is done on a feature branch.
*   **Commit Message Format:** Must follow Conventional Commits standard.
    ```
    feat(ui): add dynamic model metadata display
    
    Implements the display of model dimensions and token limits in the
    configuration UI's model selection dropdown. This addresses part of
    the UI Rework Plan.
    
    - Added new labels to ConfigWidget.
    - Updated ConfigPresenter to fetch and format this data.
    
    Refs: #45
    ```

## 5. The Triple-Log System
1.  **Application Log (`plugin.log`):** For runtime debugging. Use Python's `logging` module.
2.  **`ACTIVITY_LOG.md`:** A factual, immutable log of actions taken. Must be appended to at the end of *every* agent response.
3.  **`FEEDBACK_LOG.md` & `SELF_ANALYSIS_LOG.md`:** The engines of the L³/Level-Up cycle. Log all errors, corrections, and insights here.

## 6. Calibre-Specific Code Patterns
*   **Imports:** Always use `from qt.core import ...`. Never import from `PyQt5` or `PyQt6` directly.
*   **Threading:** For background tasks requiring UI updates, use `calibre.gui2.threaded_jobs.ThreadedJob` and the `gui.job_manager`. The function passed to `ThreadedJob` is called with `**kwargs` only, not a job object. State must be passed via the class instance.
*   **Resources:** Store icons in `resources/icons/` and load with `get_icons('my_icon.png')`.
*   **Configuration:** Use `calibre.utils.config.JSONConfig` for all settings persistence.

## 7. Destructive Operations Protocol (NEW)
*   **Before ANY file deletion or modification:**
    1. List what will be affected
    2. Create backup with timestamped directory
    3. Verify backup integrity
    4. Only then proceed with deletion
*   **Example:**
    ```bash
    # Wrong way
    rm -rf docs/*
    
    # Right way
    mkdir -p backup/$(date +%Y%m%d_%H%M%S)
    cp -r docs/* backup/$(date +%Y%m%d_%H%M%S)/
    ls -la backup/$(date +%Y%m%d_%H%M%S)/  # Verify
    # Only now proceed with modifications
    ```