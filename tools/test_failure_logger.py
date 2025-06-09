#!/usr/bin/env python3
"""
Comprehensive Test Failure Logger
Captures all test failures with detailed output for debugging
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime

def run_test_category(test_path, category_name, output_dir):
    """Run tests and capture all failures"""
    print(f"📋 Documenting {category_name}...")
    
    log_file = output_dir / f"{category_name.lower().replace(' ', '_')}_failures.log"
    
    try:
        # Run with timeout to prevent hanging
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            test_path,
            "--tb=long",          # Full traceback
            "--verbose",          # Verbose output
            "--no-header",        # Cleaner output
            "--disable-warnings", # Focus on actual failures
            "--maxfail=3"         # Stop after 3 failures
        ], 
        capture_output=True, 
        text=True, 
        timeout=30,  # 30 second timeout per category
        cwd=Path(__file__).parent.parent
        )
        
        # Write full output to log file
        with open(log_file, 'w') as f:
            f.write(f"=== {category_name} TEST FAILURES ===\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Test Path: {test_path}\n")
            f.write(f"Return Code: {result.returncode}\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("STDOUT:\n")
            f.write("-" * 40 + "\n")
            f.write(result.stdout)
            f.write("\n\n")
            
            f.write("STDERR:\n") 
            f.write("-" * 40 + "\n")
            f.write(result.stderr)
            f.write("\n")
        
        # Return summary for overview
        if result.returncode == 0:
            return "✅ PASS", None
        else:
            # Extract failure summary
            lines = result.stdout.split('\n')
            failures = [line for line in lines if 'FAILED' in line and '::' in line]
            error_lines = [line for line in lines if 'ERROR' in line and '::' in line]
            
            issues = failures + error_lines
            return "❌ FAIL", issues[:3]  # First 3 issues for overview
            
    except subprocess.TimeoutExpired:
        with open(log_file, 'w') as f:
            f.write(f"=== {category_name} TEST FAILURES ===\n")
            f.write(f"TIMEOUT: Tests hung for >30 seconds\n")
            f.write(f"This indicates pytest collection or execution is hanging\n")
        return "⏰ TIMEOUT", ["Tests hang during collection/execution"]
        
    except Exception as e:
        with open(log_file, 'w') as f:
            f.write(f"=== {category_name} TEST FAILURES ===\n")
            f.write(f"EXCEPTION: {str(e)}\n")
        return "⚠️ ERROR", [str(e)]

def main():
    """Document all test failures comprehensively"""
    print("🔍 Comprehensive Test Failure Documentation")
    print("=" * 60)
    
    # Create output directory
    output_dir = Path(__file__).parent.parent / "logs"
    output_dir.mkdir(exist_ok=True)
    
    # Clean old logs
    for old_log in output_dir.glob("*_failures.log"):
        old_log.unlink()
    
    # Test categories to document - focusing on specific files to avoid hanging
    test_categories = [
        # Specific failing files we know about
        ("tests/integration/test_epub_extraction_fix.py", "EPUB Integration"),
        ("tests/integration/test_full_workflow.py", "Full Workflow"),
        ("tests/ui/test_search_business_logic.py", "Search Logic"),
        ("tests/ui/test_index_management_ui.py", "Index Management"),
        ("tests/ui/test_actual_calibre_integration.py", "Calibre Integration"),
        ("tests/ui/test_focus_stealing_bug_BUG_FOCUS_STEAL_20250607.py", "Focus Bug Test"),
        ("tests/integration/test_delayed_initialization.py", "Delayed Init"),
        ("tests/ui/test_config_ui_redesign_tdd.py", "Config UI"),
        # Sample of unit tests that should work
        ("tests/unit/test_cache.py", "Cache Unit Tests"),
        ("tests/unit/test_vector_ops.py", "Vector Ops Unit Tests"),
    ]
    
    results = {}
    all_failures = []
    
    for test_path, category_name in test_categories:
        full_path = Path(__file__).parent.parent / test_path
        if full_path.exists():
            status, issues = run_test_category(test_path, category_name, output_dir)
            results[category_name] = status
            
            if issues:
                all_failures.extend([f"[{category_name}] {issue}" for issue in issues])
        else:
            results[category_name] = "⚠️ MISSING"
    
    # Create master summary
    summary_file = output_dir / "test_failures_summary.md"
    with open(summary_file, 'w') as f:
        f.write("# Test Failures Summary\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Overview\n\n")
        for category, status in results.items():
            f.write(f"- **{category}**: {status}\n")
        
        f.write("\n## All Detected Failures\n\n")
        if all_failures:
            for failure in all_failures:
                f.write(f"- {failure}\n")
        else:
            f.write("No failures detected in sampled tests.\n")
        
        f.write("\n## Detailed Logs\n\n")
        f.write("Individual failure logs are available in:\n")
        for log_file in sorted(output_dir.glob("*_failures.log")):
            f.write(f"- `{log_file.name}`\n")
    
    print(f"\n📊 SUMMARY")
    print("=" * 60)
    for category, status in results.items():
        print(f"{status} {category}")
    
    print(f"\n📁 Detailed logs saved to: {output_dir}")
    print(f"📋 Master summary: {summary_file}")
    
    if all_failures:
        print(f"\n🚨 Sample failures detected:")
        for failure in all_failures[:5]:
            print(f"  {failure}")

if __name__ == "__main__":
    main()