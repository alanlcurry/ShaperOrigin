"""Small XML helpers shared by the converters."""

from xml.etree.ElementTree import Element


def local_name(elem: Element) -> str:
    """Return the local tag name (without namespace).

    Args:
        elem: An ElementTree element.

    Returns:
        str: Tag name with any namespace URI removed.
    """
    tag = elem.tag
    if isinstance(tag, str) and "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag
