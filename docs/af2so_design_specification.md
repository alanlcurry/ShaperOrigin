# af2so — Design Specification

> Short summary: This document specifies the design, behaviour, interfaces, validation, and test strategy for the `af2so` tool which converts Affinity Designer 2 and Affinity 3 exported SVGs to include Shaper Origin attributes.

---

## Table of contents
1. Purpose & scope ✅
2. Goals & non-goals 🎯 / ❌
3. Terminology 📚
4. High-level architecture & components 🔧
5. Data flow & processing steps 🔁
6. CLI & configuration ⚙️
7. Validation & error handling ⚠️
8. Output guarantees & compatibility 💡
9. Tests & verification ✅
10. Migration & future improvements 🚀
11. Acceptance criteria ✔️
12. Changelog (recent refactor) 📝

---

## 1. Purpose & scope ✅
- **Purpose:** Convert SVGs produced by Affinity Designer 2 or Affinity 3 so that CNC tooling (Shaper Origin) attributes (e.g., `shaper:cutDepth`, `shaper:cutType`, `shaper:toolDia`) are applied to the appropriate SVG elements.
- **Scope:**
  - Parse `serif:id` (Designer 2) or `affinity:id` (Affinity 3) layer names for `shaper:` attributes. When both are present, `serif:id` wins.
  - Map element styles (fill/stroke) to Shaper cut types.
  - Apply group-level attributes to descendants; apply global CLI-specified attributes where group/element attributes are absent.
  - Declare `xmlns:shaper`, `xmlns:serif`, and `xmlns:affinity` on the root. Shaper Studio's webpage uses the serif namespace. Affinity 3 uses the affinity namespace.

---

## 2. Goals & non-goals 🎯 / ❌
- **Goals:**
  - Correctly annotate SVG elements with `shaper:` attributes.
  - Declare `xmlns:serif`, `xmlns:affinity`, and `xmlns:shaper` on the output.
  - Provide clear CLI interface and robust validation + warnings (non-blocking).
  - Keep code readable and testable with small helpers and limited global state.
- **Non-goals:**
  - Full DTD-based XML validation by default.
  - Extensive geometry rewriting or SVG structural changes beyond attribute additions.

---

## 3. Terminology 📚
- **AD2:** Affinity Designer 2. Stores the layer name in `serif:id` (`http://www.serif.com/`).
- **Affinity 3:** Affinity Studio. Stores the layer name in `affinity:id` (`https://www.affinity.studio/`).
- **`shaper:*`:** Namespaced attributes consumed by Shaper Origin workflow (e.g., `shaper:cutType`).

---

## 4. High-level architecture & components 🔧
- **Entry:** `af2so.py::main()` — CLI parsing and per-file orchestration.
- **Helpers:**
  - `local_name(elem)` — get local tag name.
  - `parse_style(style_str)` — parse `style` into a dict.
  - `layer_id(elem)` — read `serif:id`, otherwise `affinity:id`.
  - `set_group_attributes(elem)` — extract group `shaper:` attrs (returns list or `None`), sets UUID, removes both layer ids.
  - `svg_add_layer_attributes(elem)` — add `shaper:` attrs from the layer id on the element.
  - `svg_convert_attribute(elem)` — map fill/stroke to `shaper:cutType`, set `fill` and `stroke-width` and new `id`.
  - `svg_add_xmlns(elem)` — ensure `xmlns:shaper`, `xmlns:serif`, and `xmlns:affinity` exist on root.
- **Global:** minimal module-level global `gblShaperAttrs` for CLI-provided shaper attributes.
- **Logging:** Uses `logging` for info/warnings.

---

## 5. Data flow & processing steps 🔁
Per file:
1. Parse file with ElementTree.
2. Register required namespaces for serialization.
3. Iterate elements document-order:
   - If root (`svg`) → `svg_add_xmlns`.
   - If group (`g`) → `set_group_attributes()` and capture `group_attrs`.
   - Else (shape) → `svg_add_attribute(elem, group_attrs)` which:
     - Adds layer attributes from `serif:id` or `affinity:id` if present
     - Applies `group_attrs` if present
     - Applies `gblShaperAttrs` (global) if attributes are still missing
     - Converts style to `shaper:cutType`, sets `fill` and `stroke-width`, generates UUID id.
