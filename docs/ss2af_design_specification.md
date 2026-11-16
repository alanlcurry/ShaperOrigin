# ss2af Design Specification

## Title
ss2af — Shaper Studio SVG → Affinity (Designer 2 and Affinity 3) layer-name converter

## Overview
This document specifies the design of `ss2af.py`, a small command-line tool that converts Shaper Studio-flavored SVG files into a form compatible with Affinity (Designer 2 and Affinity 3) by moving Shaper Studio (`shaper:`) attributes into element `id` values. The Affinity workflow used by designers stores layer metadata in the layer name / ID field; `ss2af.py` consolidates namespaced attributes into that field so Affinity imports retain the metadata.

## Goals
- Convert `shaper:` namespaced attributes into Affinity-friendly `id` values for each SVG element.
- Preserve original SVG structure, namespaces, and other attributes.
- Support batch processing via glob/wildcard patterns.
- Be robust to corrupted or non-SVG inputs and produce clear error messages.

## Non-Goals
- Perform any geometric conversions or material/cut inference.
- Mutate colors or styles except when necessary for converting/reading namespaced attributes.

## Assumptions
- Input files are XML SVG documents that may include the `shaper` namespace: `http://www.shapertools.com/namespaces/shaper`.
- Affinity (Designer 2 and Affinity 3) expects shaper metadata present in the element's `id`/layer-name string (space-separated key=value pairs prefixed with `shaper:`).
- Python 3.x is available and `xml.etree.ElementTree` is acceptable for parsing/writing SVG.

## CLI
- Usage: `python3 ss2af.py -i INFILE [-o OUTFILE]`
- Arguments:
  - `-i, --inFile` (required): One or more input patterns (supports wildcards, e.g., `*.svg`, `dir/**/*.svg`).
  - `-o, --outFile` (optional): Output file or output directory. If multiple inputs are provided and `-o` is given, it must be an existing directory.

Behavior:
- If `-o` is omitted, outputs are written alongside inputs with a `-converted` suffix before the `.svg` extension.
- Files with `-converted` in their filename are skipped to avoid reprocessing.

## Namespaces
Register and preserve these namespaces in output:
- default SVG: `http://www.w3.org/2000/svg`
- Serif (Affinity): `http://www.serif.com/`
- Shaper: `http://www.shapertools.com/namespaces/shaper`

## Inputs and Outputs
- Input: One or more `.svg` files containing elements with attributes in the shaper namespace.
- Output: For each input SVG, a new SVG with the same structure but where per-element `shaper:` attributes are removed and replaced by a single `id` attribute containing space-separated `shaper:name=value` tokens.

Example input element attributes (namespaced):
- `{http://www.shapertools.com/namespaces/shaper}cutDepth="3"`
- `{http://www.shapertools.com/namespaces/shaper}cutType="inside"`

Corresponding output `id` value:
- `shaper:cutDepth=3 shaper:cutType=inside`

## Core Functions and Responsibilities
- `convert_attributes_to_id(elem)`
  - Purpose: For a single element, find all attributes in the shaper namespace, format each as `shaper:localName=value` (stripping internal spaces from values), join them with single spaces, set the resulting string as the element's `id` attribute, and remove the original namespaced attributes.
  - Side effects: Mutates the element's attributes in-place.

- `process_svg(tree)`
  - Purpose: Iterate all elements in the parsed `ElementTree` and call `convert_attributes_to_id` on non-root elements.
  - Behavior: Skips root `<svg>` element (so document-level shaper attributes, if any, are not converted to `id`).

- `main()`
  - Responsibilities:
    - Parse CLI args.
    - Expand input patterns using `glob`.
    - Validate inputs (skip non-SVGs, ensure output directory constraints when multiple inputs).
    - Register namespaces via `ET.register_namespace` so output preserves prefixes.
    - Parse each SVG (`ET.parse`), call `process_svg`, and write output with a `-converted` suffix unless explicit single-output was requested.
    - Handle and log parsing errors, skip unreadable files, and print helpful messages.

## Algorithmic Details
- Attribute detection is done by matching attribute names that start with the shaper namespace URI, i.e., attribute keys whose expanded name begins with `{http://www.shapertools.com/namespaces/shaper}`.
- Local attribute name is extracted by splitting on `}` and taking the trailing portion.
- Values are trimmed of internal spaces before being concatenated into the `id` string to avoid accidental tokenization issues.

## Error Handling
- If no files match the provided patterns, the program prints an error and exits non-zero.
- If multiple inputs are provided with `-o` and `-o` is not a directory, the program prints an error and exits non-zero.
- For unreadable or missing input files, the program prints an error and continues processing remaining files.
- XML parse errors for individual files are caught, printed, and the tool continues processing other files.

## Edge Cases
- Elements that already have an `id` will be overwritten by the generated `id` containing shaper attributes; this is an intentional behavior to ensure Affinity receives the shaper metadata in the layer name.
- If an element has no shaper attributes but already has an `id`, that `id` is preserved (no change).
- If an element's shaper attributes include spaces in values, those spaces are removed during concatenation; if preserving spaces is critical, this behavior should be revisited.

## Testing
- Unit tests should cover:
  - Single element with multiple shaper attributes → `id` contains all tokens in expected format.
  - Element with no shaper attributes → no modification to `id`.
  - Root `<svg>` with shaper attributes → ensure root is skipped and attributes remain untouched or documented behavior.
  - CLI glob expansion and output path handling (single file with `-o` file, multiple files with `-o` directory, omitted `-o`).
  - Handling of invalid files and parse errors.

- Suggested test harness: add tests under `tests/` that create temporary SVG files (via `tempfile`), invoke `ss2af.py` functions (preferably by importing `process_svg` and `convert_attributes_to_id`), and assert resulting XML string/value for `id` attributes.

## Logging and UX
- Current design prints progress and error messages to stdout. Consider adopting `logging` with levels (INFO/WARNING/ERROR) for more flexible integration with other tools.

## Future Improvements
- Preserve pre-existing `id` values by appending shaper tokens rather than replacing the `id` (or provide a CLI flag to control this behavior).
- Provide an option to choose the token delimiter (space vs. semicolon) or to URL-encode values to preserve spaces/constants.
- Add an option to export a CSV manifest of elements and their shaper attributes.
- Add unit-test automation and continuous integration to run tests on commits.

## File Location
Saved as `docs/ss2af_design_specification.md`.


---
Revision: 1.0
Author: Automated design spec generator
Date: 2026-01-10
