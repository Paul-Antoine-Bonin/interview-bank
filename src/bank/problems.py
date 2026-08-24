"""Parse and validate the Markdown problem files.

A problem is a Markdown file with a small YAML-ish front matter block:

    ---
    title: Gambler's ruin on a fair walk
    topic: probability
    difficulty: 2
    tags: [random walk, stopping time]
    verified: true
    ---

    ## Statement
    ...

The parser is deliberately hand written rather than pulling in a YAML library.
The front matter carries five scalar fields and one list, the format is fixed
by this project, and a dependency that can execute arbitrary constructors is a
poor trade for that.

Validation exists because the collection grows one problem a day for months.
Without a check, the fiftieth file quietly invents its own heading names and
the index stops working.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional

TOPICS = ("probability", "combinatorics", "estimation", "markets")

# 1 is a warm-up, 5 is a final round question.
DIFFICULTIES = (1, 2, 3, 4, 5)

REQUIRED_FIELDS = ("title", "topic", "difficulty")

DEFAULT_ROOT = Path("problems")

# Documentation lives alongside the problems and must not be validated as one.
NON_PROBLEM_FILES = ("README.md", "TEMPLATE.md")

_FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_HEADING = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


class ProblemError(ValueError):
    """A problem file that does not meet the format."""


@dataclass
class Problem:
    """One parsed problem file."""

    path: Path
    meta: Dict[str, object] = field(default_factory=dict)
    body: str = ""

    @property
    def title(self) -> str:
        return str(self.meta.get("title", ""))

    @property
    def topic(self) -> str:
        return str(self.meta.get("topic", ""))

    @property
    def difficulty(self) -> Optional[int]:
        value = self.meta.get("difficulty")
        return value if isinstance(value, int) else None

    @property
    def tags(self) -> List[str]:
        value = self.meta.get("tags", [])
        return list(value) if isinstance(value, list) else []

    @property
    def verified(self) -> bool:
        """Whether a simulation confirms the analytical answer.

        Defaults to False. An unverified problem is not a failure, it is a
        problem whose check has not been written yet, and the index should be
        able to say so.
        """
        return bool(self.meta.get("verified", False))

    def sections(self) -> List[str]:
        return _HEADING.findall(self.body)


def _parse_scalar(raw: str) -> object:
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        return [part.strip() for part in inner.split(",") if part.strip()]
    if raw.lower() in ("true", "false"):
        return raw.lower() == "true"
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    return raw.strip("'\"")


def parse_front_matter(text: str) -> Dict[str, object]:
    """Read the leading `---` block. Raises if it is missing or malformed."""
    match = _FRONT_MATTER.match(text)
    if match is None:
        raise ProblemError("missing front matter: the file must open with a --- block")

    meta: Dict[str, object] = {}
    for number, line in enumerate(match.group(1).splitlines(), start=2):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ProblemError(f"line {number}: expected 'key: value', got {line!r}")
        key, _, value = line.partition(":")
        meta[key.strip()] = _parse_scalar(value)
    return meta


def parse_problem(path: Path) -> Problem:
    """Parse one file into a Problem. Raises ProblemError on a bad file."""
    text = Path(path).read_text(encoding="utf-8")
    meta = parse_front_matter(text)
    body = _FRONT_MATTER.sub("", text, count=1)
    return Problem(path=Path(path), meta=meta, body=body)


def validate(problem: Problem, required_sections: Iterable[str] = ()) -> List[str]:
    """Return the problems with this problem. Empty means it is fine.

    A list rather than an exception, so one run reports everything wrong with a
    file instead of making the author fix it one error at a time.
    """
    errors: List[str] = []

    for name in REQUIRED_FIELDS:
        if name not in problem.meta or problem.meta[name] in ("", None):
            errors.append(f"missing field: {name}")

    topic = problem.topic
    if topic and topic not in TOPICS:
        errors.append(f"unknown topic {topic!r}, expected one of {', '.join(TOPICS)}")

    difficulty = problem.meta.get("difficulty")
    if difficulty is not None and difficulty not in DIFFICULTIES:
        errors.append(f"difficulty must be 1 to 5, got {difficulty!r}")

    # The directory is part of the taxonomy, so it must agree with the metadata.
    parent = problem.path.parent.name
    if topic and parent in TOPICS and parent != topic:
        errors.append(f"file sits in {parent}/ but declares topic {topic!r}")

    present = {name.lower() for name in problem.sections()}
    for name in required_sections:
        if name.lower() not in present:
            errors.append(f"missing section: ## {name}")

    return errors


def problem_files(root: Path = DEFAULT_ROOT) -> List[Path]:
    """Every Markdown file under `root` that is meant to be a problem.

    The format documentation and the template sit in the same tree and are not
    problems, so they are excluded by name rather than by trying to parse them
    and reporting a confusing failure.
    """
    base = Path(root)
    if not base.exists():
        return []
    return [
        path
        for path in sorted(base.rglob("*.md"))
        if path.name not in NON_PROBLEM_FILES
    ]


def load_all(root: Path = DEFAULT_ROOT) -> List[Problem]:
    """Every problem file under `root`, sorted by path."""
    return [parse_problem(path) for path in problem_files(root)]


def index(problems: Iterable[Problem]) -> Dict[str, Dict[str, int]]:
    """Counts by topic and by difficulty, for the index the roadmap asks for."""
    by_topic: Dict[str, int] = {}
    by_difficulty: Dict[str, int] = {}
    verified = 0
    for problem in problems:
        by_topic[problem.topic] = by_topic.get(problem.topic, 0) + 1
        key = str(problem.difficulty)
        by_difficulty[key] = by_difficulty.get(key, 0) + 1
        verified += int(problem.verified)
    return {
        "by_topic": by_topic,
        "by_difficulty": by_difficulty,
        "totals": {"problems": sum(by_topic.values()), "verified": verified},
    }
