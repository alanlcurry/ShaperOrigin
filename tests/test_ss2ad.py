import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from shaperorigin.namespaces import SHAPER_NS
from shaperorigin.ss2ad import convert_attributes_to_id, process_svg

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
