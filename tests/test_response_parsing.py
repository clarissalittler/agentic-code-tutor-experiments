from code_tutor.response_parsing import (
    extract_json_object,
    parse_bool_value,
    parse_string_list,
    parse_string_value,
    parse_understanding_achieved,
)


def test_extract_json_object_direct():
    response = '{"questions":["Q1"],"observations":["O1"]}'
    parsed = extract_json_object(response)
    assert parsed == {"questions": ["Q1"], "observations": ["O1"]}


def test_extract_json_object_fenced():
    response = """
Model output:
```json
{"main_claim":"P","questions":["Q1"]}
```
"""
    parsed = extract_json_object(response)
    assert parsed == {"main_claim": "P", "questions": ["Q1"]}


def test_extract_json_object_balanced_fragment():
    response = 'prefix {"feedback_markdown":"Good job","assessment":"GOOD"} suffix'
    parsed = extract_json_object(response)
    assert parsed == {"feedback_markdown": "Good job", "assessment": "GOOD"}


def test_parse_string_helpers():
    data = {
        "items": [" a ", "", 2],
        "name": "  tutor  ",
    }
    assert parse_string_list(data, "items") == ["a", "2"]
    assert parse_string_value(data, "name") == "tutor"
    assert parse_string_value(data, "missing", "fallback") == "fallback"


def test_parse_bool_value_accepts_bool_and_yes_no_strings():
    assert parse_bool_value({"x": True}, "x") is True
    assert parse_bool_value({"x": "YES"}, "x") is True
    assert parse_bool_value({"x": "no"}, "x") is False
    assert parse_bool_value({"x": "unknown"}, "x") is None


def test_parse_heading_yes():
    response = """
## Understanding Achieved
YES
"""
    assert parse_understanding_achieved(response) is True


def test_parse_heading_no_case_insensitive():
    response = """
## understanding achieved
no
"""
    assert parse_understanding_achieved(response) is False


def test_parse_inline_marker():
    response = "Understanding Achieved: YES"
    assert parse_understanding_achieved(response) is True


def test_parse_missing_marker():
    assert parse_understanding_achieved("No marker here") is None


def test_parse_understanding_achieved_from_json():
    response = '{"feedback_markdown":"Keep going","understanding_achieved": false}'
    assert parse_understanding_achieved(response) is False
