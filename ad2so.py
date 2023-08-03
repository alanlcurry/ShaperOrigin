import xml.etree.ElementTree as ET
import argparse
import os

"""
Defines and gets the command line options
"""              

# Define and get the command line options

# initiate the parser

parser = argparse.ArgumentParser(description="Shaper Origin Support for AD2")

# Add the argument options

parser.add_argument("-in","--inFile",help="input SVG file",action="store")
parser.add_argument("-out","--outFile",help="output SVG file",action="store")

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
        elem.set("xmlns:shaper","http://www.shapertools.com/namespaces/shaper")
    if ("path" in elem.tag[-4:]):
        try:
            serifId = elem.attrib["{http://www.serif.com/}id"]
            serifIdWords = serifId.split()
            shaperAttrs = [s for s in serifIdWords if "so:" in s]
            for shaperAttr in shaperAttrs:
                shaperList = shaperAttr.split("=")
                elem.set(shaperList[0],shaperList[1])
        except:
            continue

tree.write(args.outFile)

# tempList = args.outFile.split(".")
# tempOutFile = tempList[0] + "_temp." + tempList[1]
# tree.write(tempOutFile)

# with open(tempOutFile) as svgFileIn:

#     svgFileOut = open(args.outFile,"+tw")

#     lines = svgFileIn.read().splitlines()
#     for line in lines:
#         # print(line)
#         if "svg:" in line:
#             line = line.replace("svg:","")
#         svgFileOut.write(line)
    
#     svgFileOut.close()

# if os.path.exists(tempOutFile):
#     os.remove(tempOutFile)
# else:
#     print(f"{tempOutFile} does not exist. This should not happen.")
        
