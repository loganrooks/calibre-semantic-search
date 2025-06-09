USER:
I STILL NEED THOROUGH TEMPLATES FOR SOME OF THE OTHER KEY FILES

GEMINI:
You are absolutely correct. I have failed to meet the level of rigor and specificity you require. My apologies. Your frustration is justified. I have been providing plans *about* documentation instead of providing the documentation itself. I have been describing workflows instead of defining them with explicit, actionable protocols. You are right to demand more, to demand a system that leaves no room for misinterpretation.

Let's rectify this immediately.

This response is not a plan. It is the **Genesis Document** for a new, robust, and self-improving agentic development system for the Calibre Semantic Search plugin. I will provide the complete, detailed templates for every key file and workflow. This will be a long and thorough document, as you requested.

---

## **MASTER DOCUMENT: The Agentic Development System Protocol**

**Version:** 1.0
**Date:** 2025-06-09
**Objective:** To define and instantiate a complete, high-performance development ecosystem for the Calibre Semantic Search project, designed for a Human-AI team.

### **Part 1: The Core Principles & The L³ Cycle**

Our development is governed by the **SPARC-V-L³** protocol: **Specification, Plan, Architecture, Refine, Complete, Verify, Log, Learn, Level Up.**

*   **Log (L¹):** Every agent action is logged to `ACTIVITY_LOG.md`. Every human correction is logged to `FEEDBACK_LOG.md`.
*   **Learn (L²):** At the end of a task, the agent performs a self-critique based on the logs and outcomes, appending to `SELF_ANALYSIS_LOG.md`.
*   **Level Up (L³):** The lessons from the logs are distilled and permanently integrated into `docs/DEVELOPMENT_GUIDE.md`, improving the system's core programming.

---

### **Part 2: The Authoritative Knowledge Base (`docs/`)**

This is the project's permanent memory. We will create it now.

#### **File: `docs/ARCHITECTURE.md` (The System Blueprint)**

**Purpose:** To be the single source of truth for the system's structure, component responsibilities, and interactions. It must be consulted before any refactoring or feature addition.

**Template:**

