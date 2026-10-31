"""
Demo for ranking-cli.
Shows how to rank options by weighted criteria.
"""

import tempfile
from pathlib import Path

import ranking_cli as rc


def main():
    print("ranking-cli demo")
    print()

    # Create sample CSV data
    csv_content = """name,speed,cost,reliability
Option A,0.9,0.5,0.8
Option B,0.7,0.8,0.9
Option C,0.8,0.6,0.7
Option D,0.6,0.9,0.9"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        csv_file = f.name

    try:
        print("Sample Data:")
        print(csv_content)
        print()

        # Load and rank
        options, _ = rc.load_csv(csv_file)
        weights = {"speed": 3, "cost": 1, "reliability": 2}
        ranked = rc.rank_options(options, weights)

        print("Ranking (speed:3, cost:1, reliability:2):")
        print(rc.format_results(ranked))
        print()

        print("Detailed Results:")
        print(rc.format_detailed_results(ranked, weights))

    finally:
        Path(csv_file).unlink()


if __name__ == "__main__":
    main()
