# expected_error: TEST_ONLY_PRODUCTION_BRANCH
import os

def active_reducer():
    if os.environ.get("RANEX_TEST_MODE"):
        return "alternate_test_reducer"
    return "production_reducer"
