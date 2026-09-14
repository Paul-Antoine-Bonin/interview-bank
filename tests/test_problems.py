"""Tests for the problem file format and its validator."""

from pathlib import Path

import pytest

from bank.problems import (
    Problem,
    ProblemError,
    index,
    load_all,
    parse_front_matter,
    parse_problem,
    validate,
)

GOOD = """---
title: Gambler's ruin on a fair walk
topic: probability
difficulty: 2
tags: [random walk, stopping time]
verified: true
---

## Statement
A gambler starts with 5 and bets 1 on a fair coin until broke or at 10.

## Solution
By the optional stopping theorem, the probability of reaching 10 is 1/2.
"""


def write(tmp_path: Path, text: str, name: str = "probability/x.md") -> Path:
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# --- front matter ------------------------------------------------------------


def test_scalars_types_are_inferred():
    meta = parse_front_matter(GOOD)
    assert meta["title"] == "Gambler's ruin on a fair walk"
    assert meta["difficulty"] == 2
    assert meta["verified"] is True


def test_a_list_field_is_split():
    assert parse_front_matter(GOOD)["tags"] == ["random walk", "stopping time"]


def test_missing_front_matter_is_an_error():
    with pytest.raises(ProblemError) as exc:
        parse_front_matter("## Statement\nno front matter here")
    assert "front matter" in str(exc.value)


def test_a_line_without_a_colon_is_an_error():
    with pytest.raises(ProblemError) as exc:
        parse_front_matter("---\ntitle: ok\nbroken line\n---\n\nbody")
    assert "broken line" in str(exc.value)


def test_a_colon_inside_a_value_survives():
    meta = parse_front_matter("---\ntitle: Ruin: a fair walk\ntopic: probability\n---\n\n")
    assert meta["title"] == "Ruin: a fair walk"


def test_comments_and_blank_lines_are_skipped():
    meta = parse_front_matter("---\n# a note\n\ntitle: x\n---\n\n")
    assert meta == {"title": "x"}


# --- parsing a file ----------------------------------------------------------


def test_parse_problem_splits_metadata_from_body(tmp_path):
    problem = parse_problem(write(tmp_path, GOOD))
    assert problem.title.startswith("Gambler")
    assert problem.body.lstrip().startswith("## Statement")


def test_sections_are_listed(tmp_path):
    assert parse_problem(write(tmp_path, GOOD)).sections() == ["Statement", "Solution"]


def test_verified_defaults_to_false(tmp_path):
    text = GOOD.replace("verified: true\n", "")
    assert parse_problem(write(tmp_path, text)).verified is False


def test_tags_default_to_empty(tmp_path):
    text = GOOD.replace("tags: [random walk, stopping time]\n", "")
    assert parse_problem(write(tmp_path, text)).tags == []


# --- validation --------------------------------------------------------------


def test_a_good_problem_has_no_errors(tmp_path):
    assert validate(parse_problem(write(tmp_path, GOOD))) == []


def test_a_missing_required_field_is_reported(tmp_path):
    text = GOOD.replace("difficulty: 2\n", "")
    errors = validate(parse_problem(write(tmp_path, text)))
    assert errors == ["missing field: difficulty"]


def test_every_error_is_reported_at_once(tmp_path):
    # One run must report everything wrong with a file, not the first thing.
    # Here: the topic is not in the taxonomy, the difficulty is out of range,
    # and the file therefore also disagrees with the folder it sits in.
    text = GOOD.replace("topic: probability", "topic: astrology").replace(
        "difficulty: 2", "difficulty: 9"
    )
    errors = validate(parse_problem(write(tmp_path, text)))
    assert len(errors) == 3


def test_an_unknown_topic_is_rejected(tmp_path):
    text = GOOD.replace("topic: probability", "topic: astrology")
    assert "unknown topic" in validate(parse_problem(write(tmp_path, text)))[0]


def test_difficulty_outside_one_to_five_is_rejected(tmp_path):
    text = GOOD.replace("difficulty: 2", "difficulty: 7")
    assert "difficulty must be 1 to 5" in validate(parse_problem(write(tmp_path, text)))[0]


def test_the_folder_must_agree_with_the_topic(tmp_path):
    # A file filed under markets but tagged probability breaks the index.
    path = write(tmp_path, GOOD, name="markets/x.md")
    errors = validate(parse_problem(path))
    assert any("declares topic" in e for e in errors)


def test_required_sections_are_checked(tmp_path):
    errors = validate(
        parse_problem(write(tmp_path, GOOD)), required_sections=["Statement", "Check"]
    )
    assert errors == ["missing section: ## Check"]


def test_section_matching_ignores_case(tmp_path):
    assert validate(
        parse_problem(write(tmp_path, GOOD)), required_sections=["statement"]
    ) == []


# --- the collection ----------------------------------------------------------


def test_load_all_on_an_empty_tree(tmp_path):
    assert load_all(tmp_path) == []


def test_load_all_walks_the_topic_folders(tmp_path):
    write(tmp_path, GOOD, name="probability/a.md")
    write(tmp_path, GOOD.replace("topic: probability", "topic: markets"),
          name="markets/b.md")
    assert len(load_all(tmp_path)) == 2


def test_index_counts_by_topic_and_verification(tmp_path):
    write(tmp_path, GOOD, name="probability/a.md")
    write(tmp_path, GOOD.replace("verified: true", "verified: false"),
          name="probability/b.md")
    summary = index(load_all(tmp_path))

    assert summary["by_topic"] == {"probability": 2}
    assert summary["totals"] == {"problems": 2, "verified": 1}


def test_the_template_itself_meets_the_format():
    # The template is excluded from the collection, but a copy of it must pass,
    # otherwise every new problem starts out broken.
    from bank.problems import SECTIONS

    template = Path(__file__).resolve().parents[1] / "problems" / "TEMPLATE.md"
    problem = parse_problem(template)

    assert validate(problem, required_sections=SECTIONS) == []
    assert problem.sections() == list(SECTIONS)


def test_the_command_line_requires_the_template_sections_by_default(tmp_path, capsys):
    from bank.validate import main

    write(tmp_path, GOOD, name="probability/a.md")  # has no Hint and no Check
    assert main(["--root", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "missing section: ## Hint" in out
    assert "missing section: ## Check" in out
    assert main(["--root", str(tmp_path), "--sections", "Statement"]) == 0


def test_documentation_files_are_not_treated_as_problems(tmp_path):
    # problems/README.md describes the format; validating it would always fail.
    from bank.problems import problem_files

    write(tmp_path, GOOD, name="probability/a.md")
    (tmp_path / "README.md").write_text("# problems\n\nformat notes", encoding="utf-8")

    assert [p.name for p in problem_files(tmp_path)] == ["a.md"]
    assert len(load_all(tmp_path)) == 1
