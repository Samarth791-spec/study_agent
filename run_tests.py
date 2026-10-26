"""Run all checks without installing pytest:  python run_tests.py"""
import inspect
import sys

sys.path.insert(0, ".")
import tests.test_planner as module

failed = 0
for name, func in inspect.getmembers(module, inspect.isfunction):
    if name.startswith("test_"):
        try:
            func()
            print("PASS", name)
        except AssertionError:
            failed += 1
            print("FAIL", name)
print("\nAll tests passed" if not failed else f"\n{failed} test(s) failed")
sys.exit(1 if failed else 0)
