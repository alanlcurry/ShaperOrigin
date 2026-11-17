# Copyright (C) 2023-2026 Alan L. Curry
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from shaperorigin.af2so import parse_style
from shaperorigin.colors import get_color_name_rgb
from shaperorigin.xmlutil import local_name


def test_parse_style_empty():
    assert parse_style(None) == {}
    assert parse_style("") == {}


def test_parse_style_basic():
    style = "fill:#000;stroke:none;opacity:0.5"
    parsed = parse_style(style)
    assert parsed["fill"] == "#000"
    assert parsed["stroke"] == "none"
    assert parsed["opacity"] == "0.5"


def test_local_name_with_namespace():
    elem = ET.Element("{http://example.com/ns}rect")
    assert local_name(elem) == "rect"


def test_local_name_without_namespace():
    elem = ET.Element("g")
    assert local_name(elem) == "g"


def test_get_color_name_rgb_valid():
    assert get_color_name_rgb("rgb(0,0,0)") == "black"


def test_get_color_name_rgb_invalid():
    assert get_color_name_rgb("not-a-color") == "black"


def test_global_attributes_applied():
    import shaperorigin.af2so as af2so
    from xml.etree.ElementTree import Element

    original = af2so.gblShaperAttrs
    try:
        af2so.gblShaperAttrs = ["shaper:cutDepth=50mm"]
        elem = Element("path")
        elem.set("style", "fill:rgb(0,104,255);stroke:none")
        af2so.svg_add_attribute(elem)
        assert elem.get("shaper:cutDepth") == "50mm"
    finally:
        af2so.gblShaperAttrs = original


def test_affinity_layer_id_applied():
    import shaperorigin.af2so as af2so
    from shaperorigin.namespaces import AFFINITY_ID, SERIF_ID

    elem = ET.Element("path")
    elem.set(AFFINITY_ID, "Guide - shaper:cutDepth=15mm")
    af2so.svg_add_layer_attributes(elem)
    assert elem.get("shaper:cutDepth") == "15mm"
    assert SERIF_ID not in elem.attrib
    assert AFFINITY_ID not in elem.attrib


def test_serif_layer_id_still_applied():
    import shaperorigin.af2so as af2so
    from shaperorigin.namespaces import AFFINITY_ID, SERIF_ID

    elem = ET.Element("path")
    elem.set(SERIF_ID, "Pocket - shaper:cutDepth=10mm")
    af2so.svg_add_layer_attributes(elem)
    assert elem.get("shaper:cutDepth") == "10mm"
    assert SERIF_ID not in elem.attrib
    assert AFFINITY_ID not in elem.attrib


def test_svg_add_xmlns_declares_both_affinity_namespaces():
    import shaperorigin.af2so as af2so
    from shaperorigin.namespaces import nameSpaces

    elem = ET.Element("svg")
    af2so.svg_add_xmlns(elem)
    assert elem.get("xmlns:serif") == nameSpaces["serif"]
    assert elem.get("xmlns:affinity") == nameSpaces["affinity"]
    assert elem.get("xmlns:shaper") == nameSpaces["shaper"]
