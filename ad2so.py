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
# - Supports layer-specific and group-inherited attributes
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

import xml.etree.ElementTree as ET
import argparse
import sys
import uuid
import webcolors
import glob
import os.path
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)

gblTree = None
gblShaperAttrs = None
grpShaperAttrs = None
gblShaperAttrNames = {"cutDepth", "toolDia", "cutOffset", "cutType"}
gblShaperCutTypes = {"guide", "inside", "outside","pocket"}

# shaper:cutType="guide" shaper:cutOffset="0in" shaper:toolDia="0.125in"
# shaper:cutType="outside" shaper:cutOffset="0in" shaper:toolDia="0.125in"
# shaper:cutType="pocket"
# shaper:cutType="inside"

# XML namespaces used in SVG processing:
# - w3: Standard SVG namespace
# - serif: Affinity Designer namespace for layer information
# - shaper: Shaper Origin namespace for CNC attributes
nameSpaces = {
    "w3": "http://www.w3.org/2000/svg",
    "serif": "http://www.serif.com/",
    "shaper": "http://www.shapertools.com/namespaces/shaper"
}

# Convenience constant for serif:id attribute
SERIF_ID = "{" + nameSpaces["serif"] + "}id"


def local_name(elem):
    """Return the local tag name (without namespace)."""
    tag = elem.tag
    if isinstance(tag, str) and '}' in tag:
        return tag.rsplit('}', 1)[-1]
    return tag


def parse_style(style_str):
    """Parse an SVG style string into a dict: 'fill:#000;stroke:none' -> {'fill':'#000','stroke':'none'}"""
    if not style_str:
        return {}
    return dict(item.split(':', 1) for item in style_str.split(';') if ':' in item)


def rgb_to_hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)



