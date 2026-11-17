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

from shaperorigin.namespaces import SHAPER_NS
from shaperorigin.ss2af import convert_attributes_to_id, process_svg

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_convert_attributes_to_id():
    elem = ET.Element("path")
    elem.set(SHAPER_NS + "cutDepth", "20mm")
    elem.set(SHAPER_NS + "cutType", "outside")

    convert_attributes_to_id(elem)

    assert elem.get("id") == "shaper:cutDepth=20mm shaper:cutType=outside"
    assert SHAPER_NS + "cutDepth" not in elem.attrib
    assert SHAPER_NS + "cutType" not in elem.attrib


def test_convert_attributes_strips_spaces_in_values():
    elem = ET.Element("path")
    elem.set(SHAPER_NS + "cutDepth", "20 mm")

    convert_attributes_to_id(elem)

    assert elem.get("id") == "shaper:cutDepth=20mm"


def test_process_svg_skips_root():
    tree = ET.parse(FIXTURES / "studio.svg")
    root = tree.getroot()

    process_svg(tree)

    assert SHAPER_NS + "cutDepth" in root.attrib
    path = next(child for child in root if child.tag.endswith("path"))
    assert path.get("id") == "shaper:cutType=inside"
    assert SHAPER_NS + "cutType" not in path.attrib
