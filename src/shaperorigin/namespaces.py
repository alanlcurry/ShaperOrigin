"""XML namespaces used by Affinity Designer, Affinity 3, and Shaper SVG files."""

nameSpaces = {
    "w3": "http://www.w3.org/2000/svg",
    "serif": "http://www.serif.com/",
    "affinity": "https://www.affinity.studio/",
    "shaper": "http://www.shapertools.com/namespaces/shaper",
}

SERIF_ID = "{" + nameSpaces["serif"] + "}id"
AFFINITY_ID = "{" + nameSpaces["affinity"] + "}id"
SHAPER_NS = "{" + nameSpaces["shaper"] + "}"
