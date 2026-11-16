#!/usr/local/bin/python3

# MIT License

# Copyright (c) 2023-2025  Alan L. Curry

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# This module processes Affinity Designer 2 (AD2) generated SVG files to add Shaper Origin-specific
# attributes. It reads layer names from AD2 that contain 'shaper:' attributes and applies them to
# the corresponding SVG elements. The tool supports both layer-specific attributes and group-level
# attributes that can be inherited by child elements.
#
# Key Features:
# - Processes AD2-exported SVG files to add Shaper Origin attributes
# - Supports layer-specific and group-inherited attributes using recursive tree traversal
# - Converts color attributes to Shaper Origin cut types
# - Allows global attributes to be applied via command line
#
# Usage: 
#   ad2so.py [-h] -i INFILE [-o OUTFILE] [-g [GBLATTR ...]]
#
# Examples:
#   python3 ad2so.py -i input.svg -o output.svg
#   python3 ad2so.py -i input.svg -g shaper:cutDepth=15mm shaper:toolDia=0.25in
#
# Options:
#   -h, --help            Show this help message and exit
#   -i INFILE, --inFile INFILE
#                         Input SVG file from Affinity Designer 2
#   -o OUTFILE, --outFile OUTFILE
#                         Output SVG file (optional, defaults to input file)
#   -g [GBLATTR ...], --gblAttr [GBLATTR ...]
#                         Global shaper attributes to apply (optional)
"""
ad2so.py: Enhanced conversion of Affinity Designer 2 SVGs for Shaper Origin.
This version improves group attribute inheritance using recursive processing.
"""

import xml.etree.ElementTree as ET
import argparse
import sys
import uuid
import webcolors
import glob
import os.path
import logging
import re

# Configure basic logging
logging.basicConfig(level=logging.INFO)

gblShaperAttrs = None
gblShaperAttrNames = {"cutDepth", "toolDia", "cutOffset", "cutType"}
gblShaperCutTypes = {"guide", "inside", "outside", "pocket"}

# XML namespaces used in SVG processing:
# - w3: Standard SVG namespace
# - serif: Affinity Designer namespace for layer information
# - shaper: Shaper Origin namespace for CNC attributes
nameSpaces = {
    "w3": "http://www.w3.org/2000/svg",
    "serif": "http://www.serif.com/",
    "shaper": "http://www.shapertools.com/namespaces/shaper"
}

SERIF_ID = "{" + nameSpaces["serif"] + "}id"

def local_name(elem):
    """Return the local tag name (without namespace)."""
    tag = elem.tag
    if isinstance(tag, str) and '}' in tag:
        return tag.rsplit('}', 1)[-1]
    return tag

def parse_style(style_str):
    """Parse an SVG style string into a dict."""
    if not style_str:
        return {}
    return dict(item.split(':', 1) for item in style_str.split(';') if ':' in item)

def closest_color(requested_colour):
    """
    Find the closest CSS3 color name for a given RGB value.
    
    Uses Euclidean distance in RGB color space to find the nearest named color.
    
    Args:
        requested_colour (tuple): RGB color values as (r, g, b)
        
    Returns:
        str: The name of the closest CSS3 color
        
    Example:
        closest_color((128, 128, 128))  # Returns 'grey'"""
    min_colours = {}
    # Note: Using CSS3 color mapping as preferred by Shaper
    for name in webcolors.names("css3"):
        r_c, g_c, b_c = webcolors.name_to_rgb(name)
        rd = (r_c - requested_colour[0]) ** 2
        gd = (g_c - requested_colour[1]) ** 2
        bd = (b_c - requested_colour[2]) ** 2
        min_colours[(rd + gd + bd)] = name
    return min_colours[min(min_colours.keys())]

def get_color_name(rgb_tuple):
    """
    Get the CSS3 color name for an RGB tuple.
    
    First attempts an exact match, then falls back to finding the closest color.
    
    Args:
        rgb_tuple (tuple): RGB color values as (r, g, b)
        
    Returns:
        str: The name of the exact or closest CSS3 color
        
    Example:
        get_color_name((0, 0, 0))  # Returns 'black'"""
    try:
        hex_value = webcolors.rgb_to_hex(rgb_tuple)
        return webcolors.hex_to_name(hex_value)
    except ValueError:
        return closest_color(rgb_tuple)
    
