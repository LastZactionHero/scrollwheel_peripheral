# Scrollwheel Peripheral Project

This is a KiCad project for a scrollwheel peripheral device.

## Library Management

This project includes a library management tool that helps organize components and datasheets.

### Using the Library Manager

1. Place your component files in the following directories:
   - `imports/parts/` - Parts downloaded from componentsearchengine.com or similar
   - `imports/datasheets/` - PDF datasheets for components

2. Run the library manager:
   ```
   python kicad_library_manager.py
   ```

3. The tool will:
   - Extract and organize symbols, footprints, and 3D models from imported parts
   - Organize datasheets for easy reference
   - Create library table files (`sym-lib-table` and `fp-lib-table`)
   - Update the project file with new library references

### Directory Structure

After running the tool, you'll have the following organized structure:

```
project/
├── imports/               # Original imported files
│   ├── datasheets/        # Original datasheets
│   └── parts/             # Original part files
├── library/               # Organized libraries
│   ├── symbols/           # Symbol libraries (.lib, .kicad_sym)
│   ├── footprints/        # Footprint libraries (.kicad_mod)
│   ├── models/            # 3D models (.stp, .wrl)
│   └── datasheets/        # Organized datasheets by manufacturer
├── sym-lib-table          # Symbol library table
├── fp-lib-table           # Footprint library table
├── kicad_library_manager.py  # The library management tool
└── [project files]        # KiCad project files
```

### Adding New Components

To add new components to your project:

1. Download the component files and datasheets
2. Place them in the appropriate import directories
3. Run the library manager again
4. Open your KiCad project, and the new libraries will be available

## Development Notes

- The library manager preserves your original files in the imports directory
- Datasheets are organized by manufacturer name (extracted from filename)
- Symlink tables are created to make libraries accessible in KiCad