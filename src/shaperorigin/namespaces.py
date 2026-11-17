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
