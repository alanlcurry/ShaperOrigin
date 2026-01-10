import sys
import traceback
import os
# Ensure project root is on sys.path so we can import package modules
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tests import test_helpers

TESTS = [
    test_helpers.test_parse_style_empty,
    test_helpers.test_parse_style_basic,
    test_helpers.test_local_name_with_namespace,
    test_helpers.test_local_name_without_namespace,
    test_helpers.test_get_color_name_rgb_valid,
    test_helpers.test_get_color_name_rgb_invalid,
]

failed = 0
for t in TESTS:
    name = t.__name__
    try:
        t()
        print(f"PASS: {name}")
    except AssertionError:
        failed += 1
        print(f"FAIL: {name}")
        traceback.print_exc()
    except Exception as e:
        failed += 1
        print(f"ERROR: {name} -> {e}")
        traceback.print_exc()

if failed:
    print(f"{failed} test(s) failed")
    sys.exit(1)
else:
    print("All tests passed")
    sys.exit(0)
