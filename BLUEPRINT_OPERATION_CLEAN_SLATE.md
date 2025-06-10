## **MASTER BLUEPRINT: OPERATION CLEAN SLATE**

**Version:** 1.0
**Objective:** To refactor the Calibre Semantic Search project and its development process into a high-performance, self-improving, agent-driven ecosystem. This document is the single source of truth for this operation.

### **Part 1: The Agentic Development System Protocol**

This is the constitution of our development process. All actions by any agent MUST adhere to these principles.

#### **Principle 1: The SPARC-V-L³ Cybernetic Loop**
Our development is not a linear process; it is a self-correcting loop. **Specification, Plan, Architecture, Refine, Complete, Verify, Log, Learn, Level Up.**

*   **S**pecification: Fully understand the requirements of the task.
*   **P**lan: Create a detailed, step-by-step TDD plan.
*   **A**rchitecture: Consult `docs/ARCHITECTURE.md` to ensure the plan aligns with the system's design.
*   **R**efine: Implement the code via the Red-Green-Refactor TDD cycle.
*   **C**omplete: All new and existing tests pass.
*   **V**erify: **Manually test the change in the Calibre environment (`calibre-debug -g`).** This step is non-negotiable for any user-facing change.
*   **L¹ - Log:** Log every agent action to `ACTIVITY_LOG.md`. Log every user correction, unexpected error, or deviation from the plan to `FEEDBACK_LOG.md`.
*   **L² - Learn:** At the conclusion of a task, perform a self-critique by analyzing the logs and final outcome. Append insights to `docs/SELF_ANALYSIS_LOG.md`.
*   **L³ - Level Up:** Distill the most critical lessons from the logs into the permanent `docs/DEVELOPMENT_GUIDE.md`, thereby upgrading the agent's core programming for all future tasks.

#### **Principle 2: The Triple-Log System of Record**
This system provides perfect traceability and is the engine for the L³ cycle.

1.  **Application Log (`plugin.log`):** Standard runtime logging from the Python application itself. Answers: *"What did the program do?"*
2.  **`ACTIVITY_LOG.md` (The Agent's Ship's Log):** A high-level, immutable trace of the development process. Answers: *"What did the agent do, and why?"*
3.  **`FEEDBACK_LOG.md` & `SELF_ANALYSIS_LOG.md` (The Learning Logs):** The raw material for self-improvement. Answers: *"What went wrong and what did we learn?"*

---

### **Part 2: The Master Execution Plan**

This is the agent's first epic. It will create a file named `OPERATION_CLEAN_SLATE.md` at the project root and execute the phases within.

**File Content: `OPERATION_CLEAN_SLATE.md`**

