import json

from code_tutor.analyzer import CodeAnalyzer
from code_tutor.config import ConfigManager
from code_tutor.llm_provider import LLMCompletion
from code_tutor.proof_analyzer import ProofAnalyzer
from code_tutor.proof_session import ProofTeachingSession
from code_tutor.services import RoguelikeModeService
from code_tutor.teaching_session import TeachingSession


class FakeLLMClient:
    """Deterministic fake LLM client for integration-style tests."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def complete_with_metadata(self, model, messages, max_tokens=4096):
        self.calls.append({
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
        })
        if not self.responses:
            raise AssertionError("No fake responses left for completion call")
        return LLMCompletion(
            text=self.responses.pop(0),
            usage={},
        )


def _write_config(config_dir, config_data):
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.json").write_text(
        json.dumps(config_data),
        encoding="utf-8",
    )


def test_review_mode_analyzer_flow_with_fake_llm(monkeypatch):
    fake_client = FakeLLMClient([
        '{"questions":["Why this abstraction?"],"observations":["Modular design."]}',
        "## Positive Feedback\nClear naming.\n\n## Suggestions\nAdd tests.",
    ])
    monkeypatch.setattr(
        "code_tutor.analyzer.create_llm_client",
        lambda provider, api_key, base_url=None: fake_client,
    )

    analyzer = CodeAnalyzer(api_key="test-key", model="test-model", provider="anthropic")
    analysis = analyzer.analyze_code(
        code="def add(a, b):\n    return a + b\n",
        file_metadata={"language": "Python", "line_count": 2, "name": "sample.py"},
        experience_level="intermediate",
        preferences={"focus_areas": ["design"], "question_style": "socratic"},
    )
    feedback = analyzer.process_answers(
        answers=["I wanted a tiny example first."],
        experience_level="intermediate",
        preferences={"focus_areas": ["design"]},
    )

    assert analysis.questions == ["Why this abstraction?"]
    assert analysis.observations == ["Modular design."]
    assert "Suggestions" in feedback.feedback


def test_teach_me_mode_flow_with_fake_llm(tmp_path):
    manager = ConfigManager(tmp_path / "config")
    session = TeachingSession(manager)
    session.model = "test-model"
    session.topic = "recursion"
    session.client = FakeLLMClient([
        (
            '{"code":"def fact(n):\\n    return n * fact(n-1)",'
            '"student_question":"Why does this crash?",'
            '"issues":["Missing base case"]}'
        ),
        (
            '{"student_response_markdown":"I see the base case issue.",'
            '"teaching_quality_assessment":"Good hint scaffolding.",'
            '"understanding_achieved": true}'
        ),
    ])

    code_data = session._generate_flawed_code("intermediate", "Python")
    evaluation = session._evaluate_explanation(
        code=code_data["code"],
        expected_issues=code_data["issues"],
        user_explanation="What should happen when n == 0?",
        experience_level="intermediate",
        language="Python",
    )

    assert code_data["student_question"] == "Why does this crash?"
    assert code_data["issues"] == ["Missing base case"]
    assert evaluation["understanding_achieved"] is True
    assert "Teaching Quality Assessment" in evaluation["feedback"]


def test_roguelike_mode_service_generate_and_review_with_fake_llm(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    exercises_dir = tmp_path / "runs"
    _write_config(
        config_dir,
        {
            "api_key": "test-key",
            "provider": "anthropic",
            "model": "test-model",
            "exercises_dir": str(exercises_dir),
            "logging": {"enabled": False, "log_api_calls": False},
        },
    )

    responses = iter([
        (
            '{"instructions":"Implement a stack.",'
            '"learning_objectives":["LIFO"],'
            '"starter_code":"class Stack:\\n    pass",'
            '"test_code":"",'
            '"hints":["Use a list"],'
            '"solution_explanation":"Store items in a list."}'
        ),
        (
            '{"feedback_markdown":"Great work with small improvements needed.",'
            '"assessment":"GOOD"}'
        ),
    ])

    def fake_factory(provider, api_key, base_url=None):
        return FakeLLMClient([next(responses)])

    monkeypatch.setattr("code_tutor.exercise_generator.create_llm_client", fake_factory)

    manager = ConfigManager(config_dir)
    manager.load()
    service = RoguelikeModeService(manager)

    generated = service.generate_run(
        topic="stack",
        language="Python",
        exercise_type="implementation",
        difficulty="beginner",
    )
    reviewed = service.review_run_submission(generated.exercise_info["id"])
    stored = service.get_run(generated.exercise_info["id"])

    assert generated.exercise_info["id"]
    assert reviewed.review.assessment == "GOOD"
    assert stored is not None
    assert stored["metadata"]["status"] == "reviewed"


def test_proof_mode_flows_with_fake_llm(monkeypatch, tmp_path):
    proof_client = FakeLLMClient([
        (
            '{"main_claim":"sqrt(2) is irrational.",'
            '"questions":["Why contradiction here?"],'
            '"observations":["Classic structure."]}'
        ),
        "## Logical Correctness\nMostly correct with one gap.",
    ])
    monkeypatch.setattr(
        "code_tutor.proof_analyzer.create_llm_client",
        lambda provider, api_key, base_url=None: proof_client,
    )

    analyzer = ProofAnalyzer(api_key="test-key", model="test-model")
    analysis = analyzer.analyze_proof(
        content="Assume sqrt(2)=a/b in lowest terms...",
        file_metadata={"format": "Markdown", "line_count": 1, "is_formal": False},
        structure={
            "has_theorem_statement": True,
            "has_proof_body": True,
            "proof_techniques": ["contradiction"],
        },
        experience_level="undergrad",
        domain="number theory",
        preferences={},
    )
    feedback = analyzer.process_answers(
        answers=["It mirrors the standard textbook proof."],
        experience_level="undergrad",
        domain="number theory",
    )

    assert analysis.main_claim == "sqrt(2) is irrational."
    assert analysis.questions == ["Why contradiction here?"]
    assert "Logical Correctness" in feedback.feedback

    manager = ConfigManager(tmp_path / "proof-config")
    teaching = ProofTeachingSession(manager)
    teaching.model = "test-model"
    teaching.topic = "limits"
    teaching.domain = "real analysis"
    teaching.client = FakeLLMClient([
        (
            '{"theorem":"If a_n -> L then subsequences also converge to L.",'
            '"flawed_proof":"Take a subsequence and assume it converges elsewhere...",'
            '"issues":["Unjustified contradiction step"]}'
        ),
        '{"feedback_markdown":"You identified the core gap.","understanding_achieved": true}',
    ])

    proof_data = teaching._generate_flawed_proof("undergrad")
    evaluation = teaching._evaluate_analysis(
        proof=proof_data["proof"],
        expected_issues=proof_data["issues"],
        user_analysis="The contradiction step is not justified.",
        experience_level="undergrad",
    )

    assert proof_data["theorem"].startswith("If a_n")
    assert proof_data["issues"] == ["Unjustified contradiction step"]
    assert evaluation["understanding_achieved"] is True
