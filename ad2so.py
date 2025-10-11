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
        print(f"Warning: Invalid RGB color string '{rgb_str}': {str(e)}. Using default color 'black'.")
        return "black"
        
def set_group_attributes(elem):
    '''
        Extracts and adds the shaper: attributes to grpShaperAttrs 
    '''    
    
    global gblTree
    global grpShaperAttrs
    global gblShaperAttrNames
    global gblShaperCutTypes

    serifNameSpace = "{" + nameSpaces["serif"] + "}id"
          
    try:
        serifId = elem.attrib[serifNameSpace]
        serifIdWords = serifId.split()

        # grpShaperAttrs = [s for s in serifIdWords if "shaper:" in s]
        grpShaperAttrs = []
        for s in serifIdWords:
            if "shaper:" in s:
                validate_shaper_attributes(s)
                grpShaperAttrs.append(s)

    except KeyError:
        grpShaperAttrs = None
    finally:
        elem.set("id",str(uuid.uuid4()))
        elem.attrib.pop(serifNameSpace,None)


def svg_add_xmlns(elem):
    '''
        Adds the shaper namespace to the SVG element if it doesn't exist
    '''    

    global gblTree
    global grpShaperAttrs
    global gblShaperAttrNames
    global gblShaperCutTypes

    if 'xmlns:shaper' not in elem.attrib:
        print(f"Adding xmlns:shaper={nameSpaces['shaper']} attribute to {elem.tag[-3:]} element....")
        elem.set("xmlns:shaper",nameSpaces["shaper"])

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
                print(f"Warning: Unsupported cut type - {attrValues[1]} .")
    else:
        print(f"Warning: Unsupported shaper attribute - {attrName[1]} .")


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
    global gblTree
    global grpShaperAttrs
    global gblShaperAttrNames
    global gblShaperCutTypes

    serifNameSpace = "{" + nameSpaces["serif"] + "}id"
    serifId = elem.attrib[serifNameSpace]
    serifIdWords = serifId.split()

    # Extract and validate shaper attributes
    shaperAttrs = []
    for s in serifIdWords:
        if "shaper:" in s:
            validate_shaper_attributes(s)
            shaperAttrs.append(s)

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
    - black → outside cut
    - white → inside cut
    - grey → pocket cut
    - none+grey → online cut
    - dodgerblue → guide
    - red → anchor
    
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

    serifNameSpace = "{" + nameSpaces["serif"] + "}id"
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

    elem.set("stroke-width","0.1")
    elem.set("id",str(uuid.uuid4()))
    elem.attrib.pop(serifNameSpace,None)
    style = elem.attrib.pop("style",None)

    fillValue = None
    strokeValue = None

    if style:
        styleEntries = style.split(';')

        for item in styleEntries:
            splitIt = item.split(":")
            if splitIt[0] == "fill":
                fillValue = splitIt[1]
            if splitIt[0] == "stroke":
                strokeValue = splitIt[1]

    # print(f"fill = {fillValue} stroke = {strokeValue}")      

    if fillValue:
        if "rgb" in fillValue:
            fillValue = get_color_name_rgb(fillValue)

    if strokeValue:
        if "rgb" in strokeValue:
            strokeValue = get_color_name_rgb(strokeValue)
    
    # print(f"fill = {fillValue} stroke = {strokeValue}") 
    # print("")

    if fillValue and strokeValue:
        if fillValue == "none" and strokeValue == "grey":
            color_name = fillValue + strokeValue
        elif fillValue == "none" and strokeValue:
            color_name = strokeValue
        else:
            color_name = fillValue
    elif fillValue and not strokeValue:
        color_name = fillValue  
    else:
        color_name = "black"

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
    global gblTree
    global grpShaperAttrs
    global gblShaperAttrNames
    global gblShaperCutTypes

    elemKeys = elem.keys()
    # print(attributes)
    for shaperAttr in attributes:
        attrValues = shaperAttr.split("=")
        if attrValues[0] not in elemKeys:
            shaperList = shaperAttr.split("=")
            # print(shaperList)
            elem.set(shaperList[0],shaperList[1])

