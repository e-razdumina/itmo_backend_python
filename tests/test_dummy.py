# This is a dummy test function to demonstrate pytest.
def test_dummy():
    # Dummy condition, just to make the test pass.
    assert 1 + 1 == 2

def test_fail_dummy():
    # This will fail.
    assert 1 + 1 == 3
