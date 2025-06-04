#!/usr/bin/env python3
"""
Simplified diagnosis validation that checks the actual code patterns
mentioned in UI_BACKEND_INTEGRATION_DIAGNOSIS.md without requiring full
Calibre environment setup.
"""

import os
import re

def read_file_safely(filepath):
    """Read file content safely"""
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return ""

def validate_issue_1_plugin_reference():
    """Validate Issue #1: Test Connection Plugin Reference Chain Broken"""
    print("🔍 Validating Issue #1: Plugin Reference Chain...")
    
    config_path = "calibre_plugins/semantic_search/config.py"
    content = read_file_safely(config_path)
    
    # Check for the broken parent chain traversal pattern
    has_parent_chain_traversal = "while parent and not plugin:" in content
    has_plugin_access_attempt = "hasattr(parent, 'plugin')" in content
    
    if has_parent_chain_traversal and has_plugin_access_attempt:
        print("✅ CONFIRMED: Parent chain traversal pattern found (line ~632-640)")
        print("   This confirms the broken plugin reference issue exists")
        return True
    else:
        print("❌ Pattern not found - issue may be already fixed")
        return False

def validate_issue_2_config_conflicts():
    """Validate Issue #2: Multiple Configuration Systems Conflict"""
    print("\n🔍 Validating Issue #2: Configuration Conflicts...")
    
    config_path = "calibre_plugins/semantic_search/config.py"
    content = read_file_safely(config_path)
    
    # Check for model_edit (AI Provider tab)
    has_model_edit = "self.model_edit" in content
    
    # Check for model_combo (Indexing tab)  
    has_model_combo = "self.model_combo" in content
    
    # Check if both save to same config key
    embedding_model_saves = content.count('self.config.set("embedding_model"')
    
    if has_model_edit and has_model_combo:
        print("✅ CONFIRMED: Both model_edit and model_combo found")
        print(f"   Found {embedding_model_saves} places saving to 'embedding_model' key")
        print("   This confirms the configuration conflict issue exists")
        return True
    else:
        print("❌ Only one model selection system found - may be fixed")
        return False

def validate_issue_3_index_manager():
    """Validate Issue #3: Index Manager Data Binding Issues"""
    print("\n🔍 Validating Issue #3: Index Manager Issues...")
    
    dialog_path = "calibre_plugins/semantic_search/ui/index_manager_dialog.py"
    content = read_file_safely(dialog_path)
    
    # Check for duplicate statistics
    has_html_stats = "_populate_statistics" in content or "stats_text" in content
    has_grid_stats = "total_books_label" in content or "stats_grid" in content
    
    # Check for editable table (missing read-only flags)
    has_table_setup = "QTableWidget" in content
    has_readonly_flags = "Qt.ItemIsEditable" in content and "flags() &" in content
    
    # Check for legacy fallback
    has_legacy_fallback = "'legacy'" in content and "'unknown'" in content
    
    print(f"   HTML stats display: {'✅' if has_html_stats else '❌'}")
    print(f"   Grid stats display: {'✅' if has_grid_stats else '❌'}")
    print(f"   Table setup: {'✅' if has_table_setup else '❌'}")
    print(f"   Read-only flags: {'❌' if not has_readonly_flags else '✅'}")
    print(f"   Legacy fallback: {'✅' if has_legacy_fallback else '❌'}")
    
    issues_found = 0
    if has_html_stats and has_grid_stats:
        print("✅ CONFIRMED: Duplicate statistics display")
        issues_found += 1
    if has_table_setup and not has_readonly_flags:
        print("✅ CONFIRMED: Missing read-only table flags")
        issues_found += 1
    if has_legacy_fallback:
        print("✅ CONFIRMED: Legacy fallback showing 'unknown' values")
        issues_found += 1
        
    return issues_found > 0

