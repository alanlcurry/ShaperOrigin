# AI Agent Instructions for ShaperOrigin Project

This document provides essential context for AI agents working with the ShaperOrigin codebase.

## Project Overview

This Python tool processes SVG files exported from Affinity Designer 2 or Affinity 3 to add Shaper Origin-specific attributes for CNC machining. Designer 2 stores layer names in `serif:id`. Affinity 3 stores them in `affinity:id`. Output declares both namespaces. Shaper Studio's webpage uses the serif namespace.

## Key Components

- `src/shaperorigin/af2so.py`: Affinity SVG to Shaper Origin attributes
- `src/shaperorigin/ss2ad.py`: Shaper Studio SVG back to Affinity layer ids
- `src/shaperorigin/namespaces.py`: XML namespaces for SVG, Serif, Affinity, and Shaper tools
- `src/shaperorigin/colors.py`: CSS3 color name matching
- Global constants in `af2so.py`:
  - `gblShaperAttrNames`: Valid Shaper attribute names (`cutDepth`, `toolDia`, `cutOffset`, `cutType`)
  - `gblShaperCutTypes`: Valid cut types (`guide`, `inside`, `outside`, `pocket`)

## Core Workflows

### Processing SVG Files

1. Files are processed using command line arguments:
```bash
af2so -i input.svg -o output.svg [-g shaper:attribute=value ...]
```

2. Key processing steps:
   - Add Shaper namespace to SVG
   - Process group-level attributes
   - Process individual layer attributes
   - Convert color attributes to cut types
   - Apply global attributes if specified

### Attribute Handling

- **Layer Attributes**: Extracted from `serif:id` attributes in SVG elements
- **Group Attributes**: Applied to all elements in a group unless overridden
- **Global Attributes**: Applied via command line, affect all elements unless overridden
- **Color to Cut Type Mapping**:
  ```python
  black -> outside
  white -> inside
  grey -> pocket
  dodgerblue -> guide
  red -> anchor
  ```

## Project Conventions

1. **Attribute Validation**:
   - All `shaper:` attributes are validated against `gblShaperAttrNames`
   - Cut types are validated against `gblShaperCutTypes`
   - Warnings are logged for unsupported attributes/values

2. **Color Processing**:
   - RGB colors are converted to closest CSS3 color names
   - Fill and stroke values determine cut types
   - Default stroke width is set to 0.1

3. **Element IDs**:
   - Original IDs are replaced with UUIDs
   - Original layer names preserved in warnings/logs

## Common Patterns

1. **Error Handling**:
   - Attribute validation with warnings (non-blocking)
   - Graceful handling of missing attributes
   - Default values for unspecified properties

2. **File Processing**:
   - XML parsing using `ElementTree`
   - Namespace preservation
   - Attribute inheritance (global → group → layer)

For questions or improvements, consult the examples in the README.md or review similar patterns in `src/shaperorigin/af2so.py`.