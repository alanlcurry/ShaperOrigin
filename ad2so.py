#!/usr/local/bin/python3

# MIT License

# Copyright (c) 2023  Alan L. Curry

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

# This routine reads a Affinity Designer 2 generated SVG file and adds Shaper Tools shaper: 
# attributes if present in the serif:id

# usage: ad2so.py [-h] -I INFILE -O OUTFILE [-G [GBLATTR ...]]

# Shaper Origin Support for AD2

# options:
#   -h, --help            show this help message and exit
#   -I INFILE, --inFile INFILE
#                         input SVG file
#   -O OUTFILE, --outFile OUTFILE
#                         output SVG file
#   -G [GBLATTR ...], --gblAttr [GBLATTR ...]
#                         input global shaper attributes (optional)

import xml.etree.ElementTree as ET
import argparse
import sys

gblTree = None
gblShaperAttrs = None
grpShaperAttrs = None

nameSpaces = {
                "w3":"http://www.w3.org/2000/svg",
                "serif":"http://www.serif.com/",
                "shaper":"http://www.shapertools.com/namespaces/shaper"
            }

def set_group_attributes(elem):
    '''
        Extracts and adds the shaper: attributes to the element.
    '''    
    
    global grpShaperAttrs

    serifNameSpace = "{" + nameSpaces["serif"] + "}id"

    try:
        serifId = elem.attrib[serifNameSpace]
        serifIdWords = serifId.split()
        grpShaperAttrs = [s for s in serifIdWords if "shaper:" in s]
    except KeyError:
        grpShaperAttrs = None  

def svg_add_xmlns(elem):
    '''
        Adds the shaper namespace to the SVG element
    '''    

    global gblTree

    print(f"Adding xmlns:shaper={nameSpaces['shaper']} attribute to {elem.tag[-3:]} element....")
    elem.set("xmlns:shaper",nameSpaces["shaper"])


def svg_add_attribute(elem):
    
    global gblTree

    serifNameSpace = "{" + nameSpaces["serif"] + "}id"

    try:
        if gblShaperAttrs:
            for shaperAttr in gblShaperAttrs:
                shaperList = shaperAttr.split("=")
                elem.set(shaperList[0],shaperList[1])

        serifId = elem.attrib[serifNameSpace]
        serifIdWords = serifId.split()
        shaperAttrs = [s for s in serifIdWords if "shaper:" in s]

        for shaperAttr in shaperAttrs:
            shaperList = shaperAttr.split("=")
            elem.set(shaperList[0],shaperList[1])

    except KeyError:
        if grpShaperAttrs:
            for shaperAttr in grpShaperAttrs:
                shaperList = shaperAttr.split("=")
                elem.set(shaperList[0],shaperList[1])
    finally:
        pass


 
# Define and get the command line options

# initiate the parser

parser = argparse.ArgumentParser(description="Shaper Origin Support for AD2")

# Add the argument options

parser.add_argument("-I","--inFile",help="input SVG file",action="store",required=True)
parser.add_argument("-O","--outFile",help="output SVG file",action="store",required=True)
parser.add_argument("-G","--gblAttr",help="input global shaper attributes (optional)",action="store",required=False,nargs='*')

# read arguments from the command line

args = parser.parse_args()

if args.gblAttr:
    gblShaperAttrs = args.gblAttr
 
# We think we should register some name spaces

ET.register_namespace('',nameSpaces["w3"])
ET.register_namespace("serif",nameSpaces["serif"])
ET.register_namespace("shaper",nameSpaces["shaper"])

# Get the input file and parse the tree
print(f"Reading and parsing {args.inFile}....")
gblTree = ET.parse(args.inFile)

# iterate through the elements

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

print(f"Writing {args.outFile}....")
gblTree.write(args.outFile)
