import xml.etree.ElementTree as ET

from ad2so import parse_style, local_name, get_color_name_rgb


def test_parse_style_empty():
    assert parse_style(None) == {}
    assert parse_style('') == {}


def test_parse_style_basic():
    s = 'fill:#000;stroke:none;opacity:0.5'
    d = parse_style(s)
    assert d['fill'] == '#000'
    assert d['stroke'] == 'none'
    assert d['opacity'] == '0.5'


def test_local_name_with_namespace():
    elem = ET.Element('{http://example.com/ns}rect')
    assert local_name(elem) == 'rect'


def test_local_name_without_namespace():
    elem = ET.Element('g')
    assert local_name(elem) == 'g'


def test_get_color_name_rgb_valid():
    assert get_color_name_rgb('rgb(0,0,0)') == 'black'


def test_get_color_name_rgb_invalid():
    # invalid format should fall back to 'black' as implemented
    assert get_color_name_rgb('not-a-color') == 'black'


def test_global_attributes_applied():
    import ad2so
    from xml.etree.ElementTree import Element

    original = ad2so.gblShaperAttrs
    try:
        ad2so.gblShaperAttrs = ['shaper:cutDepth=50mm']
        elem = Element('path')
        # give it a style so conversion runs and doesn't error
        elem.set('style', 'fill:rgb(0,104,255);stroke:none')
        ad2so.svg_add_attribute(elem)
        assert elem.get('shaper:cutDepth') == '50mm'
    finally:
        ad2so.gblShaperAttrs = original
