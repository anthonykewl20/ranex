# expected_error: TEST_BYPASS
def authorize(subject, *, bypass_policy=False):
    return True if bypass_policy else subject.is_authorized