def get_color_name_rgb(rgb_str):
    """
    Convert a CSS RGB string to a color name with robust parsing.
    
    Parses a string in format 'rgb(r,g,b)' and converts it to a CSS3 color name.
    
    Args:
        rgb_str (str): RGB color string in format 'rgb(r,g,b)'
        
    Returns:
        str: The CSS3 color name
        
    Example:
        get_color_name_rgb('rgb(0,0,0)')  # Returns 'black'"""
    try:
        matches = re.findall(r'\d+', rgb_str)
        if len(matches) < 3:
            raise ValueError("Incomplete RGB data")
            
        rgbValue = tuple(map(int, matches[:3]))
        if not all(0 <= x <= 255 for x in rgbValue):
            raise ValueError("Values out of range")
            
        return get_color_name(rgbValue)
    except (ValueError, TypeError) as e:
        logging.warning("Invalid RGB color '%s': %s. Defaulting to black.", rgb_str, e)
        return "black"

def validate_shaper_attributes(attribute):
    """
    Validate Shaper Origin attribute names and values.
    
    Checks if the attribute name is in the allowed set (gblShaperAttrNames)
    and if it's a cutType, validates against allowed cut types (gblShaperCutTypes).
    
    Args: attribute (str): Attribute string in format 'shaper:name=value'"""
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

def set_group_attributes(elem):
    """Extract `shaper:` attributes from a group element and return them.

    Returns:
        list[str] | None: List of `shaper:...` attribute strings if present, otherwise None.

    Side effects:
        - Sets a new UUID on the element's `id` attribute.
        - Removes the original `serif:id` attribute from the element."""
    serifId = elem.attrib.get(SERIF_ID)
    attrs = None
    if serifId:
        words = serifId.split()
        attrs = [s for s in words if s.startswith("shaper:")]
        for s in attrs:
            validate_shaper_attributes(s)
    
    elem.set("id", str(uuid.uuid4()))
    elem.attrib.pop(SERIF_ID, None)
    return attrs

def svg_add_xmlns(elem):
    """Ensure the SVG root element declares the `shaper` and `serif` namespaces.

    The function is idempotent and will add the missing namespace declarations if necessary."""
    if 'xmlns:shaper' not in elem.attrib:
        elem.set("xmlns:shaper", nameSpaces["shaper"])
    if 'xmlns:serif' not in elem.attrib:
        elem.set("xmlns:serif", nameSpaces["serif"]) 

def svg_add_layer_attributes(elem):
    """
    Extract and add Shaper attributes from layer names to SVG elements.
    
    Processes the serif:id attribute (which contains the AD2 layer name)
    to find and validate shaper: attributes, then adds them to the element.
    
    Args:
        elem (xml.etree.ElementTree.Element): The SVG element to process
        
    Side Effects:
        Adds validated shaper: attributes to the element"""
    serifId = elem.attrib.get(SERIF_ID)
    if not serifId:
        return
    
    shaperAttrs = [s for s in serifId.split() if s.startswith("shaper:")]
    for s in shaperAttrs:
        validate_shaper_attributes(s)
        kv = s.split("=")
        if len(kv) == 2:
            elem.set(kv[0], kv[1])

def svg_convert_attribute(elem):
    """
    Convert SVG style attributes to Shaper Origin cut types and fill values.
    
    Processes fill and stroke values from SVG elements and maps them to
    appropriate Shaper Origin cut types. Also handles combined fill/stroke
    scenarios and sets default values.
    
    Color Mapping Rules:
    - black fill, black stroke -> outside cut
    - white fill, black stroke -> inside cut
    - grey fill, no stroke -> pocket cut
    - no fill, grey stroke -> online cut
    - blue fill or blue stroke -> guide
    - red fill or red stroke -> anchor
    
    RGB Color References:
    - black:    rgb(0,0,0)
    - white:    rgb(255,255,255)
    - grey:     rgb(127,127,127)
    - blue:     rgb(0,104,255)
    - red:      rgb(255,0,0)
    
    Args:
        elem (xml.etree.ElementTree.Element): The SVG element to process
    
    Side Effects:
        - Sets stroke-width, UUID id, shaper:cutType, and fill attributes."""
    cutTypes = {
        "black": "outside", "white": "inside", "grey": "pocket",
        "nonegrey": "online", "dodgerblue": "guide", "red": "anchor"
    }
    fillValues = {
        "outside": "#000000", "inside": "#FFFFFF", "pocket": "#7F7F7F",
        "guide": "#0068FF", "online": "none", "anchor": "#FF0000"
    }

    elem.set("stroke-width", "0.1")
    elem.set("id", str(uuid.uuid4()))
    elem.attrib.pop(SERIF_ID, None)

    # Extract fill/stroke from style or direct attributes
    style_dict = parse_style(elem.attrib.get("style"))
    fill = style_dict.get("fill") or elem.attrib.get("fill")
    stroke = style_dict.get("stroke") or elem.attrib.get("stroke")

    # Clean up original styling
    for attr in ["style", "fill", "stroke"]:
        elem.attrib.pop(attr, None)

    if fill and "rgb" in fill: fill = get_color_name_rgb(fill)
    if stroke and "rgb" in stroke: stroke = get_color_name_rgb(stroke)

    # Determine cut type based on logic from design spec
    if fill and stroke:
        if fill == "none" and stroke == "grey": color_name = "nonegrey"
        elif fill == "none": color_name = stroke
        else: color_name = fill
    elif fill:
        color_name = "dodgerblue" if fill == "none" else fill
    else:
        color_name = "black"

    cutType = cutTypes.get(color_name, "outside")
    elem.set("shaper:cutType", cutType)
    elem.set("fill", fillValues.get(cutType, "#000000"))