```markdown
# MASTER PLAN: OPERATION CLEAN SLATE
**Objective:** To refactor the Calibre Semantic Search codebase and its development environment into a high-performance, self-improving agentic system.

## 1. SITUATION ANALYSIS (The "Why")

The project suffers from architectural debt and a chaotic knowledge base, hindering reliable development. The `COMPLETE_TEST_FAILURES_REPORT.txt` confirms:
*   **Brittle Integrations:** Core functionality like EPUB indexing and Calibre UI integration is broken.
*   **Test Suite Decay:** A significant portion of the test suite is failing, broken, or timed out, indicating issues in both application code and test infrastructure.
*   **Undisciplined Development:** Ad-hoc fixes and TDD violations (e.g., `ThreadedJob` import, focus-stealing bug) have led to regressions and an unstable UI.
*   **Inadequate Systemic Learning:** There is no formal mechanism to capture feedback or perform self-critique, leading to repeated errors.
*   **Documentation Sprawl:** Conflicting, outdated plans make it impossible for an agent to determine the project's true state.

## 2. MISSION (The "What")

1.  **Phase 1: Workspace Refactoring & Knowledge Base Synthesis:** Establish a single source of truth.
2.  **Phase 2: Test Suite Triage and Repair:** Make the test suite a reliable indicator of project health.
3.  **Phase 3: Core System Implementation:** Implement robust logging and fix critical integration bugs.
4.  **Phase 4: Long-Term Refactoring and Evolution:** Chart the course for a modular, maintainable codebase and an ever-improving agentic system.

## 3. EXECUTION PLAN (The "How")

### **Phase 1: Workspace Refactoring & Knowledge Base Synthesis**

1.  **Establish New Directory Structure:**
    ```bash
    mkdir -p docs/decisions docs/analysis docs/planning
    mkdir -p archive/pre_refactor_$(date +%Y%m%d)
    ```

2.  **Archive All Legacy Documents:** Move all current markdown files and temporary scripts into the dated archive to start fresh.
    ```bash
    # Move all .md files (except README.md and this file) and relevant scripts
    # This list is generated from the user-provided file manifest.
    mv BACKUP_PLANS.md CHANGELOG.md CLAUDE.md COMPREHENSIVE_IMPLEMENTATION_PLAN.md \
       DIRECT_VERTEX_AI_INTEGRATION.md DRAFT00.md DRAFT01.md FEEDBACK_LOG.md \
       IMPLEMENTATION_PLAN_2025.md IMPLEMENTATION_QUICK_START.md \
       LITELLM_INTEGRATION_COPILOT.md PROJECT_STATUS.md UI_BACKEND_INTEGRATION_DIAGNOSIS.md \
       validate_diagnosis.py gemini_debug_analysis_20250609_063823.md \
       COMPLETE_TEST_FAILURES_REPORT.txt \
       archive/pre_refactor_$(date +%Y%m%d)/

    # Move all old docs/ and archive/ contents
    mv docs/* archive/pre_refactor_$(date +%Y%m%d)/docs/ 2>/dev/null || true
    mv archive/* archive/pre_refactor_$(date +%Y%m%d)/archive/ 2>/dev/null || true
    rm -rf docs; mkdir -p docs/decisions docs/analysis docs/planning;
    ```

3.  **Create New Authoritative Documents:** Create fresh, empty versions of all key documents using the templates from the Genesis Document.
    ```bash
    touch docs/ARCHITECTURE.md
    touch docs/DEVELOPMENT_GUIDE.md
    touch docs/UI_REWORK_PLAN.md
    touch docs/decisions/ADR_TEMPLATE.md
    touch docs/TEST_SUITE_REPAIR_PLAN.md
    touch ACTIVITY_LOG.md
    touch FEEDBACK_LOG.md
    touch SELF_ANALYSIS_LOG.md
    touch PROJECT_STATUS.md
    touch CLAUDE.md
    touch CHANGELOG.md
    ```

4.  **Populate the Knowledge Base:** Use the Genesis Document templates to populate the newly created files. This is your primary directive for this phase.

5.  **Update `PROJECT_STATUS.md`:** Mark Phase 1 as complete.

### **Phase 2: Test Suite Triage and Repair**
*   **Action:** Execute the detailed plan outlined in `docs/TEST_SUITE_REPAIR_PLAN.md`. The goal is to get the test suite to a state where all failures are expected and meaningful (i.e., pointing to actual bugs or unimplemented features), not due to broken infrastructure.

### **Phase 3: Core System Implementation**
1.  **Implement Core Logging System:**
    *   Create `core/logging_config.py`. Implement a `setup_logging` function using `logging.handlers.RotatingFileHandler`. Log to `plugin_config_dir/logs/plugin.log`.
    *   Integrate into `interface.py`: In `SemanticSearchInterface.genesis()`, make the first call `setup_logging(self.name)`.
    *   Systematically replace all `print()` statements in the application code with appropriate `logger` calls (`logger.info`, `logger.error`, etc.).

2.  **Execute the UI Rework Plan:**
    *   Execute the TDD plan in `docs/UI_REWORK_PLAN.md` to fix the focus-stealing bug and refactor the `ConfigWidget` to the MVP pattern.

### **Phase 4: Long-Term Evolution**
*   This phase is ongoing. The initial tasks are defined in Part 5 of the Genesis Document. The agent will add new tasks to this plan as part of the L³ (Level Up) cycle.
```

---

### **Part 3: The Authoritative Knowledge Base Templates**

This section contains the **complete, final content** for the new authoritative documents.

#### **File: `CLAUDE.md` (The Agent's Prime Directive)**
```markdown
# 🎯 CURRENT TASK: [A clear, one-sentence description of the goal]
- **PLAN:** [Link to the relevant `docs/*.md` plan file, e.g., `docs/TEST_SUITE_REPAIR_PLAN.md`]
- **STATUS:** [e.g., "Phase 1: Writing failing test for EPUB extraction bug"]

---

## 🧠 CORE DIRECTIVES (VERIFY ON EVERY ACTION)

1.  **SPARC-V-L³ Protocol:** You MUST follow the full SPARC-V-L³ cycle for all non-trivial changes as detailed in `docs/DEVELOPMENT_GUIDE.md`.
2.  **TDD is Non-Negotiable:** No implementation without a failing test first. No bug fix without a replicating test first.
3.  **UI is Dumb:** UI classes contain NO business logic. All logic is in Presenters or dedicated modules, as specified in `docs/ARCHITECTURE.md`.
4.  **Verification is Mandatory:** After all tests pass, the final step is ALWAYS to outline the manual `calibre-debug -g` verification steps for any user-facing change.
5.  **Log All Anomalies:** Any deviation from the plan, unexpected error, or user correction MUST be logged with structured detail in `FEEDBACK_LOG.md`.
6.  **Log Your Actions:** At the end of every response, you MUST append a structured entry to `ACTIVITY_LOG.md`.
7.  **Self-Critique:** After completing a significant task, you MUST perform a self-analysis and log it in `SELF_ANALYSIS_LOG.md`.

---

## 📚 KNOWLEDGE BASE INTERACTION PROTOCOL

You are required to read the following documents at specific trigger points to ensure full context:

-   **WHEN:** Starting *any* new task.
    -   **READ:** `docs/DEVELOPMENT_GUIDE.md` to refresh core principles.
    -   **READ:** `docs/ARCHITECTURE.md` to understand the system context.
    -   **READ:** `PROJECT_STATUS.md` to understand the current state of the epic.

-   **WHEN:** Implementing a UI change.
    -   **READ:** The "UI Presentation Patterns (MVP)" section in `docs/DEVELOPMENT_GUIDE.md`.
    -   **READ:** The relevant component diagram in `docs/ARCHITECTURE.md`.

-   **WHEN:** Modifying the database or repository layer.
    -   **READ:** The "Data Layer & Repository Pattern" section in `docs/DEVELOPMENT_GUIDE.md`.

-   **WHEN:** A significant architectural decision is needed.
    -   **ACTION:** Propose a new Architecture Decision Record (ADR) in `docs/decisions/` using the template. Do not proceed until the ADR is approved.

-   **WHEN:** A task is complete.
    -   **ACTION:** Propose updates to `CHANGELOG.md`.
    -   **ACTION:** Propose updates to `PROJECT_STATUS.md`.
    -   **ACTION:** Perform L² (Learn) step and update `SELF_ANALYSIS_LOG.md`.
    -   **ACTION:** If a systemic lesson was learned, perform L³ (Level Up) step by creating a task to update the `DEVELOPMENT_GUIDE.md`.
```

#### **File: `docs/ARCHITECTURE.md` (The System Blueprint)**
*(This combines the best from the drafts and adds more detail)*
```markdown
# Calibre Semantic Search: System Architecture
**Version:** 1.0
**Last Updated:** [YYYY-MM-DD]

## 1. High-Level Architecture Diagram (MVP Pattern)

The system follows a Model-View-Presenter (MVP) pattern for the UI, with a clear separation of concerns into layers.

```
┌─────────────────────────────────────────────────────────────────┐
│                 User Interface Layer (The "View")               │
│      (Dumb Qt Widgets: config.py, search_dialog.py, etc.)       │
└─────────────────────────────────▲───────────────────────────────┘
                                  │ (Updates View)
                                  │
┌─────────────────────────────────┼───────────────────────────────┐
│               Presentation Layer (The "Presenter")              │
│ (Handles UI logic, no Qt imports: config_presenter.py, etc.)    │
└─────────────────────────────────│───────────────────────────────┘
                    (Calls Services)│
┌─────────────────────────────────▼───────────────────────────────┐
│                        Core Service Layer                       │
│ (Business Logic: indexing_service.py, search_engine.py, etc.)   │
└─────────────────────────────────│───────────────────────────────┘
                (Accesses Data via) │
┌─────────────────────────────────▼───────────────────────────────┐
│              Data Access Layer (The "Repository")               │
│  (Abstracts DB access: repositories.py, database.py, cache.py)  │
└─────────────────────────────────│───────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────┐
│                           Storage Layer                         │
│       (SQLite DB, sqlite-vec, Filesystem, API Endpoints)        │
└─────────────────────────────────────────────────────────────────┘
```

## 2. Component Responsibilities & Dependencies

*This section is critical for predicting the impact of changes.*

### UI Layer (`calibre_plugins/semantic_search/ui/`)
*   **Purpose:** To render the UI and emit signals on user interaction. It is "Dumb" and contains **NO business logic.**
*   **Components:** `config.py`, `search_dialog.py`, `index_manager_dialog.py`.
*   **Dependencies:** `presenters/*`. MUST NOT depend on `core` or `data` layers.

### Presentation Layer (`calibre_plugins/semantic_search/presenters/`) - **New Directory**
*   **Purpose:** To act as the "brain" of the UI. It responds to UI signals, calls services, formats data, and updates the View. Contains **NO Qt imports.**
*   **Components:** `config_presenter.py`, `search_presenter.py`.
*   **Dependencies:** `core/*`, `data/*` (for passing to services).

### Core Service Layer (`calibre_plugins/semantic_search/core/`)
*   **Purpose:** To implement the core business logic of the application.
*   **Components:**
    *   `embedding_service.py`: Manages all interactions with external embedding APIs.
    *   `indexing_service.py`: Orchestrates the book indexing workflow.
    *   `search_engine.py`: Implements the different search algorithms.
    *   `text_processor.py`: Handles text extraction and chunking.
*   **Dependencies:** `data/*`.

### Data Access Layer (`calibre_plugins/semantic_search/data/`)
*   **Purpose:** To provide a clean, abstract API for data storage and retrieval. This is the ONLY layer that should contain SQL.
*   **Components:**
    *   `repositories.py`: `EmbeddingRepository` and `CalibreRepository`.
    *   `database.py`: Low-level SQLite and `sqlite-vec` interaction logic.
    *   `cache.py`: Caching logic for API calls and results.
*   **Dependencies:** None outside this layer.

## 3. System Invariants (Non-Negotiable Rules)

1.  **UI is Dumb:** All UI logic resides in Presenters. Views only emit signals and have simple setter methods.
2.  **Unidirectional Dependencies:** UI -> Presenter -> Service -> Repository. A layer can only depend on layers below it.
3.  **No Leaky Abstractions:** The UI layer *never* imports from the Data layer.
4.  **All External Calls via Services:** All API calls (e.g., to Vertex AI) must be encapsulated in the `EmbeddingService`.
5.  **All Database Access via Repositories:** No component other than a Repository class may execute SQL queries.
6.  **Calibre Imports are Restricted:** Only `interface.py` and `config.py` should import from `calibre.gui2`. Other modules should import from `qt.core` or receive Calibre objects via dependency injection.
```

#### **File: `docs/DEVELOPMENT_GUIDE.md` (The Project Constitution)**
*(This is a more detailed version combining the best of the drafts)*
```markdown
# Calibre Semantic Search: Development & Contribution Guide
**Version:** 1.0
**Last Updated:** [YYYY-MM-DD]

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
```

#### **Templates for Other Key Files**
*   **`ACTIVITY_LOG.md`:** Must be appended to after every turn.
    ```markdown
    ### [Timestamp: YYYY-MM-DD-HHMMSS] - [Task ID/Name]
    *   **Goal:** [Brief description of the objective for this step]
    *   **Analysis:** [Summary of files read, logic considered, and plan formulated]
    *   **Actions:** [Bulleted list of `read`, `write`, `run` commands executed]
    *   **Rationale:** [Brief explanation for the chosen approach]
    ```
*   **`FEEDBACK_LOG.md`:** For logging all errors and corrections.
    ```markdown
    ### [Timestamp] - [Error Type] - [Severity: LOW/MEDIUM/HIGH/CRITICAL]
    **Context:** [What was being worked on]
    **The Mistake:** [What went wrong, including specific error messages]
    **User Interruption/Correction:** [What the user had to say or do to correct the mistake]
    **Root Cause Analysis:** [Why the mistake happened (e.g., "Assumed API without verification," "Failed to read test logs carefully")]
    **The Lesson:** [What should be done differently next time]
    **Systemic Prevention:** [A concrete suggestion for a change to `DEVELOPMENT_GUIDE.md` to prevent this class of error in the future]
    ```
*   **`PROJECT_STATUS.md`:** A simple, high-level checklist of the current epic's phases.
*   **`CHANGELOG.md`:** Standard "Keep a Changelog" format. Entries should be user-focused.

---

### **Part 4: Test Suite Triage and Repair Plan**

This plan will be created as `docs/TEST_SUITE_REPAIR_PLAN.md` and executed in Phase 2.

| Failure Category | Test Location | Root Cause Analysis | Proposed Fix | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **EPUB INTEGRATION** | `test_epub_extraction_fix.py` | The log shows `Error indexing book 1: object Mock can't be used in 'await' expression`. This is a classic async mocking error. The `embedding_service` mock is a standard `Mock()`, which is not awaitable. | Replace `Mock()` with `unittest.mock.AsyncMock`. The `generate_embedding` method on the mock needs to be an `async def` function or another `AsyncMock`. | **CRITICAL** |
| **INDEX MANAGEMENT** | `test_index_management_ui.py` | `ModuleNotFoundError: No module named 'calibre_plugins.semantic_search.ui.index_detector'`. The file `index_detector.py` has likely been moved, renamed, or was never created. | **1.** Search the codebase for `IndexDetector`. **2.** If found, correct the import path in the test. **3.** If not found, create the file `calibre_plugins/semantic_search/ui/index_detector.py` with placeholder content based on the test's expectations. | **HIGH** |
| **CALIBRE INTEGRATION** | `test_actual_calibre_integration.py` | `AssertionError: interface.py still imports ThreadedJob`. The test explicitly forbids this import to prevent Calibre-specific errors, but the import (likely inside a `try/except` block) still exists. | Edit `calibre_plugins/semantic_search/interface.py` and remove the line `from calibre.gui2.threaded_jobs import ThreadedJob`. All threading should be handled via the established `BackgroundJobManager`. | **HIGH** |
| **FOCUS BUG** | `test_focus_stealing_bug_...` | These are *expected failures* designed to replicate a known bug. The `AssertionError` confirms the focus is being stolen, and the `StopIteration`/`RuntimeError` indicates a complex mock/fixture setup issue or an underlying problem in the `DynamicLocationComboBox` constructor. | This isn't a test fix, but an application fix. Create a detailed TDD sub-plan (`docs/UI_REWORK_PLAN.md`) to refactor `DynamicLocationComboBox` and `ConfigWidget` to the MVP pattern, which will resolve the focus and threading issues. | **HIGH** |
| **CONFIG UI** | `test_config_ui_redesign_tdd.py` | These are `assert False` placeholders. They are TDD stubs for features that have not been implemented yet. | These are not "fixes" but "implementations". Use the test descriptions as specifications to build the required UI features (provider-specific sections, searchable model dropdowns). | **MEDIUM** |
| **DELAYED INIT** | `test_delayed_initialization.py` | **TIMEOUT**. The test collection hangs. The report correctly identifies this is likely a premature Qt/GUI initialization issue in a non-GUI test runner. The test is likely importing a Qt-dependent module at the top level. | **1.** Analyze `test_delayed_initialization.py` for top-level Qt imports. **2.** Refactor the test to import Qt-dependent modules *inside* the test functions. **3.** If necessary, use `pytest-qt` fixtures like `qtbot` to manage the Qt event loop correctly. | **LOW** |

---

### **Part 5: Long-Term Codebase and System Evolution Plan**

This plan outlines the next steps *after* Operation Clean Slate is complete, ensuring continuous improvement.

#### **A. Codebase Refactoring Roadmap**

1.  **Decouple `repositories.py`:** This file is too large. Split `EmbeddingRepository` and `CalibreRepository` into their own files within the `data/` directory (`data/embedding_repository.py`, `data/calibre_repository.py`).
2.  **Centralize Error Handling:** Create a new `core/exceptions.py` file. Define custom, specific exceptions (e.g., `IndexingError`, `EmbeddingProviderError`, `ConfigurationError`) to provide more structured error handling than generic `Exception`.
3.  **Implement a True Provider Plugin System:** The current `create_embedding_service` is a factory, not a plugin system. Refactor `embedding_service.py` to dynamically load provider plugins from a dedicated `embedding_providers/` directory. `direct_vertex_ai.py` will be the first official plugin.
4.  **Refactor `config.py`:** The `ConfigWidget` is still a monolith. Use the Presenter pattern fully by moving all logic (e.g., `_update_models_for_provider`, `_validate_provider_config`) into `presenters/config_presenter.py`. The `ConfigWidget` should only handle UI elements and signal connections.

#### **B. Agentic System Evolution**

1.  **Automated L³ "Level Up" Task:** A recurring task will be created for the agent to review `FEEDBACK_LOG.md` and `SELF_ANALYSIS_LOG.md`. The agent's goal will be to identify recurring error patterns and propose concrete changes to `docs/DEVELOPMENT_GUIDE.md` to prevent them. This makes the self-improvement loop an explicit, actionable part of the development process.
2.  **Context Management Enhancement:** The agent will be tasked with developing a `context_builder.py` script. This script will read the current task from `CLAUDE.md`, and based on keywords (e.g., "UI", "database", "indexing"), it will automatically concatenate the most relevant files (`ARCHITECTURE.md`, `DEVELOPMENT_GUIDE.md`, and specific source files) into a single context file for the next agent session. This automates and optimizes context-gathering.
3.  **Expansion of the Development Guide:** The agent will be tasked with adding new sections to `docs/DEVELOPMENT_GUIDE.md` over time, including:
    *   A detailed "Cookbook" of common Calibre plugin development recipes.
    *   A section on performance profiling and optimization techniques.
    *   A guide to debugging and interpreting Calibre's specific error messages.