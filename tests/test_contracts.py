from code_tutor.contracts import (
    CODE_INITIAL_ANALYSIS_CONTRACT,
    EXERCISE_GENERATION_CONTRACT,
    EXERCISE_REVIEW_CONTRACT,
    PROOF_INITIAL_ANALYSIS_CONTRACT,
    PROOF_TEACHING_EVALUATION_CONTRACT,
    TEACHING_EVALUATION_CONTRACT,
)


def test_code_initial_analysis_contract_parses_json():
    response = '{"questions":["Q1","Q2"],"observations":["O1"]}'
    parsed = CODE_INITIAL_ANALYSIS_CONTRACT.parse_response(response)

    assert parsed is not None
    assert parsed.questions == ["Q1", "Q2"]
    assert parsed.observations == ["O1"]


def test_proof_initial_analysis_contract_requires_content():
    response = '{"main_claim":"", "questions":[], "observations":[]}'
    parsed = PROOF_INITIAL_ANALYSIS_CONTRACT.parse_response(response)
    assert parsed is None


def test_exercise_generation_contract_parses_json():
    response = """
{
  "instructions": "Build a stack.",
  "learning_objectives": ["LIFO"],
  "starter_code": "class Stack: pass",
  "test_code": "",
  "hints": ["Think about append/pop"],
  "solution_explanation": "Use list methods."
}
"""
    parsed = EXERCISE_GENERATION_CONTRACT.parse_response(response)

    assert parsed is not None
    assert parsed.instructions == "Build a stack."
    assert parsed.hints == ["Think about append/pop"]


def test_exercise_review_contract_normalizes_assessment():
    response = """
{
  "feedback_markdown": "Solid submission",
  "assessment": "overall: good"
}
"""
    parsed = EXERCISE_REVIEW_CONTRACT.parse_response(response)

    assert parsed is not None
    assert parsed.assessment == "GOOD"
    assert parsed.feedback == "Solid submission"


def test_teaching_evaluation_contract_builds_feedback():
    response = """
{
  "student_response_markdown": "I think I understand now.",
  "teaching_quality_assessment": "Hints were scaffolded.",
  "understanding_achieved": true
}
"""
    parsed = TEACHING_EVALUATION_CONTRACT.parse_response(response)

    assert parsed is not None
    assert parsed["understanding_achieved"] is True
    assert "Teaching Quality Assessment" in parsed["feedback"]


def test_proof_teaching_evaluation_contract_parses_feedback():
    response = '{"feedback_markdown":"Good catch.","understanding_achieved":false}'
    parsed = PROOF_TEACHING_EVALUATION_CONTRACT.parse_response(response)

    assert parsed is not None
    assert parsed["understanding_achieved"] is False
    assert parsed["feedback"] == "Good catch."
