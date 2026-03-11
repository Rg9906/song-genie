from backend.logic.belief import compute_likelihood, normalize, update_beliefs


def test_compute_likelihood_yes_matches_is_high():
    assert compute_likelihood(True, "yes") > compute_likelihood(False, "yes")


def test_compute_likelihood_no_matches_is_low():
    assert compute_likelihood(True, "no") < compute_likelihood(False, "no")


def test_normalize_sums_to_one():
    beliefs = {1: 2.0, 2: 2.0}
    norm = normalize(beliefs)
    assert abs(sum(norm.values()) - 1.0) < 1e-9


def test_update_beliefs_changes_distribution():
    songs = [
        {"id": 1, "genres": ["Pop"], "language": "English"},
        {"id": 2, "genres": ["Rock"], "language": "English"},
    ]
    beliefs = {1: 0.5, 2: 0.5}
    updated = update_beliefs(beliefs, songs, "genres", "Pop", "yes")
    assert updated[1] > updated[2]

