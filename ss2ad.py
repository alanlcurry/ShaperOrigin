#!/usr/local/bin/python3

# MIT License

# Copyright (c) 2025  Alan L. Curry

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

# This module processes Shaper Studio SVG files to convert them back to Affinity Designer 2 (AD2) format.
# It reads shaper: attributes from SVG elements and concatenates them into the ID field that AD2 uses for
# layer names.
#
# Key Features:
# - Reads SVG files with Shaper Studio attributes
# - Converts shaper: attributes into AD2 layer names
# - Preserves essential SVG structure
# - Maintains compatibility with AD2 format
# - Supports wildcard patterns for batch processing
#
# Usage: 
#   ss2ad.py [-h] -i INFILE [-o OUTFILE]
#
# Examples:
#   Single file:
#     python3 ss2ad.py -i input.svg -o output.svg
#   
#   Wildcards (batch processing):
#     python3 ss2ad.py -i "*.svg"                # Process all SVG files in current directory
#     python3 ss2ad.py -i "*.svg" -o output_dir  # Process all SVG files into output_dir
#     python3 ss2ad.py -i "dir/*.svg"            # Process all SVG files in specific directory
#     python3 ss2ad.py -i "**/*.svg"             # Process SVG files in all subdirectories
#
# Options:
#   -h, --help            Show this help message and exit
#   -i INFILE, --inFile INFILE
#                         Input SVG file(s) from Shaper Studio. Supports wildcards (*, ?)
#   -o OUTFILE, --outFile OUTFILE
#                         Output path (optional). For single files, specifies output file.
#                         For wildcards, must be a directory. If omitted, creates files
#                         with '-converted' suffix in same location as input files.

import xml.etree.ElementTree as ET
import argparse
import sys
import glob
import os.path
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)

# XML namespaces used in SVG processing
nameSpaces = {
    "w3": "http://www.w3.org/2000/svg",
    "serif": "http://www.serif.com/",
    "shaper": "http://www.shapertools.com/namespaces/shaper"
}

def local_name(elem):
    """Return the local tag name (without namespace)."""
    tag = elem.tag
    if isinstance(tag, str) and '}' in tag:
        return tag.rsplit('}', 1)[-1]
    return tag


def convert_attributes_to_id(elem):
    """
    Convert Shaper Studio attributes to ID string.
    
    Finds all attributes in the shaper namespace and concatenates them
    into a space-separated string to be used as the element's ID.
    
    Args:
        elem (ElementTree.Element): The SVG element to process
        
    Returns:
        None - modifies element in place by:
        1. Converting shaper namespace attributes to space-separated string
        2. Setting that string as the element's id attribute
        3. Removing the original shaper attributes
    """
    # Get all attributes in the shaper namespace
    shaper_ns = "{" + nameSpaces["shaper"] + "}"
    shaper_attrs = []
    # Store attributes to remove to avoid modifying dict during iteration
    attrs_to_remove = []
    
    for qname, value in elem.attrib.items():
        # Check if attribute is in shaper namespace
        if qname.startswith(shaper_ns):
            # Get the local name of the attribute without namespace
            attr_local_name = qname.split("}")[-1]
            value = value.replace(" ", "")
            # Format as shaper:name=value
            shaper_attrs.append(f"shaper:{attr_local_name}={value}")
            attrs_to_remove.append(qname)
    
    if shaper_attrs:
        # Create the new ID by joining all shaper attributes with spaces
        new_id = " ".join(shaper_attrs)
        # Set the ID attribute directly (overwrites existing per design spec)
        elem.set("id", new_id)
        # Remove the original shaper attributes
        for attr in attrs_to_remove:
            elem.attrib.pop(attr)

def process_svg(tree):
    """
    Process all elements in the SVG tree.
    
    Walks through all elements in the SVG tree and converts
    shaper attributes to ID attributes while preserving the
    shaper namespace.
    
    Args:
        tree (ElementTree): The SVG document tree to process
        
    Returns:
        None - modifies tree in place
    """
    # Process each element in the tree
    for elem in tree.iter():
        # Skip the root SVG element
        if local_name(elem).lower() != 'svg':
            # Convert shaper attributes to ID for non-root elements
            convert_attributes_to_id(elem)
            
def main():
    """
    Main function for processing SVG files.
    
    Handles command line arguments and processes each input file
    to convert shaper attributes into AD2 layer names.
    """
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Convert Shaper Studio SVG to AD2 format")
    parser.add_argument("-i","--inFile",help="Input SVG file(s)",action="store",nargs='+',required=True)
    parser.add_argument("-o", "--outFile", help="Output SVG file (optional)", required=False)
    
    # If no arguments are provided, show help and exit
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # read arguments from the command line

    args = parser.parse_args()

    # If multiple files and output is specified, it must be a directory
    if len(args.inFile) > 1 and args.outFile:
        if not os.path.isdir(args.outFile):
            logging.error("When processing multiple files, output (-o) must be a directory")
            sys.exit(1)
    
    # Expand patterns from input
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
    
    # Register namespaces
    ET.register_namespace('', nameSpaces["w3"])
    ET.register_namespace("serif", nameSpaces["serif"])
    ET.register_namespace("shaper", nameSpaces["shaper"])
    
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
            if args.outFile and len(valid_svg_files) == 1:
                output_file = args.outFile
            else:
                # Split the filename and extension
                base_name, ext = os.path.splitext(input_file)
                filename = os.path.basename(base_name)
                if args.outFile:  # args.outFile is a directory path
                    output_file = os.path.join(args.outFile, f"{filename}-converted{ext}")
                else:
                    output_file = f"{base_name}-converted{ext}"
            
            # Parse and process the SVG file
            logging.info("Reading and parsing %s....", input_file)
            tree = ET.parse(input_file)
        
            process_svg(tree)
            
            # Write the processed file
            logging.info("Writing %s....", output_file)
            tree.write(output_file)
            
        except ET.ParseError as e:
            logging.error("Error processing %s: %s", input_file, e)
            continue

if __name__ == "__main__":
    main()
