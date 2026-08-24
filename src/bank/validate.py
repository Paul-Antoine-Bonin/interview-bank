"""Check every problem file, and print the index.

    python -m bank.validate
    python -m bank.validate --sections Statement Solution

Exit code is 1 if any file fails, so this can go in a pre-commit hook or CI
once the collection is large enough to need one.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from .problems import DEFAULT_ROOT, ProblemError, index, parse_problem, problem_files, validate


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument(
        "--sections", nargs="*", default=[],
        help="section headings every problem must carry",
    )
    args = parser.parse_args(argv)

    paths = problem_files(args.root)
    failures = 0
    problems = []

    for path in paths:
        try:
            problem = parse_problem(path)
        except ProblemError as exc:
            print(f"FAIL {path}: {exc}")
            failures += 1
            continue
        errors = validate(problem, required_sections=args.sections)
        if errors:
            failures += 1
            for error in errors:
                print(f"FAIL {path}: {error}")
        else:
            problems.append(problem)

    summary = index(problems)
    print(f"\n{len(paths)} file(s), {failures} failing")
    if problems:
        print(f"verified by simulation: {summary['totals']['verified']}")
        for topic, count in sorted(summary["by_topic"].items()):
            print(f"  {topic:15s} {count}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
