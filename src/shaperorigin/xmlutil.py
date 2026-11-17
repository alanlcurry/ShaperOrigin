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
