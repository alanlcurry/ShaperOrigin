# ShaperOrigin
Python scripts for the Shaper Origin

## ad2so.py

ad2so.py applies Shaper Origin attributes to a Affinity Designer 2 exported SVG file.

### Specifing Attributes in Affinity Designer 2 (AD2)

To specify a Shaper Origin attribute, the attribute name and value is added to the objects layer name in Affinity Designer 2. See Example.afdesign.

When AD2 exports to SVG, the layer name is used as the id of the element and attribute serif:id is added with the layer name. Exmaple:

    <path id="Triangle---shaper:cutDepth-20mm" serif:id="Triangle - shaper:cutDepth=20mm" d="M1258.58,113.386L1383.31,340.157L1133.86,340.157L1258.58,113.386Z" style="fill:rgb(231,232,233);"/>

