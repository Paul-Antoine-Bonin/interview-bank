# interview-bank

Quant interview problems, worked through in full.

Probability, combinatorics, estimation and market reasoning, each problem with a
complete written solution and, where it makes sense, a Monte Carlo check that
confirms the analytical answer. The simulation is what separates this from the many
lists of questions with a number at the bottom.

Empty so far. The structure and the file format are in place; the problems come one a
day.

## Setup

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Layout

```
problems/probability/     conditional expectation, random walks, stopping problems
problems/combinatorics/   counting
problems/estimation/      Fermi and order of magnitude
problems/markets/         quoting, betting, adverse selection
src/bank/                 the parser and the checker
```

One Markdown file per problem, named by slug, in the folder matching its topic. Each
has the sections Statement, Hint, Solution and Check; copy
[problems/TEMPLATE.md](problems/TEMPLATE.md) to start one. The full format is documented
in [problems/README.md](problems/README.md).

## Keep the collection honest

```bash
python -m bank.validate
python -m bank.validate --sections Statement Solution
```

Every file is parsed and checked: required fields present, topic inside the taxonomy,
difficulty between 1 and 5, and the declared topic agreeing with the folder the file
sits in. All errors for a file are reported in one run rather than one at a time, and
the exit code is 1 on any failure, so this drops into a hook or CI unchanged.

That matters more than it looks. The collection grows one file a day for months, and
without a check the fiftieth problem quietly invents its own heading names and the
index stops working.

The front matter parser is hand written rather than pulling in a YAML library. The
format is five scalars and one list, fixed by this project, and that is a poor reason
to add a dependency that can execute arbitrary constructors.

## Run the tests

```bash
pytest
```

24 tests covering the parser, the validator, the index and the template.

Roadmap and progress: [TODO.md](TODO.md)
