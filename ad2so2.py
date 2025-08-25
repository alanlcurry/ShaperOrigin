import xml.etree.ElementTree as ET
import argparse
import sys
import uuid
import webcolors

class ShaperSVGProcessor:
    nameSpaces = {
        "w3": "http://www.w3.org/2000/svg",
        "serif": "http://www.serif.com/",
        "shaper": "http://www.shapertools.com/namespaces/shaper"
    }
    gblShaperAttrNames = {"cutDepth", "toolDia", "cutOffset", "cutType"}
    gblShaperCutTypes = {"guide", "inside", "outside", "pocket"}

    def __init__(self, in_file, out_file=None, gbl_attrs=None):
        self.in_file = in_file
        self.out_file = out_file or in_file
        self.gblShaperAttrs = gbl_attrs
        self.grpShaperAttrs = None
        self.gblTree = None

    def closest_color(self, requested_colour):
        min_colours = {}
        for name in webcolors.names("css3"):
            r_c, g_c, b_c = webcolors.name_to_rgb(name)
            rd = (r_c - requested_colour[0]) ** 2
            gd = (g_c - requested_colour[1]) ** 2
            bd = (b_c - requested_colour[2]) ** 2
            min_colours[(rd + gd + bd)] = name
        return min_colours[min(min_colours.keys())]

    def get_color_name(self, rgb_tuple):
        try:
            hex_value = webcolors.rgb_to_hex(rgb_tuple)
            return webcolors.hex_to_name(hex_value)
        except ValueError:
            return self.closest_color(rgb_tuple)

    def get_color_name_rgb(self, rgb_str):
        rgb = rgb_str.replace("rgb(", "").replace(")", "").split(",")
        rgbValue = tuple(map(int, rgb))
        return self.get_color_name(rgbValue)

    def set_group_attributes(self, elem):
        serifNameSpace = "{" + self.nameSpaces["serif"] + "}id"
        try:
            serifId = elem.attrib[serifNameSpace]
            serifIdWords = serifId.split()
            self.grpShaperAttrs = [s for s in serifIdWords if "shaper:" in s and self.validate_shaper_attributes(s)]
        except KeyError:
            self.grpShaperAttrs = None
        finally:
            elem.set("id", str(uuid.uuid4()))
            elem.attrib.pop(serifNameSpace, None)

    def svg_add_xmlns(self, elem):
        print(f"Adding xmlns:shaper={self.nameSpaces['shaper']} attribute to {elem.tag[-3:]} element....")
        elem.set("xmlns:shaper", self.nameSpaces["shaper"])

    def validate_shaper_attributes(self, attribute):
        attrValues = attribute.split("=")
        attrName = attrValues[0].split(":")
        if attrName[1] in self.gblShaperAttrNames:
            if attrName[1] == "cutType" and attrValues[1] not in self.gblShaperCutTypes:
                print(f"Warning: Unsupported cut type - {attrValues[1]} .")
        else:
            print(f"Warning: Unsupported shaper attribute - {attrName[1]} .")
        return True

    def svg_add_layer_attributes(self, elem):
        serifNameSpace = "{" + self.nameSpaces["serif"] + "}id"
        serifId = elem.attrib[serifNameSpace]
        serifIdWords = serifId.split()
        shaperAttrs = [s for s in serifIdWords if "shaper:" in s and self.validate_shaper_attributes(s)]
        for shaperAttr in shaperAttrs:
            shaperList = shaperAttr.split("=")
            elem.set(shaperList[0], shaperList[1])

    def svg_convert_attribute(self, elem):
        
        cutTypeColors = {
            "black": "outside",
            "white": "inside",
            "grey": "pocket",
            "nonegrey": "online",
            "dodgerblue": "guide",
            "red": "anchor"
        }
        cutTypefillValues = {
            "outside": "#000000",
            "inside": "#FFFFFF",
            "pocket": "#7F7F7F",
            "guide": "#0068FF",
            "online": "none",
            "anchor": "#FF0000"
        }

        serifNameSpace = "{" + self.nameSpaces["serif"] + "}id"
  
        elem.set("stroke-width", "0.1")
        elem.set("id", str(uuid.uuid4()))
        elem.attrib.pop(serifNameSpace, None)
        style = elem.attrib.pop("style", None)
        fillValue = strokeValue = None
        if style:
            styleEntries = style.split(';')
            for item in styleEntries:
                splitIt = item.split(":")
                if splitIt[0] == "fill":
                    fillValue = splitIt[1]
                if splitIt[0] == "stroke":
                    strokeValue = splitIt[1]
        if fillValue and "rgb" in fillValue:
            fillValue = self.get_color_name_rgb(fillValue)
        if strokeValue and "rgb" in strokeValue:
            strokeValue = self.get_color_name_rgb(strokeValue)
        if fillValue and strokeValue:
            if fillValue == "none" and strokeValue == "grey":
                color_name = fillValue + strokeValue
            elif fillValue == "none" and strokeValue:
                color_name = strokeValue
            else:
                color_name = fillValue
        elif fillValue:
            color_name = fillValue
        else:
            color_name = "black"
        cutType = cutTypeColors[color_name]
        fillValue = cutTypefillValues[cutType]
        elem.set("shaper:cutType", cutType)
        elem.set("fill", fillValue)

    def svg_add_other_attributes(self, elem, attributes):
        elemKeys = elem.keys()
        for shaperAttr in attributes:
            attrValues = shaperAttr.split("=")
            if attrValues[0] not in elemKeys:
                shaperList = shaperAttr.split("=")
                elem.set(shaperList[0], shaperList[1])

    def svg_add_attribute(self, elem):
        serifNameSpace = "{" + self.nameSpaces["serif"] + "}id"
        try:
            self.svg_add_layer_attributes(elem)
        except Exception:
            pass
        finally:
            if self.grpShaperAttrs:
                self.svg_add_other_attributes(elem, self.grpShaperAttrs)
            if self.gblShaperAttrs:
                self.svg_add_other_attributes(elem, self.gblShaperAttrs)
            self.svg_convert_attribute(elem)

    def process(self):
        ET.register_namespace('', self.nameSpaces["w3"])
        ET.register_namespace("serif", self.nameSpaces["serif"])
        ET.register_namespace("shaper", self.nameSpaces["shaper"])
        print(f"Reading and parsing {self.in_file}....")
        self.gblTree = ET.parse(self.in_file)
        if self.gblShaperAttrs:
            for s in self.gblShaperAttrs:
                if "shaper:" in s:
                    self.validate_shaper_attributes(s)
        for elem in self.gblTree.iter():
            if "svg" in elem.tag[-3:]:
                self.svg_add_xmlns(elem)
            elif "g" in elem.tag[-1:]:
                self.set_group_attributes(elem)
            else:
                self.svg_add_attribute(elem)
        print(f"Writing {self.out_file}....")
        self.gblTree.write(self.out_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Shaper Origin Support for AD2")
    parser.add_argument("-i", "--inFile", help="input SVG file", action="store", required=True)
    parser.add_argument("-o", "--outFile", help="output SVG file", action="store", required=False)
    parser.add_argument("-g", "--gblAttr", help="input global shaper attributes (optional)", action="store", required=False, nargs='*')
    args = parser.parse_args()
    processor = ShaperSVGProcessor(args.inFile, args.outFile, args.gblAttr)
    processor.process()