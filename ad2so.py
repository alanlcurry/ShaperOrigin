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
#   -i INFILE, --inFile INFILE
#                         input SVG file
#   -o OUTFILE, --outFile OUTFILE
#                         output SVG file
#   -g [GBLATTR ...], --gblAttr [GBLATTR ...]
#                         input global shaper attributes (optional)

import xml.etree.ElementTree as ET
import argparse
import sys
import uuid
import webcolors

gblTree = None
gblShaperAttrs = None
grpShaperAttrs = None
gblShaperAttrNames = {"cutDepth", "toolDia", "cutOffset", "cutType"}
gblShaperCutTypes = {"guide", "inside", "outside","pocket"}

# shaper:cutType="guide" shaper:cutOffset="0in" shaper:toolDia="0.125in"
# shaper:cutType="outside" shaper:cutOffset="0in" shaper:toolDia="0.125in"
# shaper:cutType="pocket"
# shaper:cutType="inside"

nameSpaces = {
                "w3":"http://www.w3.org/2000/svg",
                "serif":"http://www.serif.com/",
                "shaper":"http://www.shapertools.com/namespaces/shaper"
            }

def closest_color(requested_colour):
    min_colours = {}
    for name in webcolors.names("css3"):
        r_c, g_c, b_c = webcolors.name_to_rgb(name)
        rd = (r_c - requested_colour[0]) ** 2
        gd = (g_c - requested_colour[1]) ** 2
        bd = (b_c - requested_colour[2]) ** 2
        min_colours[(rd + gd + bd)] = name
    return min_colours[min(min_colours.keys())]

def get_color_name(rgb_tuple):
    try:
        # Convert RGB to hex
        hex_value = webcolors.rgb_to_hex(rgb_tuple)
        # Get the color name directly
        return webcolors.hex_to_name(hex_value)
    except ValueError:
        # If exact match not found, find the closest color
        return closest_color(rgb_tuple)
    
def get_color_name_rgb(rgb_str):
    # print(rgb_str)
    # rgb = rgb_str.split(":")
    # rgb = rgb[1]
    rgb = rgb_str.replace("rgb(","")
    rgb = rgb.replace(")","")
    rgb = rgb.split(",")
    rgb = tuple(rgb)
    rgbValue = tuple(map(int, rgb))

    return get_color_name(rgbValue)
        
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
        Adds the shaper namespace to the SVG element
    '''    

    global gblTree
    global grpShaperAttrs
    global gblShaperAttrNames
    global gblShaperCutTypes

    print(f"Adding xmlns:shaper={nameSpaces['shaper']} attribute to {elem.tag[-3:]} element....")
    elem.set("xmlns:shaper",nameSpaces["shaper"])

def validate_shaper_attributes(attribute):

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

    global gblTree
    global grpShaperAttrs
    global gblShaperAttrNames
    global gblShaperCutTypes

    serifNameSpace = "{" + nameSpaces["serif"] + "}id"

    serifId = elem.attrib[serifNameSpace]
    serifIdWords = serifId.split()

    # shaperAttrs = [s for s in serifIdWords if "shaper:" in s]
    shaperAttrs = []
    for s in serifIdWords:
        if "shaper:" in s:
            validate_shaper_attributes(s)
            shaperAttrs.append(s)

    for shaperAttr in shaperAttrs:
        shaperList = shaperAttr.split("=")
        elem.set(shaperList[0],shaperList[1])

def svg_convert_attribute(elem):

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


def svg_add_other_attributes(elem,attributes):

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
        # print(f"here {grpShaperAttrs}")
        if grpShaperAttrs:           
            svg_add_other_attributes(elem,grpShaperAttrs)
        if gblShaperAttrs:
            svg_add_other_attributes(elem,gblShaperAttrs)
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

# Validate input file extension
if not args.inFile.lower().endswith('.svg'):
    print(f"Error: Input file must be an SVG file. Got: {args.inFile}")
    sys.exit(1)
 
# We think we should register some name spaces

ET.register_namespace('',nameSpaces["w3"])
ET.register_namespace("serif",nameSpaces["serif"])
ET.register_namespace("shaper",nameSpaces["shaper"])

# Get the input file and parse the tree
print(f"Reading and parsing {args.inFile}....")
gblTree = ET.parse(args.inFile)


# validate global attributes

if args.gblAttr:
    gblShaperAttrs = args.gblAttr[0].split(" ")
    for s in gblShaperAttrs:
        if "shaper:" in s:
            validate_shaper_attributes(s)

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

if ( args.outFile == None):
    args.outFile = args.inFile

gblTree.write(args.outFile)