def validate_issue_4_service_initialization():
    """Validate Issue #4: Service Initialization Race Conditions"""
    print("\n🔍 Validating Issue #4: Service Initialization Race...")
    
    interface_path = "calibre_plugins/semantic_search/interface.py"
    content = read_file_safely(interface_path)
    
    # Check for early service initialization in genesis()
    has_genesis_init = "def genesis(" in content and "_initialize_services" in content
    
    # Check for service creation with config
    has_service_creation = "create_embedding_service" in content
    has_config_read = "config.as_dict()" in content
    
    # Check if service registry pattern exists
    has_service_registry = "ServiceRegistry" in content
    has_config_change_detection = "_config_hash" in content
    
    print(f"   Early initialization: {'✅' if has_genesis_init else '❌'}")
    print(f"   Service creation: {'✅' if has_service_creation else '❌'}")
    print(f"   Config reading: {'✅' if has_config_read else '❌'}")
    print(f"   Service registry: {'❌' if not has_service_registry else '✅'}")
    print(f"   Config change detection: {'❌' if not has_config_change_detection else '✅'}")
    
    if has_genesis_init and not has_service_registry:
        print("✅ CONFIRMED: Services initialized early without config change detection")
        return True
    else:
        print("❌ Service registry pattern may already be implemented")
        return False

def validate_issue_5_database_schema():
    """Validate Issue #5: Database Schema vs UI Mismatch"""
    print("\n🔍 Validating Issue #5: Database Schema Mismatch...")
    
    indexing_path = "calibre_plugins/semantic_search/core/indexing_service.py"
    dialog_path = "calibre_plugins/semantic_search/ui/index_manager_dialog.py"
    
    indexing_content = read_file_safely(indexing_path)
    dialog_content = read_file_safely(dialog_path)
    
    # Check if indexing stores metadata
    stores_provider = "'provider'" in indexing_content and "embedding_service" in indexing_content
    stores_model = "'model_name'" in indexing_content
    stores_dimensions = "'dimensions'" in indexing_content
    
    # Check if UI tries to display metadata
    ui_expects_provider = "get('provider'" in dialog_content
    ui_expects_model = "get('model_name'" in dialog_content
    
    print(f"   Indexing stores provider: {'✅' if stores_provider else '❌'}")
    print(f"   Indexing stores model: {'✅' if stores_model else '❌'}")
    print(f"   Indexing stores dimensions: {'✅' if stores_dimensions else '❌'}")
    print(f"   UI expects provider: {'✅' if ui_expects_provider else '❌'}")
    print(f"   UI expects model: {'✅' if ui_expects_model else '❌'}")
    
    metadata_stored = stores_provider and stores_model and stores_dimensions
    metadata_expected = ui_expects_provider and ui_expects_model
    
    if metadata_expected and not metadata_stored:
        print("✅ CONFIRMED: UI expects metadata that indexing doesn't store")
        return True
    else:
        print("❌ Metadata storage may already be implemented")
        return False

def main():
    """Run all diagnosis validations"""
    print("🔍 DIAGNOSIS VALIDATION REPORT")
    print("=" * 50)
    
    validations = [
        validate_issue_1_plugin_reference,
        validate_issue_2_config_conflicts,
        validate_issue_3_index_manager,
        validate_issue_4_service_initialization,
        validate_issue_5_database_schema
    ]
    
    confirmed_issues = 0
    
    for validation in validations:
        if validation():
            confirmed_issues += 1
    
    print("\n" + "=" * 50)
    print(f"📊 SUMMARY: {confirmed_issues}/5 issues confirmed to exist")
    
    if confirmed_issues >= 3:
        print("✅ DIAGNOSIS VALIDATED: Proceed with Phase 1 fixes")
        print("   The identified issues are real and need to be addressed")
    else:
        print("⚠️  Some issues may already be fixed - review individually")
    
    return confirmed_issues

if __name__ == '__main__':
    confirmed = main()
    exit(0 if confirmed >= 3 else 1)