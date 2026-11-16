"""Convert Shaper Studio SVGs back to Affinity layer ids.

Shaper attributes are concatenated into each element's ``id``, which Affinity
shows as the layer name.
"""

import argparse
import glob
import logging
import os
import os.path
import sys
import xml.etree.ElementTree as ET

from shaperorigin.namespaces import SHAPER_NS, nameSpaces
from shaperorigin.xmlutil import local_name


def convert_attributes_to_id(elem):
    """Move Shaper namespace attributes into the element's id.

    Args:
        elem: SVG element modified in place. Shaper attributes become a
            space-separated ``shaper:name=value`` id, then are removed.
    """
    shaper_attrs = []
    attrs_to_remove = []

    for qname, value in elem.attrib.items():
        if qname.startswith(SHAPER_NS):
            attr_local_name = qname.split("}")[-1]
            value = value.replace(" ", "")
            shaper_attrs.append(f"shaper:{attr_local_name}={value}")
            attrs_to_remove.append(qname)

    if shaper_attrs:
        elem.set("id", " ".join(shaper_attrs))
        for attr in attrs_to_remove:
            elem.attrib.pop(attr)


def process_svg(tree):
    """Convert shaper attributes to ids on every element except the root.

    Args:
        tree: SVG document tree modified in place. The root ``svg`` element
            is left unchanged so the namespace declaration stays put.
    """
    for elem in tree.iter():
        if local_name(elem).lower() != "svg":
            convert_attributes_to_id(elem)


def main():
    """Parse arguments and convert each input SVG."""
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Convert Shaper Studio SVG to Affinity format")
    parser.add_argument("-i", "--inFile", help="Input SVG file(s)", action="store", nargs="+", required=True)
    parser.add_argument("-o", "--outFile", help="Output SVG file (optional)", required=False)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    if len(args.inFile) > 1 and args.outFile:
        if not os.path.isdir(args.outFile):
            logging.error("When processing multiple files, output (-o) must be a directory")
            sys.exit(1)

    expanded_files = []
    for pattern in args.inFile:
        expanded_files.extend(glob.glob(pattern))

    valid_svg_files = []
    for path in expanded_files:
        if path.lower().endswith(".svg"):
            valid_svg_files.append(path)
        else:
            logging.warning("Skipping non-SVG file: %s", path)

    if not expanded_files:
        logging.error("No files found matching the input pattern(s): %s", " ".join(args.inFile))
        sys.exit(1)

    if not valid_svg_files:
        logging.error("No valid SVG files found to process.")
        sys.exit(1)

    ET.register_namespace("", nameSpaces["w3"])
    ET.register_namespace("serif", nameSpaces["serif"])
    ET.register_namespace("shaper", nameSpaces["shaper"])

    for input_file in valid_svg_files:
        try:
            if "-converted" in input_file:
                continue

            if not os.path.isfile(input_file):
                logging.error("Input file '%s' does not exist", input_file)
                continue

            if not os.access(input_file, os.R_OK):
                logging.error("No read permission for input file '%s'", input_file)
                continue

            if args.outFile and len(valid_svg_files) == 1:
                output_file = args.outFile
            else:
                base_name, ext = os.path.splitext(input_file)
                filename = os.path.basename(base_name)
                if args.outFile:
                    output_file = os.path.join(args.outFile, f"{filename}-converted{ext}")
                else:
                    output_file = f"{base_name}-converted{ext}"

            logging.info("Reading and parsing %s....", input_file)
            tree = ET.parse(input_file)

            process_svg(tree)

            logging.info("Writing %s....", output_file)
            tree.write(output_file)

        except ET.ParseError as exc:
            logging.error("Error processing %s: %s", input_file, exc)
            continue


if __name__ == "__main__":
    main()
