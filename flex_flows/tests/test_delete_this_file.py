def test_print():
    try:
        print("Hello") is None
    except:
        print("Test print function failed.")
        assert False