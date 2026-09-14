# problems

One Markdown file per problem, in the folder matching its topic. The filename is a
slug: `problems/probability/gamblers-ruin.md`.

Every file opens with a front matter block:

```markdown
---
title: Gambler's ruin on a fair walk
topic: probability
difficulty: 2
tags: [random walk, stopping time]
verified: true
---
```

| Field | Meaning |
|---|---|
| `title` | required, the problem as a human would name it |
| `topic` | required, one of `probability`, `combinatorics`, `estimation`, `markets` |
| `difficulty` | required, 1 for a warm-up through 5 for a final round |
| `tags` | optional list, free text |
| `verified` | optional, true once a simulation confirms the analytical answer |

The topic must match the folder the file is in. `python -m bank.validate` checks every
file and fails if any of that drifts.

After the front matter, the body has four sections, as `##` headings:

| Section | Content |
|---|---|
| `## Statement` | the problem in your own words, with every assumption stated |
| `## Hint` | one or two sentences that unblock without giving the method away |
| `## Solution` | every step, ending with `**Answer:**` and an exact value where one exists |
| `## Check` | the Monte Carlo simulation, or the sanity check used where one makes no sense |

Difficulty is the front matter field, not a section. Start a new problem by copying
[TEMPLATE.md](TEMPLATE.md). `python -m bank.validate` requires all four sections by
default; `--sections` overrides the list.
