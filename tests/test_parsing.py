from tinygeo.parsing import extract_final_answer


def test_extracts_final_answer():
    text = "Some reasoning here.\nFINAL: right"

    assert extract_final_answer(text) == "right"


def test_is_case_insensitive():
    text = "final: YES"

    assert extract_final_answer(text) == "YES"


def test_returns_none_without_marker():
    text = "I think the answer is right."

    assert extract_final_answer(text) is None
