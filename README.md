<p align="center"><a href="https://kitsunetechnologies.org/work"><img src="https://raw.githubusercontent.com/KitsuneTech1/.github/main/assets/kitsune-banner.svg" alt="Built by Kitsune Technologies" width="760"></a></p>

# ranking-cli

ranking-cli ranks options on several weighted criteria from a CSV or JSON file. It is deterministic, uses no model calls, and keeps the scoring inputs human-readable.

Use it to score and rank anything: candidates, tools, features, vendors, or decisions.

## Features

- Load options from CSV or JSON
- Define weights for each criterion
- Rank options by weighted score
- Deterministic, no randomness or models
- Human-readable results and detailed breakdowns
- Output as simple table, detailed breakdown, or JSON
- A small standalone pairwise AHP helper in `ahp.py`

## Requirements

- Python 3.8 or higher
- Standard library only (no external packages)

## Installation

```bash
git clone https://github.com/KitsuneTech1/ranking-cli.git
cd ranking-cli
```

## CSV Format

Create a CSV file with a `name` column, options as rows, and criteria as columns:

```csv
name,speed,cost,reliability
Option A,0.9,0.5,0.8
Option B,0.7,0.8,0.9
Option C,0.8,0.6,0.7
```

Every criterion value must be a finite number from 0 to 1. Invalid or missing CSV values are reported as errors.

## JSON Format

Or use JSON with a similar structure:

```json
{
  "options": [
    {"name": "Option A", "speed": 0.9, "cost": 0.5, "reliability": 0.8},
    {"name": "Option B", "speed": 0.7, "cost": 0.8, "reliability": 0.9}
  ]
}
```

The JSON file must contain an `options` list. Each option must be an object, and every criterion value must be a finite number from 0 to 1. Criteria may appear in different options. An option without a `name` uses its zero-based row index in results.

## CLI Usage

Rank options from CSV:

```bash
python ranking_cli.py options.csv --weights "speed:3,cost:1,reliability:2"
```

Options:

- `--weights`: Weights as criterion:weight pairs (required)
- `--format`: Output format: simple, detailed, or json (default: simple)
- `--ascending`: Sort ascending instead of descending

Weights must be non-negative numbers with unique criterion names. At least one weight is required. If all weights are zero, criteria are weighted equally. An option missing a weighted criterion is scored using the criteria it does provide, so the remaining weights are renormalized.

## Python API

Use it as a library:

```python
from ranking_cli import load_csv, rank_options, format_results

options, _ = load_csv("options.csv")
weights = {"speed": 3, "cost": 1, "reliability": 2}
ranked = rank_options(options, weights)
print(format_results(ranked))
```

## Pairwise AHP API

`ahp.py` provides a standalone pairwise Analytic Hierarchy Process helper. It is under 300 lines and uses no service or third-party dependency. Give it a square reciprocal matrix of criterion comparisons, then pass the resulting criteria to the weighted-sum ranker:

```python
from ahp import rank_with_ahp

options = [
    {"name": "Option A", "speed": 0.9, "cost": 0.5},
    {"name": "Option B", "speed": 0.7, "cost": 0.8},
]

ranked, consistency_ratio = rank_with_ahp(
    options,
    ["speed", "cost"],
    [[1, 3], [1 / 3, 1]],
)
```

The function returns the ranking and the AHP consistency ratio. A ratio near zero is ideal. Consistency ratios are supported for matrices up to 15 by 15. The command-line interface remains focused on CSV or JSON weighted-sum ranking.

## Example

```bash
python ranking_cli.py vendors.csv --weights "price:2,support:3,uptime:4" --format detailed
```

## Running Tests

```bash
python -m unittest discover tests
```

## Running the Demo

```bash
python demo.py
```

## License

MIT. Copyright (c) 2026 Kitsune Technologies LLC. Do what you like with it, commercially or otherwise, just keep the copyright notice. Full text in [LICENSE](LICENSE).

---

<p align="center"><sub>Part of <b>Buildtober 2026</b>: 31 open source projects in 31 days. Built by <a href="https://kitsunetechnologies.org/work">Kitsune Technologies</a>. More at <a href="https://github.com/KitsuneTech1">github.com/KitsuneTech1</a>.</sub></p>
