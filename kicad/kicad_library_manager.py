#!/usr/bin/env python3
"""
KiCad Library Manager

A utility for organizing KiCad libraries from imports folder:
- Extracts and organizes symbols, footprints, and 3D models from imported parts
- Organizes datasheets for easy reference
- Updates project file with new library references

Usage:
  python kicad_library_manager.py

Author: Zach Dicklin
"""

import os
import sys
import shutil
import json
import logging
import glob
import zipfile
import re
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
IMPORTS_DIR = os.path.join(PROJECT_DIR, 'imports')
DATASHEETS_DIR = os.path.join(IMPORTS_DIR, 'datasheets')
PARTS_DIR = os.path.join(IMPORTS_DIR, 'parts')

# Create these directories for organized libraries
LIB_DIR = os.path.join(PROJECT_DIR, 'library')
SYMBOLS_DIR = os.path.join(LIB_DIR, 'symbols')
FOOTPRINTS_DIR = os.path.join(LIB_DIR, 'footprints')
MODELS_DIR = os.path.join(LIB_DIR, 'models')
DATASHEETS_ORGANIZED_DIR = os.path.join(LIB_DIR, 'datasheets')

# KiCad project files
PROJECT_FILE = os.path.join(PROJECT_DIR, [f for f in os.listdir(PROJECT_DIR) if f.endswith('.kicad_pro')][0])


def create_directory_structure():
    """Create the necessary directory structure for libraries if it doesn't exist."""
    for directory in [LIB_DIR, SYMBOLS_DIR, FOOTPRINTS_DIR, MODELS_DIR, DATASHEETS_ORGANIZED_DIR]:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")


def process_datasheets():
    """Process and organize datasheets from the imports directory."""
    if not os.path.exists(DATASHEETS_DIR):
        logger.warning(f"Datasheets directory not found: {DATASHEETS_DIR}")
        return

    # Create manufacturer folders for better organization
    datasheet_files = glob.glob(os.path.join(DATASHEETS_DIR, '*.pdf'))
    
    for datasheet in datasheet_files:
        filename = os.path.basename(datasheet)
        # Try to extract manufacturer from filename
        # This is a simple approach - patterns might need adjustment for your naming convention
        parts = filename.split('_')
        
        if len(parts) > 1:
            # Use first part as manufacturer directory
            manufacturer = parts[0].upper()
        else:
            # If no clear pattern, use "Misc"
            manufacturer = "Misc"
            
        # Create manufacturer directory
        manufacturer_dir = os.path.join(DATASHEETS_ORGANIZED_DIR, manufacturer)
        os.makedirs(manufacturer_dir, exist_ok=True)
        
        # Copy datasheet to organized location
        destination = os.path.join(manufacturer_dir, filename)
        if not os.path.exists(destination):
            shutil.copy2(datasheet, destination)
            logger.info(f"Copied datasheet: {filename} to {manufacturer_dir}")


def extract_kicad_libraries_from_part(part_dir):
    """Extract KiCad libraries from a part directory."""
    kicad_dir = os.path.join(part_dir, 'KiCad')
    if not os.path.exists(kicad_dir):
        logger.warning(f"No KiCad directory found in {part_dir}")
        return None
    
    part_name = os.path.basename(part_dir)
    extracted_files = {
        'symbols': [],
        'footprints': [],
        'models': []
    }
    
    # Look for symbol files (.kicad_sym, .lib, .dcm)
    symbol_files = glob.glob(os.path.join(kicad_dir, '*.kicad_sym'))
    symbol_files.extend(glob.glob(os.path.join(kicad_dir, '*.lib')))
    symbol_files.extend(glob.glob(os.path.join(kicad_dir, '*.dcm')))
    
    # Look for footprint files (.kicad_mod, .mod)
    footprint_files = glob.glob(os.path.join(kicad_dir, '*.kicad_mod'))
    footprint_files.extend(glob.glob(os.path.join(kicad_dir, '*.mod')))
    
    # Look for 3D model files (.stp, .step, .wrl)
    model_files = glob.glob(os.path.join(part_dir, '3D', '*.stp'))
    model_files.extend(glob.glob(os.path.join(part_dir, '3D', '*.step')))
    model_files.extend(glob.glob(os.path.join(part_dir, '3D', '*.wrl')))
    
    # Copy symbol files to symbols directory
    for symbol_file in symbol_files:
        filename = os.path.basename(symbol_file)
        destination = os.path.join(SYMBOLS_DIR, filename)
        shutil.copy2(symbol_file, destination)
        extracted_files['symbols'].append(destination)
        logger.info(f"Copied symbol: {filename}")
    
    # Copy footprint files to footprints directory
    for footprint_file in footprint_files:
        filename = os.path.basename(footprint_file)
        destination = os.path.join(FOOTPRINTS_DIR, filename)
        shutil.copy2(footprint_file, destination)
        extracted_files['footprints'].append(destination)
        logger.info(f"Copied footprint: {filename}")
    
    # Copy 3D model files to models directory
    for model_file in model_files:
        filename = os.path.basename(model_file)
        destination = os.path.join(MODELS_DIR, filename)
        shutil.copy2(model_file, destination)
        extracted_files['models'].append(destination)
        logger.info(f"Copied 3D model: {filename}")
    
    return extracted_files


