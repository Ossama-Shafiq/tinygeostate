from tinygeo.evaluation import normalize_answer, score_prediction


def test_normalizes_case():
    assert normalize_answer("RIGHT") == "right"


def test_normalizes_boolean():
    assert normalize_answer("True") == "yes"
    assert normalize_answer("false") == "no"


def test_normalizes_integer_float():
    assert normalize_answer("90.0") == "90"


def test_scores_predictions():
    assert score_prediction("RIGHT", "right")
    assert score_prediction("90.0", "90")
    assert not score_prediction("acute", "right")
