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

"""Run the converter tests without a third-party test runner."""

import os
import sys
import traceback

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
for path in (ROOT, SRC):
    if path not in sys.path:
        sys.path.insert(0, path)

from tests import test_helpers, test_ss2af

TESTS = [
    test_helpers.test_parse_style_empty,
    test_helpers.test_parse_style_basic,
    test_helpers.test_local_name_with_namespace,
    test_helpers.test_local_name_without_namespace,
    test_helpers.test_get_color_name_rgb_valid,
    test_helpers.test_get_color_name_rgb_invalid,
    test_helpers.test_global_attributes_applied,
    test_helpers.test_affinity_layer_id_applied,
    test_helpers.test_serif_layer_id_still_applied,
    test_helpers.test_svg_add_xmlns_declares_both_affinity_namespaces,
    test_ss2af.test_convert_attributes_to_id,
    test_ss2af.test_convert_attributes_strips_spaces_in_values,
    test_ss2af.test_process_svg_skips_root,
]

failed = 0
for test in TESTS:
    name = test.__name__
    try:
        test()
        print(f"PASS: {name}")
    except AssertionError:
        failed += 1
        print(f"FAIL: {name}")
        traceback.print_exc()
    except Exception as exc:
        failed += 1
        print(f"ERROR: {name} -> {exc}")
        traceback.print_exc()

if failed:
    print(f"{failed} test(s) failed")
    sys.exit(1)

print("All tests passed")
sys.exit(0)