def process_parts():
    """Process and organize parts from the imports directory."""
    if not os.path.exists(PARTS_DIR):
        logger.warning(f"Parts directory not found: {PARTS_DIR}")
        return
    
    all_extracted_files = {
        'symbols': [],
        'footprints': [],
        'models': []
    }
    
    # Get all lib directories (directories starting with LIB_)
    lib_dirs = [d for d in glob.glob(os.path.join(PARTS_DIR, 'LIB_*')) if os.path.isdir(d)]
    
    for lib_dir in lib_dirs:
        # Find part directories within this lib directory
        part_dirs = [d for d in glob.glob(os.path.join(lib_dir, '*')) if os.path.isdir(d) and not d.endswith('license.txt')]
        
        for part_dir in part_dirs:
            logger.info(f"Processing part: {os.path.basename(part_dir)}")
            extracted = extract_kicad_libraries_from_part(part_dir)
            if extracted:
                for category in all_extracted_files:
                    all_extracted_files[category].extend(extracted[category])
    
    return all_extracted_files


def create_symbol_library_table():
    """Create or update the sym-lib-table file."""
    table_file = os.path.join(PROJECT_DIR, 'sym-lib-table')
    
    # Get all symbol library files
    symbol_libs = glob.glob(os.path.join(SYMBOLS_DIR, '*.lib'))
    if not symbol_libs:
        logger.warning("No symbol libraries found to add to table.")
        return
    
    # Create table entries
    table_entries = []
    table_entries.append("(sym_lib_table")
    
    for lib_file in symbol_libs:
        lib_name = os.path.splitext(os.path.basename(lib_file))[0]
        relative_path = os.path.relpath(lib_file, PROJECT_DIR)
        # Fix: Use string literal instead of undefined variable
        table_entries.append(f'  (lib (name "{lib_name}")(type "Legacy")(uri "${{KIPRJMOD}}/{relative_path}")(options "")(descr ""))')
    
    table_entries.append(")")
    
    # Write the table file
    with open(table_file, 'w') as f:
        f.write('\n'.join(table_entries))
    
    logger.info(f"Created/updated symbol library table: {table_file}")


def create_footprint_library_table():
    """Create or update the fp-lib-table file."""
    table_file = os.path.join(PROJECT_DIR, 'fp-lib-table')
    
    # Get footprint library paths (directories with .kicad_mod files)
    footprint_libs = set()
    for file in glob.glob(os.path.join(FOOTPRINTS_DIR, '*.kicad_mod')):
        footprint_libs.add(FOOTPRINTS_DIR)
    
    if not footprint_libs:
        logger.warning("No footprint libraries found to add to table.")
        return
    
    # Create table entries
    table_entries = []
    table_entries.append("(fp_lib_table")
    
    for lib_path in footprint_libs:
        lib_name = "project_footprints"
        relative_path = os.path.relpath(lib_path, PROJECT_DIR)
        # Fix: Use string literal instead of undefined variable
        table_entries.append(f'  (lib (name "{lib_name}")(type "KiCad")(uri "${{KIPRJMOD}}/{relative_path}")(options "")(descr ""))')
    
    table_entries.append(")")
    
    # Write the table file
    with open(table_file, 'w') as f:
        f.write('\n'.join(table_entries))
    
    logger.info(f"Created/updated footprint library table: {table_file}")


def update_project_file():
    """Update KiCad project file (.kicad_pro) to include new libraries."""
    try:
        with open(PROJECT_FILE, 'r') as file:
            project_data = json.load(file)
        
        # Get symbol and footprint library names
        symbol_libs = [os.path.splitext(os.path.basename(f))[0] for f in glob.glob(os.path.join(SYMBOLS_DIR, '*.lib'))]
        footprint_libs = ["project_footprints"]  # Using the name defined in create_footprint_library_table
        
        # Update libraries section
        if 'libraries' not in project_data:
            project_data['libraries'] = {}
        
        # Update pinned symbol libraries
        project_data['libraries']['pinned_symbol_libs'] = symbol_libs
        
        # Update pinned footprint libraries
        project_data['libraries']['pinned_footprint_libs'] = footprint_libs
        
        # Write back the updated project file
        with open(PROJECT_FILE, 'w') as file:
            json.dump(project_data, file, indent=2)
        
        logger.info(f"Updated project file with new libraries: {PROJECT_FILE}")
        
    except Exception as e:
        logger.error(f"Error updating project file: {e}")


def main():
    """Main entry point for the script."""
    logger.info("Starting KiCad Library Manager")
    
    # Create necessary directory structure
    create_directory_structure()
    
    # Process datasheets
    logger.info("Processing datasheets...")
    process_datasheets()
    
    # Process parts
    logger.info("Processing parts...")
    extracted_files = process_parts()
    
    if extracted_files and (extracted_files['symbols'] or extracted_files['footprints']):
        # Create library tables
        create_symbol_library_table()
        create_footprint_library_table()
        
        # Update project file
        update_project_file()
    
    logger.info("KiCad Library Manager completed successfully")


if __name__ == "__main__":
    main()