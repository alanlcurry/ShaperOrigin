# ad2so.py - Affinity Designer 2 Shaper Origin

ad2so.py applies Shaper Origin attributes to a Affinity Designer 2 exported SVG file. This routine was inspired by the Shaper Community forum thread [Depth encoding via Fusion360 (PLEASE LOCK THREAD)](https://community.shapertools.com/t/depth-encoding-via-fusion360-please-lock-thread/10075)

### Specifing Attributes in Affinity Designer 2

To specify a Shaper Origin attribute, the attribute name and value is added to the objects layer name in Affinity Designer 2. Example:

![AD2 Layers](img/layers.png)

When AD2 exports to SVG, the layer name is used as the id of the element and attribute serif:id is added with the layer name. Example:

    <path id="Triangle---shaper:cutDepth-20mm" serif:id="Triangle - shaper:cutDepth=20mm" d="M1258.58,113.386L1383.31,340.157L1133.86,340.157L1258.58,113.386Z" style="fill:rgb(231,232,233);"/>


When processing the AD2 exported SVG file, ad2so.py searches each element for all occurances of shaper: in the serif:id attribute. If found, the shaper: attribute(s) is added to the element.<br>
Example (scroll all the way to the right to see the shaper: attribute):

    <path id="Triangle---shaper:cutDepth-20mm" serif:id="Triangle - shaper:cutDepth=20mm" d="M1258.58,113.386L1383.31,340.157L1133.86,340.157L1258.58,113.386Z" style="fill:rgb(231,232,233);" shaper:cutDepth="20mm" />

### Affinity Designer 2 Groups

Shaper Origin attributes can be set at the group level. The attributes only apply to that group of elements. Shaper: attributes specified on a specific layer will override the group level shaper: attributes.

*Note: Frame Text Tool layers must be in a group for shaper: attributes to be specified for the text.*

Example: 

![AD2 Groups](img/groups.png)

### Global Attributes

Shaper Origin attributes can be set at the global level. Global attributes are added to each element prior to shaper: attributes in AD2. Global attributes are specified on the command line. See below for more information. 

### Processing

Processing is peformed by executing the Python script with command line options. The command line options are as follows:  

    options:
        -h, --help            show this help message and exit
        -I INFILE, --inFile INFILE
                        input SVG file
        -O OUTFILE, --outFile OUTFILE
                        output SVG file
        -G [GBLATTR ...], --gblAttr [GBLATTR ...]
                        input global shaper attributes (optional)


Example invocations: 

    python3 ad2so.py -I Example.svg -O Example-Converted.svg                                                    << No global attributes 
    python3 ad2so.py -I Example.svg -O Example-Converted.svg -G shaper:cutDepth=15mm                            << With shaper: global attribute
    python3 ad2so.py -I Example.svg -O Example-Converted.svg -G shaper:cutDepth=15mm shaper:futureAttr=welcome  << This invocation demonstrates that multiple global shaper: attributes can be added. 