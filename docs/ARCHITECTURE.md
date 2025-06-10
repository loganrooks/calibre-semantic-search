# Calibre Semantic Search: System Architecture
**Version:** 1.0
**Last Updated:** 2025-06-09

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