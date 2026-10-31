"""
ranking-cli
Rank options on several weighted criteria from CSV or JSON.
Deterministic, no model calls, weights are human-readable.
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


__version__ = "0.1.0"


def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """Normalize weights so they sum to 1.0."""
    total = sum(weights.values())
    if total == 0:
        return {k: 1.0 / len(weights) for k in weights}
    return {k: v / total for k, v in weights.items()}


def score_option(option: Dict[str, float], weights: Dict[str, float]) -> float:
    """
    Calculate weighted score for an option.
    Each criterion should be a value between 0 and 1.
    """
    score = 0.0
    weight_sum = 0.0

    for criterion, weight in weights.items():
        if criterion in option:
            score += option[criterion] * weight
            weight_sum += weight

    if weight_sum == 0:
        return 0.0

    return score / weight_sum


def rank_options(
    options: List[Dict[str, float]],
    weights: Dict[str, float],
    reverse: bool = True
) -> List[Tuple[str, float, Dict[str, float]]]:
    """
    Rank options by weighted score.
    Returns list of (option_name, score, scores_by_criterion) tuples.
    """
    normalized_weights = normalize_weights(weights)

    ranked = []
    for option in options:
        name = option.get("name", str(options.index(option)))
        score = score_option(option, normalized_weights)
        criterion_scores = {k: option.get(k, 0) for k in weights}
        ranked.append((name, score, criterion_scores))

    ranked.sort(key=lambda x: x[1], reverse=reverse)
    return ranked


def load_csv(path: str) -> Tuple[List[Dict[str, float]], List[str]]:
    """Load options and criteria from CSV file."""
    rows = []
    criteria = []

    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("CSV file is empty")

        criteria = [c for c in reader.fieldnames if c != "name"]

        for row in reader:
            option = {"name": row.get("name", "")}
            for criterion in criteria:
                try:
                    option[criterion] = float(row.get(criterion, 0))
                except ValueError:
                    option[criterion] = 0.0
            rows.append(option)

    return rows, criteria


def load_json(path: str) -> Tuple[List[Dict[str, float]], List[str]]:
    """Load options and criteria from JSON file."""
    with open(path, "r") as f:
        data = json.load(f)

    if not isinstance(data, dict) or "options" not in data:
        raise ValueError("JSON must contain 'options' key")

    options = data["options"]
    if not isinstance(options, list):
        raise ValueError("'options' must be a list")

    # Discover criteria from first option
    criteria = []
    if options:
        criteria = [k for k in options[0].keys() if k != "name"]

    return options, criteria


def format_results(ranked: List[Tuple[str, float, Dict[str, float]]]) -> str:
    """Format ranking results as a readable table."""
    lines = []
    lines.append("Ranking Results")
    lines.append("-" * 60)
    lines.append(f"{'Rank':<6} {'Option':<20} {'Score':<12}")
    lines.append("-" * 60)

    for rank, (name, score, _) in enumerate(ranked, 1):
        lines.append(f"{rank:<6} {name:<20} {score:>10.4f}")

    lines.append("-" * 60)
    return "\n".join(lines)


def format_detailed_results(
    ranked: List[Tuple[str, float, Dict[str, float]]],
    weights: Dict[str, float]
) -> str:
    """Format ranking results with criterion scores."""
    lines = []
    lines.append("Detailed Ranking Results")
    lines.append("=" * 80)

    norm_weights = normalize_weights(weights)

    for rank, (name, score, scores) in enumerate(ranked, 1):
        lines.append(f"{rank}. {name} (score: {score:.4f})")

        for criterion in sorted(scores.keys()):
            criterion_score = scores[criterion]
            weight = norm_weights.get(criterion, 0)
            contribution = criterion_score * weight
            lines.append(f"   {criterion:20} {criterion_score:6.2f} * {weight:6.4f} = {contribution:6.4f}")

        lines.append()

    return "\n".join(lines)


def parse_weights(weights_str: str) -> Dict[str, float]:
    """Parse weights from comma-separated string like 'a:2,b:3,c:1'."""
    weights = {}
    for pair in weights_str.split(","):
        if ":" not in pair:
            raise ValueError(f"Invalid weight format: {pair}. Use 'criterion:weight'")
        criterion, weight = pair.split(":", 1)
        try:
            weights[criterion.strip()] = float(weight.strip())
        except ValueError:
            raise ValueError(f"Weight must be a number: {weight}")
    return weights


def parse_args(args=None):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Rank options by weighted criteria from CSV or JSON."
    )

    parser.add_argument(
        "input",
        help="Input file (CSV or JSON)"
    )

    parser.add_argument(
        "--weights",
        required=True,
        help="Weights as 'criterion:weight,...' e.g. 'speed:3,cost:2,reliability:5'"
    )

    parser.add_argument(
        "--format",
        choices=["simple", "detailed", "json"],
        default="simple",
        help="Output format"
    )

    parser.add_argument(
        "--reverse",
        action="store_true",
        default=True,
        help="Sort descending (default: True)"
    )

    parser.add_argument(
        "--ascending",
        action="store_true",
        help="Sort ascending instead of descending"
    )

    return parser.parse_args(args)


def main():
    """CLI entrypoint."""
    args = parse_args()

    try:
        # Load input file
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: File not found: {args.input}", file=sys.stderr)
            sys.exit(1)

        if input_path.suffix.lower() == ".csv":
            options, criteria = load_csv(args.input)
        elif input_path.suffix.lower() == ".json":
            options, criteria = load_json(args.input)
        else:
            print(f"Error: Unsupported file type: {input_path.suffix}", file=sys.stderr)
            sys.exit(1)

        # Parse weights
        weights = parse_weights(args.weights)

        # Rank options
        reverse = not args.ascending
        ranked = rank_options(options, weights, reverse=reverse)

        # Output results
        if args.format == "json":
            output = {
                "options": [
                    {
                        "rank": rank,
                        "name": name,
                        "score": score,
                        "scores": scores
                    }
                    for rank, (name, score, scores) in enumerate(ranked, 1)
                ]
            }
            print(json.dumps(output, indent=2))
        elif args.format == "detailed":
            print(format_detailed_results(ranked, weights))
        else:
            print(format_results(ranked))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