def closest_color(requested_colour):
    """
    Find the closest CSS3 color name for a given RGB value.
    
    Uses Euclidean distance in RGB color space to find the nearest named color.
    
    Args:
        requested_colour (tuple): RGB color values as (r, g, b)
        
    Returns:
        str: The name of the closest CSS3 color
        
    Example:
        closest_color((128, 128, 128))  # Returns 'grey'
    """
    min_colours = {}
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
        get_color_name((0, 0, 0))  # Returns 'black'
        get_color_name((128, 128, 128))  # Returns 'grey'
    """
    try:
        # Convert RGB to hex
        hex_value = webcolors.rgb_to_hex(rgb_tuple)
        # Get the color name directly
        return webcolors.hex_to_name(hex_value)
    except ValueError:
        # If exact match not found, find the closest color
        return closest_color(rgb_tuple)
    
def get_color_name_rgb(rgb_str):
    """
    Convert a CSS RGB string to a color name.
    
    Parses a string in format 'rgb(r,g,b)' and converts it to a CSS3 color name.
    
    Args:
        rgb_str (str): RGB color string in format 'rgb(r,g,b)'
        
    Returns:
        str: The CSS3 color name
        
    Example:
        get_color_name_rgb('rgb(0,0,0)')  # Returns 'black'
    """
    try:
        if not rgb_str.startswith("rgb(") or not rgb_str.endswith(")"):
            raise ValueError("Invalid RGB string format")
        
        rgb = rgb_str.replace("rgb(","")
        rgb = rgb.replace(")","")
        rgb = rgb.split(",")
        
        if len(rgb) != 3:
            raise ValueError("RGB string must contain exactly 3 values")
            
        rgb = tuple(rgb)
        rgbValue = tuple(map(int, rgb))
        
        # Validate RGB values are in valid range
        if not all(0 <= x <= 255 for x in rgbValue):
            raise ValueError("RGB values must be between 0 and 255")
            
        return get_color_name(rgbValue)
    except (ValueError, TypeError) as e:
        logging.warning(f"Invalid RGB color string '%s': %s. Using default color 'black'.", rgb_str, e)
        return "black"
        
def set_group_attributes(elem):
    """Extract `shaper:` attributes from a group element and return them.

    Returns:
        list[str] | None: List of `shaper:...` attribute strings if present, otherwise None.

    Side effects:
        - Sets a new UUID on the element's `id` attribute.
        - Removes the original `serif:id` attribute from the element.
    """
    serifId = elem.attrib.get(SERIF_ID)
    attrs = None
    if serifId:
        serifIdWords = serifId.split()
        attrs = [s for s in serifIdWords if s.startswith("shaper:")]
        for s in attrs:
            validate_shaper_attributes(s)
    elem.set("id", str(uuid.uuid4()))
    elem.attrib.pop(SERIF_ID, None)
    return attrs


def svg_add_xmlns(elem):
    """Ensure the SVG root element declares the `shaper` and `serif` namespaces.

    The function is idempotent and will add the missing namespace declarations if necessary.
    """

    if 'xmlns:shaper' not in elem.attrib:
        logging.info("Adding xmlns:shaper=%s attribute to %s element.", nameSpaces['shaper'], local_name(elem))
        elem.set("xmlns:shaper", nameSpaces["shaper"])
    if 'xmlns:serif' not in elem.attrib:
        logging.info("Adding xmlns:serif=%s attribute to %s element.", nameSpaces['serif'], local_name(elem))
        elem.set("xmlns:serif", nameSpaces["serif"]) 

def validate_shaper_attributes(attribute):
    """
    Validate Shaper Origin attributes against allowed names and values.
    
    Checks if the attribute name is in the allowed set (gblShaperAttrNames)
    and if it's a cutType, validates against allowed cut types (gblShaperCutTypes).
    
    Args:
        attribute (str): Attribute string in format 'shaper:name=value'
    
    Global Variables Used:
        gblShaperAttrNames: Set of valid attribute names
        gblShaperCutTypes: Set of valid cut types
    
    Prints warnings for:
        - Unsupported attribute names
        - Unsupported cut types
        
    Example:
        validate_shaper_attributes('shaper:cutType=inside')  # Valid
        validate_shaper_attributes('shaper:unknown=value')   # Warning
    """
    global gblTree
    global grpShaperAttrs
    global gblShaperAttrNames
    global gblShaperCutTypes

    attrValues = attribute.split("=")
    attrName = attrValues[0].split(":")

    if attrName[1] in gblShaperAttrNames:
        if attrName[1] == "cutType":
            if attrValues[1] not in gblShaperCutTypes:
                logging.warning("Unsupported cut type - %s", attrValues[1])
    else:
        logging.warning("Unsupported shaper attribute - %s", attrName[1])


def svg_add_layer_attributes(elem):
    """
    Extract and add Shaper attributes from layer names to SVG elements.
    
    Processes the serif:id attribute (which contains the AD2 layer name)
    to find and validate shaper: attributes, then adds them to the element.
    
    Args:
        elem (ElementTree.Element): The SVG element to process
        
    Global Variables Used:
        nameSpaces: For getting the serif namespace
        
    Side Effects:
        Adds validated shaper: attributes to the element
        
    Example:
        A layer named "Circle - shaper:cutDepth=0.5in" will add
        the attribute cutDepth="0.5in" to the element.
    """
    serifId = elem.attrib.get(SERIF_ID)
    if not serifId:
        return
    serifIdWords = serifId.split()

    # Extract and validate shaper attributes
    shaperAttrs = [s for s in serifIdWords if s.startswith("shaper:")]
    for s in shaperAttrs:
        validate_shaper_attributes(s)

    # Add validated attributes to the element
    for shaperAttr in shaperAttrs:
        shaperList = shaperAttr.split("=")
        elem.set(shaperList[0], shaperList[1])

def svg_convert_attribute(elem):
    """
    Convert SVG style attributes to Shaper Origin cut types and fill values.
    
    Processes fill and stroke values from SVG elements and maps them to
    appropriate Shaper Origin cut types. Also handles combined fill/stroke
    scenarios and sets default values.
    
    Color Mapping Rules:
    - black fill, black stroke → outside cut
    - white fill, black stroke → inside cut
    - grey fill, no stroke → pocket cut
    - no fill, grey stroke → online cut
    - blue fill or blue stroke → guide
    - red fill or red stroke → anchor
    
    RGB Color References:
    - black:    rgb(0,0,0)
    - white:    rgb(255,255,255)
    - grey:     rgb(127,127,127)
    - blue:     rgb(0,104,255)
    - red:      rgb(255,0,0)
    
    Args:
        elem (ElementTree.Element): The SVG element to process
    
    Global Variables Used:
        nameSpaces: Dictionary of XML namespaces
    
    Side Effects:
        - Sets stroke-width attribute
        - Generates new UUID for id attribute
        - Removes serif:id attribute
        - Sets shaper:cutType attribute
        - Sets fill attribute
    """
    global gblTree
    global grpShaperAttrs
    global gblShaperAttrNames
    global gblShaperCutTypes

    # rgbValue = (0,0,0)
    rgbValue = None
    fillValue = None

    anchorRGBvalue = (255,0,0)

    cutTypes = {
            "black":"outside",
            "white":"inside",
            "grey":"pocket",
            "nonegrey":"online",
            "dodgerblue":"guide",
            "red":"anchor"
    }

    fillValues = {
            "outside":"#000000",
            "inside":"#FFFFFF",
            "pocket":"#7F7F7F",
            "guide":"#0068FF",
            "online":"none",
            "anchor":"#FF0000"
    }

    tag = elem.tag
    elem.set("stroke-width", "0.1")
    elem.set("id", str(uuid.uuid4()))
    elem.attrib.pop(SERIF_ID, None)
    style = elem.attrib.pop("style", None)

    style_dict = parse_style(style)
    fillValue = style_dict.get("fill")
    strokeValue = style_dict.get("stroke")

    # print(f"fill = {fillValue} stroke = {strokeValue}")      

    if fillValue and "rgb" in fillValue:
        fillValue = get_color_name_rgb(fillValue)

    if strokeValue and "rgb" in strokeValue:
        strokeValue = get_color_name_rgb(strokeValue)


    if fillValue and strokeValue:
        if fillValue == "none" and strokeValue == "grey":
            color_name = fillValue + strokeValue
        elif fillValue == "none" and strokeValue:
            color_name = strokeValue
        else:
            color_name = fillValue
    elif fillValue and not strokeValue:
        if fillValue == "none":
            color_name = "dodgerblue"
        else:
            color_name = fillValue  
    else:
        color_name = "black"
    # print(color_name)
    cutType = cutTypes[color_name]
    fillValue = fillValues[cutType]

    # print(f"cutype = {cutType} fillValue = {fillValue}")
    
    elem.set("shaper:cutType",cutType)
    elem.set("fill",fillValue)


def svg_add_other_attributes(elem, attributes):
    """
    Add additional Shaper attributes to an SVG element.
    
    Adds attributes from a list if they don't already exist on the element.
    Used for both group-level and global attributes.
    
    Args:
        elem (ElementTree.Element): The SVG element to modify
        attributes (list): List of attribute strings in format 'shaper:name=value'
    
    Global Variables Used:
        None
    
    Example:
        svg_add_other_attributes(elem, ['shaper:cutDepth=0.5in'])
    """
    elemKeys = elem.keys()
    # print(attributes)
    for shaperAttr in attributes:
        attrValues = shaperAttr.split("=")
        if attrValues[0] not in elemKeys:
            shaperList = shaperAttr.split("=")
            # print(shaperList)
            elem.set(shaperList[0],shaperList[1])

def svg_add_attribute(elem, group_attrs=None):
    """Process a non-group SVG element: add layer attributes, group attrs, global attrs, then convert styles."""
    svg_add_layer_attributes(elem)

    if group_attrs:
        svg_add_other_attributes(elem, group_attrs)
    if gblShaperAttrs:
        svg_add_other_attributes(elem, gblShaperAttrs)
    svg_convert_attribute(elem)
   
# Define and get the command line options

# initiate the parser

def main():
    parser = argparse.ArgumentParser(description="Shaper Origin Support for AD2")

    # Add the argument options
    parser.add_argument("-i","--inFile",help="input SVG file(s)",action="store",nargs='+',required=True)
    parser.add_argument("-o","--outFile",help="output SVG file or directory",action="store",required=False)
    parser.add_argument("-g","--gblAttr",help="input global shaper attributes (optional)",action="store",required=False,nargs='*')

    # read arguments from the command line
    args = parser.parse_args()

    # If multiple files and output is specified, it must be a directory
    if len(args.inFile) > 1 and args.outFile:
        if not os.path.isdir(args.outFile):
            logging.error("When processing multiple files, output (-o) must be a directory")
            sys.exit(1)

    # Expand wildcards from input patterns
    expanded_files = []
    for pattern in args.inFile:
        expanded_files.extend(glob.glob(pattern))

    # Separate valid SVG files from others and warn about invalid ones
    valid_svg_files = []
    for f in expanded_files:
        if f.lower().endswith('.svg'):
            valid_svg_files.append(f)
        else:
            logging.warning("Skipping non-SVG file: %s", f)

    if not expanded_files:
        logging.error("No files found matching the input pattern(s): %s", ' '.join(args.inFile))
        sys.exit(1)

    # Check if there are any valid files to process
    if not valid_svg_files:
        logging.error("No valid SVG files found to process.")
        sys.exit(1)

    # We think we should register some name spaces
    ET.register_namespace('',nameSpaces["w3"])
    ET.register_namespace("serif",nameSpaces["serif"])
    ET.register_namespace("shaper",nameSpaces["shaper"])

    # validate global attributes
    if args.gblAttr:
        # store in the module-level global so processing functions can see it
        global gblShaperAttrs
        gblShaperAttrs = []
        for token in args.gblAttr:
            # handle either a single quoted string or multiple tokens
            gblShaperAttrs.extend(token.split())
        logging.info("Global shaper attributes: %s", gblShaperAttrs)
        for s in gblShaperAttrs:
            if "shaper:" in s:
                validate_shaper_attributes(s)

    # Process each matching file
    for input_file in valid_svg_files:
        try:
            # Skip files that have already been converted
            if "-converted" in input_file:
                continue

            # Verify input file exists and is readable
            if not os.path.isfile(input_file):
                logging.error("Input file '%s' does not exist", input_file)
                continue

            if not os.access(input_file, os.R_OK):
                logging.error("No read permission for input file '%s'", input_file)
                continue

            # Generate output filename
            if args.outFile and len(args.inFile) == 1:
                output_file = args.outFile
            else:
                # Split the filename and extension
                base_name, ext = os.path.splitext(input_file)
                filename = os.path.basename(base_name)
                if args.outFile:  # args.outFile is a directory path
                    output_file = os.path.join(args.outFile, f"{filename}-converted{ext}")
                else:
                    output_file = f"{base_name}-converted{ext}"

            # Get the input file and parse the tree
            logging.info("Reading and parsing %s", input_file)
            gblTree = ET.parse(input_file)

            # Process the current file
            group_attrs = None
            for elem in gblTree.iter():
                name = local_name(elem)
                if name == 'svg':
                    svg_add_xmlns(elem)
                elif name == 'g':
                    group_attrs = set_group_attributes(elem)
                else:
                    svg_add_attribute(elem, group_attrs)

            logging.info("Writing %s", output_file)
            gblTree.write(output_file)

        except ET.ParseError as e:
            logging.error("Error processing %s: %s", input_file, e)
            continue
        finally:
            # Clean up global variables
            gblTree = None
            grpShaperAttrs = None


if __name__ == '__main__':
    main()
