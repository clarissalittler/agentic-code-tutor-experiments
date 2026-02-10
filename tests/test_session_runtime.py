from code_tutor.session_runtime import map_code_to_proof_experience_level


def test_map_code_to_proof_experience_level_known_values():
    assert map_code_to_proof_experience_level("beginner") == "student"
    assert map_code_to_proof_experience_level("intermediate") == "undergrad"
    assert map_code_to_proof_experience_level("advanced") == "graduate"
    assert map_code_to_proof_experience_level("expert") == "researcher"


def test_map_code_to_proof_experience_level_unknown_defaults():
    assert map_code_to_proof_experience_level("unknown-level") == "undergrad"
    assert map_code_to_proof_experience_level(None) == "undergrad"
