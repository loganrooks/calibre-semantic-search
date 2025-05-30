#!/usr/bin/env python3
"""
Build script for creating the Calibre plugin ZIP file
"""

import os
import sys
import zipfile
import shutil
from pathlib import Path
import argparse


def clean_build_dir(build_dir):
    """Clean the build directory"""
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True)


def copy_plugin_files(src_dir, build_dir):
    """Copy plugin files to build directory"""
    plugin_dir = src_dir / 'calibre_plugins' / 'semantic_search'
    dest_dir = build_dir / 'calibre_plugins' / 'semantic_search'
    
    # Copy Python files
    shutil.copytree(plugin_dir, dest_dir, 
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo'))
    
    # Ensure plugin-import-name file is at the root
    import_name_src = dest_dir / 'plugin-import-name-semantic_search.txt'
    import_name_dst = build_dir / 'plugin-import-name-semantic_search.txt'
    if import_name_src.exists():
        shutil.copy2(import_name_src, import_name_dst)


def create_plugin_zip(build_dir, output_file):
    """Create the plugin ZIP file"""
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Walk through the semantic_search directory specifically
        plugin_dir = build_dir / 'calibre_plugins' / 'semantic_search'
        
        for root, dirs, files in os.walk(plugin_dir):
            # Skip __pycache__ directories
            dirs[:] = [d for d in dirs if d != '__pycache__']
            
            for file in files:
                if file.endswith(('.pyc', '.pyo')):
                    continue
                    
                file_path = Path(root) / file
                # Make the path relative to the semantic_search directory
                arcname = file_path.relative_to(plugin_dir)
                
                zf.write(file_path, arcname)
        
        # Add the plugin-import-name file at the root
        import_name_file = build_dir / 'plugin-import-name-semantic_search.txt'
        if import_name_file.exists():
            zf.write(import_name_file, 'plugin-import-name-semantic_search.txt')
    
    print(f"Created plugin ZIP: {output_file}")
    print(f"Size: {output_file.stat().st_size / 1024:.1f} KB")


def verify_plugin_structure(zip_file):
    """Verify the plugin ZIP has correct structure"""
    required_files = [
        '__init__.py',
        'plugin-import-name-semantic_search.txt'
    ]
    
    with zipfile.ZipFile(zip_file, 'r') as zf:
        files = zf.namelist()
        
        for required in required_files:
            if required not in files:
                print(f"WARNING: Required file missing: {required}")
                return False
                
    print("Plugin structure verified ✓")
    return True


def main():
    parser = argparse.ArgumentParser(description='Build Calibre Semantic Search plugin')
    parser.add_argument('--output', '-o', default='calibre-semantic-search.zip',
                        help='Output ZIP file name')
    parser.add_argument('--clean', action='store_true',
                        help='Clean build directory after creating ZIP')
    args = parser.parse_args()
    
    # Paths
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    build_dir = project_dir / 'build'
    output_file = project_dir / args.output
    
    try:
        # Clean and prepare build directory
        print("Cleaning build directory...")
        clean_build_dir(build_dir)
        
        # Copy plugin files
        print("Copying plugin files...")
        copy_plugin_files(project_dir, build_dir)
        
        # Create ZIP
        print("Creating plugin ZIP...")
        create_plugin_zip(build_dir, output_file)
        
        # Verify structure
        verify_plugin_structure(output_file)
        
        # Clean up if requested
        if args.clean:
            print("Cleaning up build directory...")
            shutil.rmtree(build_dir)
            
        print("\nBuild complete!")
        print(f"\nTo install in Calibre:")
        print(f"  calibre-customize -a {output_file}")
        
    except Exception as e:
        print(f"Build failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()