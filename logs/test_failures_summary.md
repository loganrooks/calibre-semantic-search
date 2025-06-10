# Test Failures Summary

Generated: 2025-06-09 08:03:21

## Overview

- **EPUB Integration**: ❌ FAIL
- **Full Workflow**: ✅ PASS
- **Search Logic**: ✅ PASS
- **Index Management**: ❌ FAIL
- **Calibre Integration**: ❌ FAIL
- **Focus Bug Test**: ❌ FAIL
- **Delayed Init**: ⏰ TIMEOUT
- **Config UI**: ❌ FAIL
- **Cache Unit Tests**: ✅ PASS
- **Vector Ops Unit Tests**: ✅ PASS

## All Detected Failures

- [EPUB Integration] FAILED tests/integration/test_epub_extraction_fix.py::TestEPUBExtractionFix::test_indexing_with_epub
- [Index Management] FAILED tests/ui/test_index_management_ui.py::TestIndexDetectorUI::test_get_index_status_for_multiple_books
- [Index Management] FAILED tests/ui/test_index_management_ui.py::TestIndexDetectorUI::test_index_status_formatting_for_display
- [Index Management] FAILED tests/ui/test_index_management_ui.py::TestIndexDetectorUI::test_index_status_icons
- [Calibre Integration] FAILED tests/ui/test_actual_calibre_integration.py::TestActualCalibreIntegration::test_interface_does_not_import_threaded_job_at_all
- [Focus Bug Test] FAILED tests/ui/test_focus_stealing_bug_BUG_FOCUS_STEAL_20250607.py::TestFocusStealingBug::test_typing_continuous_focus_preservation
- [Focus Bug Test] FAILED tests/ui/test_focus_stealing_bug_BUG_FOCUS_STEAL_20250607.py::TestFocusStealingBug::test_no_qtimer_threading_errors_during_typing
- [Focus Bug Test] FAILED tests/ui/test_focus_stealing_bug_BUG_FOCUS_STEAL_20250607.py::TestFocusStealingBug::test_dropdown_updates_without_focus_interruption
- [Delayed Init] Tests hang during collection/execution
- [Config UI] FAILED tests/ui/test_config_ui_redesign_tdd.py::TestConfigUIRedesign::test_provider_selection_shows_clear_sections
- [Config UI] FAILED tests/ui/test_config_ui_redesign_tdd.py::TestConfigUIRedesign::test_model_selection_is_searchable_with_metadata
- [Config UI] FAILED tests/ui/test_config_ui_redesign_tdd.py::TestConfigUIRedesign::test_progressive_disclosure_hides_complexity

## Detailed Logs

Individual failure logs are available in:
- `cache_unit_tests_failures.log`
- `calibre_integration_failures.log`
- `config_ui_failures.log`
- `delayed_init_failures.log`
- `epub_integration_failures.log`
- `focus_bug_test_failures.log`
- `full_workflow_failures.log`
- `index_management_failures.log`
- `search_logic_failures.log`
- `vector_ops_unit_tests_failures.log`
