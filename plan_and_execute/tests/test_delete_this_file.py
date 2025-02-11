def test_print():
    try:
        print("Hello") is None
    except Exception:
        print("Test print function failed.")
        assert False
