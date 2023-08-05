import xml.etree.ElementTree as ET
import argparse

tree = None

def svg_svg(elem):

    global tree

    elem.set("xmlns:shaper","http://www.shapertools.com/namespaces/shaper")

def svg_path(elem):

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

def svg_g(elem):

    global tree
    pass

def svg_g_frame_text_tool(elem):
    
    global tree

    serifId = elem.attrib["{http://www.serif.com/}id"]
    serifIdWords = serifId.split()
    shaperAttrs = [s for s in serifIdWords if "shaper:" in s]

    for child in elem.iter():
   
        if "path" in child.tag[-4:]:
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

for elem in tree.iter():
    if "svg" in elem.tag[-3:]:
        svg_svg(elem)
    if "path" in elem.tag[-4:]:
        svg_path(elem)     
    if "g" in elem.tag[-1:]:
        try:
            serifId = elem.attrib["{http://www.serif.com/}id"]
            if "Frame Text Tool" in serifId:
                svg_g_frame_text_tool(elem)
        except KeyError: 
            pass

tree.write(args.outFile)