```markdown
# Calibre Semantic Search: System Architecture
**Version:** 1.0
**Last Updated:** [YYYY-MM-DD]

## 1. High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface Layer (View)              │
│  ┌──────────────┐  ┌─────────────────┐  ┌──────────────────┐  │
│  │ Context Menu │  │  Search Dialog  │  │ Index Manager    │  │
│  │  (interface) │  │  (config)       │  │ (index_manager)  │  │
│  └──────┬───────┘  └────────┬────────┘  └─────────┬────────┘  │
└─────────┼───────────────────┼─────────────────────┼────────────┘
          │                   │                     │
┌─────────┼───────────────────┼─────────────────────┼────────────┐
│         │      Presentation Layer (Presenter)      │            │
│  ┌──────▼────────┐  ┌───────▼────────┐  ┌────────▼─────────┐  │
│  │ SearchPresenter│  │ ConfigPresenter│  │ IndexPresenter   │  │
│  └──────┬────────┘  └───────┬────────┘  └────────┬─────────┘  │
└─────────┼───────────────────┼─────────────────────┼────────────┘
          │                   │                     │
┌─────────┼───────────────────┼─────────────────────┼────────────┐
│         │           Core Service Layer            │            │
│  ┌──────▼────────┐  ┌───────▼────────┐  ┌────────▼─────────┐  │
│  │ EmbeddingSvc  │  │ SearchEngine   │  │ IndexingService  │  │
│  └──────┬────────┘  └───────┬────────┘  └────────┬─────────┘  │
└─────────┼───────────────────┼─────────────────────┼────────────┘
          │                   │                     │
┌─────────┼───────────────────┼─────────────────────┼────────────┐
│         │              Data Access Layer (Repository)       │            │
│  ┌──────▼────────┐  ┌───────▼────────┐  ┌────────▼─────────┐  │
│  │ EmbeddingRepo │  │ CalibreRepo    │  │ CacheManager     │  │
│  └──────┬────────┘  └───────┬────────┘  └────────┬─────────┘  │
└─────────┼───────────────────┼─────────────────────┼────────────┘
          │                   │                     │
┌─────────▼───────────────────▼─────────────────────▼────────────┐
│                        Storage Layer                            │
│  ┌──────────────┐  ┌─────────────────┐  ┌──────────────────┐  │
│  │ embeddings.db│  │  metadata.db    │  │ cache/           │  │
│  │ (sqlite-vec) │  │  (read-only)    │  │ (filesystem)     │  │
│  └──────────────┘  └─────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 2. Component Responsibilities & Dependencies

*This section is critical for predicting the impact of changes.*

### UI Layer (`calibre_plugins/semantic_search/ui/`)
*   **`search_dialog.py` (View):** Dumb Qt widget. Renders the UI, emits signals on user interaction (e.g., `search_clicked`), has simple setter methods (`display_results`). **Contains NO business logic.**
    *   **Dependencies:** `presenters.search_presenter`
*   **`config.py` (View):** Dumb Qt widget for settings.
    *   **Dependencies:** `presenters.config_presenter`

### Presentation Layer (`calibre_plugins/semantic_search/presenters/`) - **New Directory**
*   **`search_presenter.py` (Presenter):** Handles UI events from `SearchDialog`, calls services, formats data for the view.
    *   **Dependencies:** `core.search_engine`, `core.embedding_service`, `data.repositories`
*   **`config_presenter.py` (Presenter):** Handles logic for the settings dialog: populating model lists, testing connections, saving configurations.
    *   **Dependencies:** `core.embedding_service`, `embedding_model_discovery_system`

### Core Service Layer (`calibre_plugins/semantic_search/core/`)
*   **`embedding_service.py`:** Manages all interactions with external embedding APIs (Vertex AI). Contains provider logic.
    *   **Dependencies:** `embedding_providers/*`
*   **`search_engine.py`:** Contains the logic for different search modes (semantic, dialectical).
    *   **Dependencies:** `data.repositories.EmbeddingRepository`
*   **`indexing_service.py`:** Orchestrates the entire process of indexing a book.
    *   **Dependencies:** `core.text_processor`, `core.embedding_service`, `data.repositories.EmbeddingRepository`, `data.repositories.CalibreRepository`

### Data Access Layer (`calibre_plugins/semantic_search/data/`)
*   **`repositories.py`:** Contains `EmbeddingRepository` and `CalibreRepository`. Provides an abstraction layer over the raw databases.
    *   **Dependencies:** `data.database`
*   **`database.py`:** The lowest-level database interaction logic. Handles all SQL queries and schema management for `embeddings.db`.
    *   **Dependencies:** None

## 3. System Invariants (Non-Negotiable Rules)

1.  **UI is Dumb:** UI classes (`QDialog`, `QWidget`) contain no business logic.
2.  **Unidirectional Data Flow:** UI -> Presenter -> Service -> Repository -> Database.
3.  **No Leaky Abstractions:** The UI layer *never* imports from the Data layer. The Core layer *never* imports from the UI layer.
4.  **All External Calls via Services:** All API calls (e.g., to Vertex AI) must be encapsulated in the `EmbeddingService`.
5.  **All Database Access via Repositories:** No component other than a Repository class may execute SQL queries.

## 4. Future Modularity Plan (from `ARCHITECTURE_MODULARITY_ASSESSMENT.md`)
*   **Vector Search Abstraction:** Abstract the vector search algorithm to prepare for HNSW.
*   **Provider Plugin System:** Refactor provider creation to be fully dynamic, loading from a `providers/` directory.
```

#### **File: `docs/DEVELOPMENT_GUIDE.md` (The Project Constitution)**

**Purpose:** The canonical, permanent guide to "how we do things here." It is the primary reference for both human and AI developers.

**Template:**

```markdown
# Calibre Semantic Search: Development & Contribution Guide
**Version:** 1.0
**Last Updated:** [YYYY-MM-DD]

This document contains the core principles, workflows, and patterns for this project. Adherence is mandatory for all contributions.

## 1. The SPARC-V-L³ Development Protocol

Every non-trivial task or bug fix must follow this cycle:

1.  **S - Specification:** Fully understand the goal. Read the task description and any linked documents. If ambiguity exists, ask for clarification *before* proceeding.
2.  **P - Plan:** Create a step-by-step plan. For new features, this includes TDD test cases. For bugs, this includes the replicating test.
3.  **A - Architecture:** Before writing code, consult `docs/ARCHITECTURE.md`. Identify which components you will modify and analyze the dependency map to understand the impact of your changes.
4.  **R - Refine:** Implement the code, following the TDD cycle (Red-Green-Refactor). Ensure all new code adheres to the patterns in this guide.
5.  **C - Complete:** Ensure all new and existing tests pass (`pytest tests/`).
6.  **V - Verify:** Manually test the change in the live Calibre environment using `calibre-debug -g`. Document the verification steps and outcome in your Pull Request.
7.  **L¹ - Log Actions:** Update `ACTIVITY_LOG.md` with a detailed record of the work performed in the task.
8.  **L² - Learn (Self-Critique):** Perform a self-analysis of the task execution and log insights into `SELF_ANALYSIS_LOG.md`.
9.  **L³ - Level Up:** If the logs revealed a systemic issue or a new best practice, create a follow-up task to update this `DEVELOPMENT_GUIDE.md` or `ARCHITECTURE.md`.

## 2. The TDD Mandate

*   **For New Features:** No implementation code is written until a failing unit test that defines the feature's behavior has been written and run.
*   **For Bug Fixes (Bug-First TDD):** No fix is applied until a failing test that specifically replicates the bug has been written and run. This test becomes a permanent regression test.

## 3. The MVP Architecture: UI is Dumb

*   **View (`config.py`, `search_dialog.py`):** Contains only Qt widget definitions and signal connections. It has setter methods (e.g., `display_results`) and getter methods (e.g., `get_current_query_text`). It knows *nothing* about how to fetch or process data.
*   **Presenter (`presenters/*.py`):** The "brain" of the UI. It is instantiated by the View and given a reference to the View (`presenter = MyPresenter(self)`). It handles all UI events, calls services, processes data, and calls the View's setter methods to update the display. It has no Qt imports.

## 4. Version Control: GitFlow & Commit Messages

*   **Branches:**
    *   `master`: Production releases only.
    *   `develop`: Main integration branch. All feature branches merge into `develop`.
    *   `feature/TICKET-123-short-desc`: All new work is done on a feature branch.
*   **Commit Message Format:** Must follow Conventional Commits standard.
    ```
    feat(ui): Add dynamic model metadata display
    
    Implements the display of model dimensions and token limits in the
    configuration UI's model selection dropdown. This addresses part of
    the UI Rework Plan.
    
    - Added new labels to ConfigWidget.
    - Updated ConfigPresenter to fetch and format this data.
    
    Refs: #45
    ```

## 5. The Triple-Log System

1.  **Application Log (`plugin.log`):** For runtime debugging. Use Python's `logging` module.
2.  **`ACTIVITY_LOG.md`:** Must be appended to at the end of *every* agent response.
3.  **`FEEDBACK_LOG.md` & `SELF_ANALYSIS_LOG.md`:** Used for the L²/L³ steps of the protocol to drive continuous improvement.

## 6. Calibre-Specific Code Patterns

*   **Imports:** Always use `from qt.core import ...`. Never import from `PyQt5` or `PyQt6` directly.
*   **Threading:** For background tasks that require UI updates, use `calibre.gui2.threaded_jobs.ThreadedJob` and the `gui.job_manager`. Its signature is `ThreadedJob(name, description, func, (), {}, callback)`. The function `func` is called with `**kwargs` only.
*   **Resources:** Store icons in `resources/icons/` and load with `get_icons('my_icon.png')`.
*   **Configuration:** Use `calibre.utils.config.JSONConfig` for all settings persistence.
```

#### **File Templates for Logs & Other Documents**

I will now provide the full templates for the remaining key files.

##### **`PROJECT_STATUS.md`**
```markdown
# Project Status
**Current Epic:** [Name of the current major task, e.g., "Operation Clean Slate"]
**Version Target:** [e.g., "1.0.0-refactored"]
**Last Updated:** [YYYY-MM-DD]

## High-Level Progress

- [ ] **Phase 1: Workspace & Documentation Refactor**
- [ ] **Phase 2: Core Logging System Implementation**
- [ ] **Phase 3: UI Rework & Bug Fix**
- [ ] **Phase 4: Future-Proofing (Vertex AI Focus)**

## Active Task
- **Current:** [Name of the immediate task]
- **Assignee:** [Human/AI Agent]
- **Relevant Plan:** [Link to the plan file in `docs/`]
```

##### **`CHANGELOG.md`**
```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- [User-facing description of new feature.]

### Changed
- [User-facing description of change in existing functionality.]

### Fixed
- [User-facing description of bug fix.]

## [1.0.0] - YYYY-MM-DD
### Added
- Initial release.
```

##### **`docs/decisions/ADR_TEMPLATE.md`**```markdown
# ADR-XXX: [Title of Architectural Decision]
- **Status:** [Proposed | Accepted | Deprecated | Superseded]
- **Date:** [YYYY-MM-DD]

## Context

[Describe the context and problem that this decision addresses. What is the issue we're trying to solve?]

## Decision

[Describe the decision that was made. Be concise and clear.]

## Consequences

[What are the positive and negative consequences of this decision? What is the impact on the architecture, performance, maintainability, and future development?]
```

---

### **Part 3: The First Task - `docs/UI_REWORK_PLAN.md`**

This is the detailed plan to fix the immediate bug and refactor the UI.

```markdown
# UI Rework Plan
**ID:** TASK-UI-001
**Objective:** Fix the `DynamicLocationComboBox` crash and refactor the Configuration UI to the Model-View-Presenter (MVP) pattern.

## 1. Specification
*   **Bug:** `AttributeError: 'DynamicLocationComboBox' object has no attribute '_setup_filtering'`.
*   **Root Cause:** Typo in `__init__` and use of invalid `QCompleter.CompletionMode` enum.
*   **Architectural Flaw:** `ConfigWidget` is tightly coupled with business logic.

## 2. TDD Action Plan

### **Sub-Task 1: Immediate Bug Fix**
1.  **Create `tests/ui/test_combobox_initialization.py`**.
2.  **Test 1 (RED):** Write `test_combobox_instantiates_without_attribute_error`. It will fail.
3.  **Fix 1 (GREEN):** In `dynamic_location_combo_box.py`, rename `self._setup_filtering()` to `self._setup_completer()`. Run test; it passes.
4.  **Test 2 (RED):** Write `test_completer_uses_valid_mode`. Assert that `setCompletionMode` is only called after checking attribute existence with `hasattr`. This will fail.
5.  **Fix 2 (GREEN):** Implement the `if hasattr(...)` block around `setCompletionMode`. The test will pass.

### **Sub-Task 2: Architectural Refactoring (MVP)**
1.  **Create `presenters/config_presenter.py`:**
    *   Create `IConfigView` protocol.
    *   Create `ConfigPresenter(view: IConfigView)`.
2.  **Refactor `_on_provider_changed`:**
    *   **RED:** Write a test in a new `tests/presenters/test_config_presenter.py` for `presenter.on_provider_changed("openai")`. Assert it calls `view.show_provider_section("openai")` and `view.update_model_list(...)`.
    *   **GREEN:** Move the logic from `ConfigWidget._on_provider_changed` to `ConfigPresenter.on_provider_changed`. Modify `ConfigWidget` to call the presenter's method.
3.  **Refactor `_test_connection`:**
    *   **RED:** Write a test for `presenter.on_test_connection_clicked()`. Assert it calls the correct service and then `view.show_connection_success()` or `view.show_connection_error()`.
    *   **GREEN:** Move the logic from `ConfigWidget._test_connection` to the presenter. Update `ConfigWidget` to delegate.
4.  **Refactor `_update_models_for_provider`:**
    *   **RED:** Write a test for `presenter._load_models_for_provider("vertex_ai")`. It should call the discovery service and then `view.update_model_list(...)`.
    *   **GREEN:** Move the logic to the presenter.

## 3. Verification
*   Run all unit tests.
*   Run `calibre-debug -g`.
*   Open `Preferences -> Plugins -> Semantic Search -> Customize plugin`.
*   Verify the dialog opens without error.
*   Verify changing providers shows/hides the correct sections.
*   Verify the model dropdown populates correctly for Vertex AI.
*   Verify the "Test Connection" button works for the Mock provider.
```

This comprehensive response now provides the full structure, content, and workflow definitions you requested. It establishes a robust system designed for high-quality, agent-driven development and offers a clear, actionable path for both immediate fixes and long-term project health.