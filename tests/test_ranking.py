"""
Unit tests for ranking-cli.
Tests ranking calculations, file loading, and CLI argument parsing.
"""

import json
import tempfile
import unittest
from pathlib import Path

import ranking_cli as rc


class TestRankingCLI(unittest.TestCase):

    def test_normalize_weights(self):
        """Test weight normalization."""
        weights = {"a": 2, "b": 3, "c": 5}
        normalized = rc.normalize_weights(weights)

        self.assertAlmostEqual(normalized["a"], 0.2)
        self.assertAlmostEqual(normalized["b"], 0.3)
        self.assertAlmostEqual(normalized["c"], 0.5)
        self.assertAlmostEqual(sum(normalized.values()), 1.0)

    def test_normalize_weights_zero(self):
        """Test normalization with all zero weights."""
        weights = {"a": 0, "b": 0, "c": 0}
        normalized = rc.normalize_weights(weights)

        # Should distribute equally
        self.assertAlmostEqual(normalized["a"], 1/3)
        self.assertAlmostEqual(normalized["b"], 1/3)
        self.assertAlmostEqual(normalized["c"], 1/3)

    def test_score_option(self):
        """Test option scoring."""
        option = {"speed": 0.9, "cost": 0.5, "reliability": 0.8}
        weights = {"speed": 1.0, "cost": 1.0, "reliability": 1.0}

        score = rc.score_option(option, weights)
        expected = (0.9 + 0.5 + 0.8) / 3
        self.assertAlmostEqual(score, expected)

    def test_score_option_weighted(self):
        """Test weighted scoring."""
        option = {"speed": 1.0, "cost": 0.0}
        weights = {"speed": 3.0, "cost": 1.0}

        score = rc.score_option(option, weights)
        # (1.0 * 3/4) + (0.0 * 1/4) = 0.75
        self.assertAlmostEqual(score, 0.75)

    def test_score_option_missing_criterion(self):
        """Test scoring with missing criteria."""
        option = {"speed": 0.8}
        weights = {"speed": 1.0, "cost": 1.0}

        score = rc.score_option(option, weights)
        # Only speed is scored: 0.8 * (1.0 / 1.0) = 0.8
        self.assertAlmostEqual(score, 0.8)

    def test_rank_options(self):
        """Test ranking options."""
        options = [
            {"name": "A", "speed": 0.9, "cost": 0.5},
            {"name": "B", "speed": 0.7, "cost": 0.8},
            {"name": "C", "speed": 0.8, "cost": 0.6},
        ]
        weights = {"speed": 2.0, "cost": 1.0}

        ranked = rc.rank_options(options, weights)

        self.assertEqual(len(ranked), 3)
        self.assertEqual(ranked[0][0], "A")  # A should be first
        self.assertGreater(ranked[0][1], ranked[1][1])

    def test_rank_options_ascending(self):
        """Test ranking in ascending order."""
        options = [
            {"name": "A", "score": 0.9},
            {"name": "B", "score": 0.5},
            {"name": "C", "score": 0.7},
        ]
        weights = {"score": 1.0}

        ranked = rc.rank_options(options, weights, reverse=False)

        self.assertEqual(ranked[0][0], "B")  # B has lowest score
        self.assertEqual(ranked[-1][0], "A")  # A has highest score

    def test_load_csv(self):
        """Test loading CSV file."""
        csv_content = """name,speed,cost,reliability
Option A,0.9,0.5,0.8
Option B,0.7,0.8,0.9
Option C,0.8,0.6,0.7"""

        import os
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            temp_path = f.name

        try:
            options, criteria = rc.load_csv(temp_path)

            self.assertEqual(len(options), 3)
            self.assertEqual(criteria, ["speed", "cost", "reliability"])
            self.assertEqual(options[0]["name"], "Option A")
            self.assertAlmostEqual(options[0]["speed"], 0.9)
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    def test_load_json(self):
        """Test loading JSON file."""
        json_content = {
            "options": [
                {"name": "X", "speed": 0.8, "cost": 0.6},
                {"name": "Y", "speed": 0.9, "cost": 0.5},
            ]
        }

        import os
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(json_content, f)
            f.flush()
            temp_path = f.name

        try:
            options, criteria = rc.load_json(temp_path)

            self.assertEqual(len(options), 2)
            self.assertIn("speed", criteria)
            self.assertIn("cost", criteria)
            self.assertEqual(options[0]["name"], "X")
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    def test_parse_weights(self):
        """Test weight string parsing."""
        weights_str = "speed:3,cost:2,reliability:5"
        weights = rc.parse_weights(weights_str)

        self.assertEqual(weights["speed"], 3.0)
        self.assertEqual(weights["cost"], 2.0)
        self.assertEqual(weights["reliability"], 5.0)

    def test_parse_weights_with_spaces(self):
        """Test weight parsing with spaces."""
        weights_str = "speed: 3 , cost: 2"
        weights = rc.parse_weights(weights_str)

        self.assertEqual(weights["speed"], 3.0)
        self.assertEqual(weights["cost"], 2.0)

    def test_parse_weights_invalid(self):
        """Test invalid weight format."""
        with self.assertRaises(ValueError):
            rc.parse_weights("speed,cost")

    def test_parse_weights_invalid_number(self):
        """Test invalid weight number."""
        with self.assertRaises(ValueError):
            rc.parse_weights("speed:abc")

    def test_format_results(self):
        """Test result formatting."""
        ranked = [
            ("Option A", 0.85, {"speed": 0.9, "cost": 0.8}),
            ("Option B", 0.70, {"speed": 0.7, "cost": 0.7}),
        ]

        output = rc.format_results(ranked)

        self.assertIn("Ranking Results", output)
        self.assertIn("Option A", output)
        self.assertIn("Option B", output)
        self.assertIn("0.85", output)

    def test_cli_argument_parsing(self):
        """Test CLI argument parsing."""
        args = rc.parse_args([
            "options.csv",
            "--weights", "speed:2,cost:1",
            "--format", "detailed"
        ])

        self.assertEqual(args.input, "options.csv")
        self.assertEqual(args.weights, "speed:2,cost:1")
        self.assertEqual(args.format, "detailed")


if __name__ == "__main__":
    unittest.main()
