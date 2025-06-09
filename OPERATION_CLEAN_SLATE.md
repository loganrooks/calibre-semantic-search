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

**Status: ✅ COMPLETE (2025-06-09)**

#### Additional Analysis - Root Directory Cleanup Needed:
Test files scattered in root:
- test_calibre_qt_api.py
- test_config_ui_redesign.py
- test_discovery_integration.py
- test_dynamic_discovery.py
- test_litellm_discovery.py
- test_litellm_models.py
- test_model_info_detailed.py
- test_provider_apis.py
- debug_config_ui.py
- validate_diagnosis.py

Other files needing organization:
- calibre-semantic-search.zip → build/
- calibre-test.log, calibre.log → logs/
- *.json model discovery files → data/ or config/
- embedding_model_discovery_system.py → scripts/

1.  **Establish New Directory Structure:**
    ```bash
    mkdir -p docs/decisions docs/analysis docs/planning
    mkdir -p archive/pre_refactor_$(date +%Y%m%d)
    ```

2.  **Archive All Legacy Documents:** Move all current markdown files and temporary scripts into the dated archive to start fresh.

3.  **Create New Authoritative Documents:** Create fresh, empty versions of all key documents using the templates from the Genesis Document.

4.  **Populate the Knowledge Base:** Use the Genesis Document templates to populate the newly created files.

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