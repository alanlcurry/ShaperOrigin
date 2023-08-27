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

# Shaper Origin Support for AD2

# usage: ad2so.py [-h] -in INFILE -out OUTFILE
# options:
#   -h, --help            show this help message and exit
#   -in INFILE, --inFile INFILE
#                         input SVG file
#   -out OUTFILE, --outFile OUTFILE
#                         output SVG file

import xml.etree.ElementTree as ET
import argparse

tree = None

def svg_add_xmlns(elem):
    '''
        Adds the Shaper Tools xml namespace to the SVG element.
    '''

    global tree

    elem.set("xmlns:shaper","http://www.shapertools.com/namespaces/shaper")

def svg_add_attribute(elem):
    '''
        Extracts and adds the shaper: attributes to the element.
    '''    

    global tree

    try:
        serifId = elem.attrib["{http://www.serif.com/}id"]
        serifIdWords = serifId.split()
        shaperAttrs = [s for s in serifIdWords if "shaper:" in s]
        for shaperAttr in shaperAttrs:
            shaperList = shaperAttr.split("=")
            elem.set(shaperList[0],shaperList[1])
    except:
        pass

def svg_frame_text_tool(elem):
    '''
        Form text tool must be in a group. Extracts and adds the shaper: attributes 
        to the child elements.
        Yea, yea, I know.... there's some duplicate code. 
    '''    
    
    global tree

    serifId = elem.attrib["{http://www.serif.com/}id"]
    serifIdWords = serifId.split()
    shaperAttrs = [s for s in serifIdWords if "shaper:" in s]

    for child in elem.iter():
        for shaperAttr in shaperAttrs:
            shaperList = shaperAttr.split("=")
            child.set(shaperList[0],shaperList[1])
                


# Define and get the command line options

# initiate the parser

parser = argparse.ArgumentParser(description="Shaper Origin Support for AD2")

# Add the argument options

parser.add_argument("-in","--inFile",help="input SVG file",action="store",required=True)
parser.add_argument("-out","--outFile",help="output SVG file",action="store",required=True)

# read arguments from the command line

args = parser.parse_args()

# We think we should register some name spaces

ET.register_namespace('',"http://www.w3.org/2000/svg")
ET.register_namespace('serif',"http://www.serif.com/")
ET.register_namespace('shaper',"http://www.shapertools.com/namespaces/shaper")

# Get the command line arguments

tree = ET.parse(args.inFile)

# iterate through the elements

for elem in tree.iter():
    # add the namespace
    if "svg" in elem.tag[-3:]:
        svg_add_xmlns(elem)
    else:
        # check and add the attributes
        try:
            serifId = elem.attrib["{http://www.serif.com/}id"]
            if "Frame Text Tool" in serifId:
                svg_frame_text_tool(elem)
            else:
                svg_add_attribute(elem)
        except KeyError: 
            pass

tree.write(args.outFile)