4. Write tree via `ElementTree.write()`.

Notes:
- `serif:id` and `affinity:id` are removed during processing (UUID added instead).
- The root declares `xmlns:serif` and `xmlns:affinity` even after those layer ids are removed. Shaper Studio's webpage uses `xmlns:serif`.

---

## 6. CLI & configuration ⚙️
- Example usages:
  - `af2so -i input.svg`
  - `af2so -i input.svg -o output.svg`
  - `af2so -i "dir/*.svg" -g "shaper:cutDepth=50mm shaper:toolDia=8mm"`
- `-i/--inFile` supports glob patterns.
- `-o/--outFile` optional. If multiple inputs are provided, `-o` must be a directory.
- `-g/--gblAttr` accepts multiple tokens or a single quoted string with tokens; parsed into `gblShaperAttrs`.

---

## 7. Validation & error handling ⚠️
- `validate_shaper_attributes(attr)` ensures attribute name is allowed and `cutType` values are valid; logs `warning` for unsupported values.
- Per-file `ET.ParseError` is caught and logged; processing continues for other files.
- Non-fatal issues are logged (warnings) rather than halting execution.

---

## 8. Output guarantees & compatibility 💡
- **Guaranteed:**
  - Processed elements receive UUIDs in `id`.
  - `shaper:` attributes are present from layer/group/global rules.
  - `xmlns:shaper`, `xmlns:serif`, and `xmlns:affinity` present on root.
- **Not preserved:**
  - XML declaration and DOCTYPE are not preserved by ElementTree-based flow.
- **Improvement option:**
  - Use `lxml` for precise DOCTYPE and XML declaration control if round-trip fidelity is required.

---

## 9. Tests & verification ✅
- Unit tests added: `tests/test_helpers.py` and `tests/run_tests.py`.
  - `parse_style`, `local_name`, `get_color_name_rgb` covered.
  - `test_global_attributes_applied()` ensures CLI global attrs apply when element/group has no shaper attrs.
- Recommended additions:
  - Integration test: run CLI on fixture SVG and assert root namespaces and sample element attributes.
  - Edge case tests for invalid RGB strings, unknown attributes, missing files.
- CI: add GitHub Actions to run tests on push/PR.

---

## 10. Migration & future improvements 🚀
- Switch to `lxml` to preserve DOCTYPE and XML declaration for full fidelity.
- Extend style parsing to support additional CSS forms and `fill`/`stroke` attributes outside `style`.
- Add integration and regression tests to cover real-world AD2 outputs.
- Consider providing a library API for programmatic use.

---

## 11. Acceptance criteria ✔️
- Running `af2so -i Example.svg -o out.svg -g "shaper:cutDepth=50mm shaper:toolDia=8mm"` produces:
  - `xmlns:serif` and `xmlns:shaper` on root
  - Elements lacking `serif:` shaper attributes have `shaper:cutDepth="50mm"` (global applied)
  - All shapes have `shaper:cutType` and `stroke-width="0.1"`
- Unit tests pass and warnings are logged for unsupported attributes.

---

## 12. Changelog (recent refactor) 📝
- Added helpers: `local_name`, `parse_style`.
- Replaced prints with `logging`.
- Encapsulated CLI in `main()` and made module import-safe for tests.
- `set_group_attributes` returns attrs and removes reliance on a global.
- Ensured `xmlns:serif` is preserved on root.
- Fixed parsing and application of global attributes.
- Added unit tests and a lightweight test runner.

---

### Example (short) 🔍
Input (layer name):

```xml
<g serif:id="shaper:toolDia=0.125in shaper:cutDepth=30mm">
  <rect ... style="fill:rgb(0,0,0)" />
</g>
```

Expected output:

```xml
<svg ... xmlns:shaper="http://..." xmlns:serif="http://...">
  <g id="...">
    <rect shaper:toolDia="0.125in" shaper:cutDepth="30mm" shaper:cutType="outside" fill="#000000" stroke-width="0.1" id="..."/>
  </g>
</svg>
```

---

If you'd like, I can add this spec to the `README.md` as a short section, create a GitHub Actions workflow to run tests, or build an integration test that asserts the output file contents from `Example.svg`.
