# 🎯 CURRENT TASK: Execute BLUEPRINT OPERATION CLEAN SLATE - Phase 1 Workspace Refactoring
- **PLAN:** BLUEPRINT_OPERATION_CLEAN_SLATE.md
- **STATUS:** Phase 1: Creating authoritative knowledge base after initial file organization

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

## 🔄 CONTEXT INITIALIZATION PROTOCOL (CRITICAL)

**MANDATORY:** Execute this protocol at the start of EVERY conversation and whenever context may have been compacted/refreshed.

### Context Refresh Detection Triggers:
- Beginning of any new conversation
- When you cannot recall recent task details or decisions
- When foundational documents (DEVELOPMENT_GUIDE.md, ARCHITECTURE.md) are not in working memory
- When architectural patterns or coding standards are unclear

### IMMEDIATE INITIALIZATION SEQUENCE:
1. **ALWAYS READ FIRST:** 
   - `docs/DEVELOPMENT_GUIDE.md` - Core principles, patterns, and methodologies
   - `docs/ARCHITECTURE.md` - System design and component relationships  
   - `PROJECT_STATUS.md` - Current epic state and progress
   - `FEEDBACK_LOG.md` - Recent lessons and workflow decisions

2. **VERIFY UNDERSTANDING:**
   - MVP pattern requirements (UI is dumb, logic in presenters)
   - TDD methodology (failing test first, no implementation without tests)
   - SPARC-V-L³ protocol compliance
   - Git workflow decisions (PR vs direct merge based on context)

3. **LOAD PROJECT CONTEXT:**
   - Current task status and priorities
   - Recent architectural decisions and patterns
   - Active issues and their resolution approaches

**NEVER SKIP THIS PROTOCOL** - Inconsistent decisions result from missing foundational context.

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

---

## 🚨 LESSONS FROM INITIAL ATTEMPT

1. **ALWAYS** verify backups before destructive operations
2. **READ** and understand existing structure before reorganizing
3. **THINK** ultra hard before executing commands
4. **PRESERVE** valuable documentation while establishing new standards

---

## 🔀 GIT WORKFLOW DECISION MATRIX

**CRITICAL:** Consider project context before suggesting git workflows. Avoid defaulting to enterprise patterns.

### Use DIRECT MERGE (git merge --no-ff) when:
- ✅ Solo development project
- ✅ Merging to non-production branch (develop)
- ✅ Code is well-tested and verified
- ✅ Changes are focused and well-documented
- ✅ Overhead of PR process isn't justified

### Use PULL REQUEST workflow when:
- 🔄 Major architectural changes requiring discussion
- 🔄 External contributions from other developers
- 🔄 Seeking explicit code review and feedback
- 🔄 Merging to production/master branch
- 🔄 Complex changes that benefit from CI/CD validation

### Decision Factors:
- **Project size:** Solo vs team development
- **Branch criticality:** develop vs master/production
- **Change complexity:** Simple fix vs architectural change
- **Testing coverage:** Well-tested vs needs validation
- **Review needs:** Self-sufficient vs requires discussion

**Default for this project:** Direct merge to develop for tested fixes, PR only for major changes or external contributions.