def svg_add_attribute(elem):
    """
    Main attribute processing function for SVG elements.
    
    Coordinates the entire attribute processing workflow for an element:
    1. Attempts to add layer-specific attributes
    2. Applies any inherited group attributes
    3. Applies any global attributes
    4. Converts style/color attributes to Shaper cut types
    
    Args:
        elem (ElementTree.Element): The SVG element to process
        
    Global Variables Used:
        grpShaperAttrs: Group-level attributes to inherit
        gblShaperAttrs: Global attributes to apply
        
    Side Effects:
        - Adds layer attributes if present
        - Applies group attributes if any
        - Applies global attributes if any
        - Converts color attributes to cut types
    """
    global gblTree
    global grpShaperAttrs
    global gblShaperAttrNames
    global gblShaperCutTypes

    serifNameSpace = "{" + nameSpaces["serif"] + "}id"

    try:
        svg_add_layer_attributes(elem)
    except:
        pass

    finally:
        if grpShaperAttrs:           
            svg_add_other_attributes(elem, grpShaperAttrs)
        if gblShaperAttrs:
            svg_add_other_attributes(elem, gblShaperAttrs)
        svg_convert_attribute(elem)
   
# Define and get the command line options

# initiate the parser

parser = argparse.ArgumentParser(description="Shaper Origin Support for AD2")

# Add the argument options

parser.add_argument("-i","--inFile",help="input SVG file",action="store",required=True)
parser.add_argument("-o","--outFile",help="output SVG file",action="store",required=False)
parser.add_argument("-g","--gblAttr",help="input global shaper attributes (optional)",action="store",required=False,nargs='*')

# read arguments from the command line

args = parser.parse_args()

# Check if input pattern contains wildcards
has_wildcards = '*' in args.inFile or '?' in args.inFile

# If wildcards are used and output is specified, it must be a directory
if has_wildcards and args.outFile:
    if not os.path.isdir(args.outFile):
        print("Error: When using wildcards, output (-o) must be a directory")
        sys.exit(1)

# Find all matching input files
input_files = glob.glob(args.inFile)

if not input_files:
    print(f"Error: No files found matching pattern: {args.inFile}")
    sys.exit(1)

# Filter for SVG files only
input_files = [f for f in input_files if f.lower().endswith('.svg')]

if not input_files:
    print(f"Error: No SVG files found matching pattern: {args.inFile}")
    sys.exit(1)

# We think we should register some name spaces
ET.register_namespace('',nameSpaces["w3"])
ET.register_namespace("serif",nameSpaces["serif"])
ET.register_namespace("shaper",nameSpaces["shaper"])

# validate global attributes
if args.gblAttr:
    gblShaperAttrs = args.gblAttr[0].split(" ")
    for s in gblShaperAttrs:
        if "shaper:" in s:
            validate_shaper_attributes(s)

# Process each matching file
for input_file in input_files:
    try:
        # Skip files that have already been converted
        if "-converted" in input_file:
            continue
            
        # Verify input file exists and is readable
        if not os.path.isfile(input_file):
            print(f"Error: Input file '{input_file}' does not exist")
            continue
            
        if not os.access(input_file, os.R_OK):
            print(f"Error: No read permission for input file '{input_file}'")
            continue
            
        # Generate output filename
        if args.outFile and not has_wildcards:
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
        print(f"Reading and parsing {input_file}....")
        gblTree = ET.parse(input_file)

        # Process the current file
        for elem in gblTree.iter():
            # add the namespace
            if "svg" in elem.tag[-3:]:
                svg_add_xmlns(elem)
            # group level? 
            elif "g" in elem.tag[-1:]:
                set_group_attributes(elem)
            else:
                # check and add the attributes
                svg_add_attribute(elem)
                
        print(f"Writing {output_file}....")
        gblTree.write(output_file)

    except ET.ParseError as e:
        print(f"Error processing {input_file}: {e}")
        continue
    finally:
        # Clean up global variables
        gblTree = None
        grpShaperAttrs = None