def svg_add_other_attributes(elem, attributes):
    """
    Add additional Shaper attributes to an SVG element.
    
    Adds attributes from a list if they don't already exist on the element.
    Used for both group-level and global attributes.
    
    Args: elem, attributes (list)"""
    existing = elem.keys()
    for attr in attributes:
        kv = attr.split("=")
        if len(kv) == 2 and kv[0] not in existing:
            elem.set(kv[0], kv[1])

def svg_add_attribute(elem, group_attrs=None):
    """Process a shape element by combining layer, group, and global attributes."""
    # 1. Layer attributes (highest priority)
    svg_add_layer_attributes(elem)
    # 2. Group attributes
    if group_attrs:
        svg_add_other_attributes(elem, group_attrs)
    # 3. Global attributes (lowest priority)
    if gblShaperAttrs:
        svg_add_other_attributes(elem, gblShaperAttrs)
    
    svg_convert_attribute(elem)

def process_element(elem, group_attrs=None):
    """
    Recursively process the SVG tree to handle hierarchical inheritance.
    This ensures nested groups apply attributes correctly only to their children.
    """
    name = local_name(elem)
    current_attrs = group_attrs

    if name == 'svg':
        svg_add_xmlns(elem)
    elif name == 'g':
        new_group_attrs = set_group_attributes(elem)
        if new_group_attrs:
            # Inherit from parent group then add/overwrite with current group
            if current_attrs:
                # Create a merged list where current group can overwrite parent group keys
                merged = {a.split('=')[0]: a.split('=')[1] for a in current_attrs}
                for a in new_group_attrs:
                    kv = a.split('=')
                    merged[kv[0]] = kv[1]
                current_attrs = [f"{k}={v}" for k, v in merged.items()]
            else:
                current_attrs = new_group_attrs
    elif name in {'path', 'rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon'}:
        svg_add_attribute(elem, current_attrs)

    # Continue to children
    for child in list(elem):
        process_element(child, current_attrs)

def main():
    """
    Main function for processing SVG files.
    
    Handles command line arguments, glob expansion, namespace registration,
    and triggers the recursive processing of each valid input file."""
    parser = argparse.ArgumentParser(description="Convert AD2 SVG to Shaper Origin format")
    parser.add_argument("-i", "--inFile", help="Input SVG file(s)", nargs='+', required=True)
    parser.add_argument("-o", "--outFile", help="Output file or directory", required=False)
    parser.add_argument("-g", "--gblAttr", help="Global shaper attributes", nargs='*', required=False)

    # If no arguments are provided, show help and exit instead of raising a required-argument error
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    if args.inFile and len(args.inFile) > 1 and args.outFile and not os.path.isdir(args.outFile):
        logging.error("With multiple inputs, --outFile must be a directory.")
        sys.exit(1)

    # Resolve files
    expanded = []
    for p in args.inFile: expanded.extend(glob.glob(p))
    valid_files = [f for f in expanded if f.lower().endswith('.svg')]

    if not valid_files:
        logging.error("No valid SVG files found.")
        sys.exit(1)

    # Register namespaces for serialization
    ET.register_namespace('', nameSpaces["w3"])
    ET.register_namespace("serif", nameSpaces["serif"])
    ET.register_namespace("shaper", nameSpaces["shaper"])

    # Setup global attributes
    global gblShaperAttrs
    if args.gblAttr:
        gblShaperAttrs = []
        for token in args.gblAttr:
            gblShaperAttrs.extend(token.split())
        for attr in gblShaperAttrs:
            validate_shaper_attributes(attr)

    for input_file in valid_files:
        try:
            if "-converted" in input_file: continue
            
            # Determine output path
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

        except ET.ParseError as e:
            logging.error("XML Parse Error in %s: %s", input_file, e)
        except Exception as e:
            logging.error("Failed to process %s: %s", input_file, e)

if __name__ == "__main__":
    main()