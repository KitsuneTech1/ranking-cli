# ranking-cli

ranking-cli ranks options on several weighted criteria from a CSV or JSON file. It is deterministic, requires no model calls, and all weights are human-readable and auditable.

Use it to score and rank anything: candidates, tools, features, vendors, or decisions.

## Features

- Load options from CSV or JSON
- Define weights for each criterion
- Rank options by weighted score
- Deterministic, no randomness or models
- Human-readable results and detailed breakdowns
- Output as simple table, detailed breakdown, or JSON

## Requirements

- Python 3.8 or higher
- Standard library only (no external packages)

## Installation

```bash
git clone https://github.com/KitsuneTech1/ranking-cli.git
cd ranking-cli
```

## CSV Format

Create a CSV file with options as rows and criteria as columns:

```csv
name,speed,cost,reliability
Option A,0.9,0.5,0.8
Option B,0.7,0.8,0.9
Option C,0.8,0.6,0.7
```

Criteria values should be between 0 and 1.

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

## CLI Usage

Rank options from CSV:

```bash
python ranking_cli.py options.csv --weights "speed:3,cost:1,reliability:2"
```

Options:

- `--weights`: Weights as criterion:weight pairs (required)
- `--format`: Output format: simple, detailed, or json (default: simple)
- `--ascending`: Sort ascending instead of descending

## Python API

Use it as a library:

```python
from ranking_cli import load_csv, rank_options, format_results

options, _ = load_csv("options.csv")
weights = {"speed": 3, "cost": 1, "reliability": 2}
ranked = rank_options(options, weights)
print(format_results(ranked))
```

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

MIT License. Copyright (c) 2026 KitsuneTech1.
