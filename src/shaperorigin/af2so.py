# Copyright (C) 2023-2026 Alan L. Curry
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Convert Affinity Designer 2 and Affinity 3 SVGs to Shaper Origin attributes.

Reads layer names that contain ``shaper:`` attributes and applies them to the
corresponding SVG elements. Group attributes are inherited by child shapes.
Designer 2 stores the layer name in ``serif:id``. Affinity 3 stores it in
``affinity:id``. Output declares both namespaces so Shaper Studio can keep
using ``serif`` while later Affinity versions can use ``affinity``.
"""

import argparse
import glob
import logging
import os.path
import sys
import uuid
import xml.etree.ElementTree as ET

from shaperorigin.colors import get_color_name_rgb
from shaperorigin.namespaces import AFFINITY_ID, SERIF_ID, nameSpaces
from shaperorigin.xmlutil import local_name

gblShaperAttrs = None
gblShaperAttrNames = {"cutDepth", "toolDia", "cutOffset", "cutType"}
gblShaperCutTypes = {"guide", "inside", "outside", "pocket"}


def parse_style(style_str):
    """Parse an SVG style string into a dict.

    Args:
        style_str (str | None): A CSS declaration list such as ``fill:#000;``.

    Returns:
        dict: Property names mapped to values. Empty when the input is missing.
    """
    if not style_str:
        return {}
    return dict(item.split(":", 1) for item in style_str.split(";") if ":" in item)


def validate_shaper_attributes(attribute):
    """Validate Shaper Origin attribute names and values.

    Checks if the attribute name is in the allowed set and, for ``cutType``,
    checks the value against the allowed cut types.

    Args:
        attribute (str): Attribute string in format ``shaper:name=value``.
    """
    parts = attribute.split("=")
    if len(parts) < 2:
        return

    name_parts = parts[0].split(":")
    attr_name = name_parts[1] if len(name_parts) > 1 else name_parts[0]

    if attr_name in gblShaperAttrNames:
        if attr_name == "cutType" and parts[1] not in gblShaperCutTypes:
            logging.warning("Unsupported cut type: %s", parts[1])
    else:
        logging.warning("Unsupported shaper attribute: %s", attr_name)


def layer_id(elem):
    """Return the Affinity layer name stored on an element.

    Affinity Designer 2 uses ``serif:id``. Affinity 3 uses ``affinity:id``.
    When both are present, ``serif:id`` wins because Shaper Studio reads that
    namespace.

    Args:
        elem: SVG element that may carry a layer-name attribute.

    Returns:
        str | None: The layer name, or None when neither attribute is set.
    """
    serif_value = elem.attrib.get(SERIF_ID)
    if serif_value:
        return serif_value
    return elem.attrib.get(AFFINITY_ID)


def clear_layer_ids(elem):
    """Remove both Affinity layer-name attributes from an element.

    Args:
        elem: SVG element updated in place.
    """
    elem.attrib.pop(SERIF_ID, None)
    elem.attrib.pop(AFFINITY_ID, None)


def set_group_attributes(elem):
    """Extract ``shaper:`` attributes from a group element and return them.

    Args:
        elem: Group element whose layer id may hold shaper attributes.

    Returns:
        list[str] | None: ``shaper:...`` attribute strings, or None when absent.

    Side effects:
        Sets a new UUID on the element's ``id`` attribute and removes both
        ``serif:id`` and ``affinity:id``.
    """
    layer_name = layer_id(elem)
    attrs = None
    if layer_name:
        words = layer_name.split()
        attrs = [token for token in words if token.startswith("shaper:")]
        for token in attrs:
            validate_shaper_attributes(token)

    elem.set("id", str(uuid.uuid4()))
    clear_layer_ids(elem)
    return attrs


def svg_add_xmlns(elem):
    """Ensure the SVG root declares shaper, serif, and affinity namespaces.

    Shaper Studio's webpage renders with the serif namespace. Affinity 3
    expects the affinity namespace. Both are declared on every output file.

    Args:
        elem: The SVG root element. Missing declarations are added in place.
    """
    if "xmlns:shaper" not in elem.attrib:
        elem.set("xmlns:shaper", nameSpaces["shaper"])
    if "xmlns:serif" not in elem.attrib:
        elem.set("xmlns:serif", nameSpaces["serif"])
    if "xmlns:affinity" not in elem.attrib:
        elem.set("xmlns:affinity", nameSpaces["affinity"])


def svg_add_layer_attributes(elem):
    """Add Shaper attributes found in an element's layer name.

    Args:
        elem: SVG element whose ``serif:id`` or ``affinity:id`` may contain
            ``shaper:`` tokens. Both layer-id attributes are removed.
    """
    layer_name = layer_id(elem)
    clear_layer_ids(elem)
    if not layer_name:
        return

    shaper_attrs = [token for token in layer_name.split() if token.startswith("shaper:")]
    for token in shaper_attrs:
        validate_shaper_attributes(token)
        key_value = token.split("=")
        if len(key_value) == 2:
            elem.set(key_value[0], key_value[1])


def svg_convert_attribute(elem):
    """Map fill and stroke colors to a Shaper cut type and fill value.

    Color mapping:
        black fill, black stroke -> outside
        white fill, black stroke -> inside
        grey fill, no stroke -> pocket
        no fill, grey stroke -> online
        blue fill or blue stroke -> guide
        red fill or red stroke -> anchor

    Args:
        elem: Shape element updated in place with ``shaper:cutType`` and fill.
    """
    cut_types = {
        "black": "outside",
        "white": "inside",
        "grey": "pocket",
        "nonegrey": "online",
        "dodgerblue": "guide",
        "red": "anchor",
    }
    fill_values = {
        "outside": "#000000",
        "inside": "#FFFFFF",
        "pocket": "#7F7F7F",
        "guide": "#0068FF",
        "online": "none",
        "anchor": "#FF0000",
    }

    elem.set("stroke-width", "0.1")
    elem.set("id", str(uuid.uuid4()))
    clear_layer_ids(elem)

    style_dict = parse_style(elem.attrib.get("style"))
    fill = style_dict.get("fill") or elem.attrib.get("fill")
    stroke = style_dict.get("stroke") or elem.attrib.get("stroke")

    for attr in ["style", "fill", "stroke"]:
        elem.attrib.pop(attr, None)

    if fill and "rgb" in fill:
        fill = get_color_name_rgb(fill)
    if stroke and "rgb" in stroke:
        stroke = get_color_name_rgb(stroke)

    if fill and stroke:
        if fill == "none" and stroke == "grey":
            color_name = "nonegrey"
        elif fill == "none":
            color_name = stroke
        else:
            color_name = fill
    elif fill:
        color_name = "dodgerblue" if fill == "none" else fill
    else:
        color_name = "black"

    cut_type = cut_types.get(color_name, "outside")
    elem.set("shaper:cutType", cut_type)
    elem.set("fill", fill_values.get(cut_type, "#000000"))


def svg_add_other_attributes(elem, attributes):
    """Add Shaper attributes that are not already set on an element.

    Args:
        elem: Element to update.
        attributes (list): Strings in ``name=value`` form.
    """
    existing = elem.keys()
    for attr in attributes:
        key_value = attr.split("=")
        if len(key_value) == 2 and key_value[0] not in existing:
            elem.set(key_value[0], key_value[1])


def svg_add_attribute(elem, group_attrs=None):
    """Apply layer, group, and global attributes, then convert color.

    Args:
        elem: Shape element to update.
        group_attrs (list | None): Inherited ``shaper:`` attributes.
    """
    svg_add_layer_attributes(elem)
    if group_attrs:
        svg_add_other_attributes(elem, group_attrs)
    if gblShaperAttrs:
        svg_add_other_attributes(elem, gblShaperAttrs)

    svg_convert_attribute(elem)


def process_element(elem, group_attrs=None):
    """Walk the SVG tree and inherit group attributes onto child shapes.

    Args:
        elem: Current element.
        group_attrs (list | None): Attributes inherited from ancestor groups.
    """
    name = local_name(elem)
    current_attrs = group_attrs

    if name == "svg":
        svg_add_xmlns(elem)
    elif name == "g":
        new_group_attrs = set_group_attributes(elem)
        if new_group_attrs:
            if current_attrs:
                merged = {item.split("=")[0]: item.split("=")[1] for item in current_attrs}
                for item in new_group_attrs:
                    key_value = item.split("=")
                    merged[key_value[0]] = key_value[1]
                current_attrs = [f"{key}={value}" for key, value in merged.items()]
            else:
                current_attrs = new_group_attrs
    elif name in {"path", "rect", "circle", "ellipse", "line", "polyline", "polygon"}:
        svg_add_attribute(elem, current_attrs)

    for child in list(elem):
        process_element(child, current_attrs)


def main():
    """Parse arguments and convert each input SVG."""
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Convert Affinity SVG to Shaper Origin format")
    parser.add_argument("-i", "--inFile", help="Input SVG file(s)", nargs="+", required=True)
    parser.add_argument("-o", "--outFile", help="Output file or directory", required=False)
    parser.add_argument("-g", "--gblAttr", help="Global shaper attributes", nargs="*", required=False)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    if args.inFile and len(args.inFile) > 1 and args.outFile and not os.path.isdir(args.outFile):
        logging.error("With multiple inputs, --outFile must be a directory.")
        sys.exit(1)

    expanded = []
    for pattern in args.inFile:
        expanded.extend(glob.glob(pattern))
    valid_files = [path for path in expanded if path.lower().endswith(".svg")]

    if not valid_files:
        logging.error("No valid SVG files found.")
        sys.exit(1)

    ET.register_namespace("", nameSpaces["w3"])
    ET.register_namespace("serif", nameSpaces["serif"])
    ET.register_namespace("affinity", nameSpaces["affinity"])
    ET.register_namespace("shaper", nameSpaces["shaper"])

    global gblShaperAttrs
    if args.gblAttr:
        gblShaperAttrs = []
        for token in args.gblAttr:
            gblShaperAttrs.extend(token.split())
        for attr in gblShaperAttrs:
            validate_shaper_attributes(attr)

    for input_file in valid_files:
        try:
            if "-converted" in input_file:
                continue

            if args.outFile and len(valid_files) == 1 and not os.path.isdir(args.outFile):
                output_file = args.outFile
            else:
                base, ext = os.path.splitext(input_file)
                fname = os.path.basename(base)
                if args.outFile:
                    output_file = os.path.join(args.outFile, f"{fname}-converted{ext}")
                else:
                    output_file = f"{base}-converted{ext}"

            logging.info("Processing: %s", input_file)
            tree = ET.parse(input_file)
            process_element(tree.getroot())

            logging.info("Saving: %s", output_file)
            tree.write(output_file)

        except ET.ParseError as exc:
            logging.error("XML Parse Error in %s: %s", input_file, exc)
        except Exception as exc:
            logging.error("Failed to process %s: %s", input_file, exc)


if __name__ == "__main__":
    main()
