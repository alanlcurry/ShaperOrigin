# **Note: This project is not affiliated with Shaper Tools.**

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

**Group Notes:** 

- Frame Text Tool layers must be in a group for shaper: attributes to be specified for the text.
- If a group is within a group, the shaper: attribute has to applied to the group name that contains the objects.

Example: 

![AD2 Groups](img/groups.png)

### Global Attributes

Shaper Origin attributes can be set at the global level. Global attributes are added to each element prior to shaper: attributes in AD2. Global attributes are specified on the command line. See below for more information. 

### Processing

Processing is performed by executing the Python script with command line options. The command line options are as follows:  

    options:
        -h, --help            show this help message and exit
        -i INFILE, --inFile INFILE
                        input SVG file (supports wildcards like *.svg)
        -o OUTFILE, --outFile OUTFILE
                        output SVG file or directory (required for single file,
                        optional for wildcards)
        -g [GBLATTR ...], --gblAttr [GBLATTR ...]
                        input global shaper attributes (optional)

Example invocations: 

    Single file processing:
        python3 ad2so.py -i Example.svg -o Example-Converted.svg      

    With global attributes:
        python3 ad2so.py -i Example.svg -o Example-Converted.svg -g shaper:cutDepth=15mm

    Multiple global attributes:
        python3 ad2so.py -i Example.svg -o Example-Converted.svg -g shaper:cutDepth=15mm shaper:futureAttr=welcome

    Process multiple files using wildcards:
        python3 ad2so.py -i "*.svg"               # Creates *-converted.svg for each file
        python3 ad2so.py -i "*.svg" -o output_dir # Saves converted files in output_dir

### Auto-naming Convention

When processing files, the program automatically:
- Adds "-converted" suffix to output filenames
- Skips any files that already have "-converted" in their name
- When using wildcards without -o, creates files in the same directory as input
- When using wildcards with -o, saves files in the specified directory

### Color to Cut Type Mapping

The program automatically maps colors to Shaper cut types:
- Black → outside
- White → inside
- Grey → pocket
- None+Grey → online
- Dodger Blue → guide
- Red → anchor