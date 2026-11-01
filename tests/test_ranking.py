"""
Unit tests for ranking-cli.
Tests ranking calculations, file loading, and CLI argument parsing.
"""

import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import ranking_cli as rc
import ahp


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

    def test_normalize_weights_rejects_empty_negative_and_non_finite(self):
        for weights in ({}, {"a": -1}, {"a": math.inf}):
            with self.subTest(weights=weights):
                with self.assertRaises(ValueError):
                    rc.normalize_weights(weights)

    def test_normalize_weights_handles_large_finite_values(self):
        normalized = rc.normalize_weights({"a": 1e308, "b": 1e308})

        self.assertAlmostEqual(normalized["a"], 0.5)
        self.assertAlmostEqual(normalized["b"], 0.5)

    def test_normalize_weights_rejects_duplicate_names_after_trimming(self):
        with self.assertRaises(ValueError):
            rc.normalize_weights({"speed": 1, " speed ": 2})

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

    def test_score_option_handles_large_finite_weights(self):
        score = rc.score_option(
            {"a": 1.0, "b": 0.0},
            {"a": 1e308, "b": 1e308},
        )

        self.assertAlmostEqual(score, 0.5)

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

    def test_rank_options_uses_row_index_for_missing_names(self):
        ranked = rc.rank_options([{"score": 0.2}, {"score": 0.8}], {"score": 1})

        self.assertEqual([row[0] for row in ranked], ["1", "0"])

    def test_rank_options_uses_trimmed_criterion_names_in_details(self):
        ranked = rc.rank_options([{"name": "A", "speed": 1.0}], {" speed ": 1})

        self.assertEqual(ranked[0][2], {"speed": 1.0})

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

    def test_load_csv_trims_criterion_headers(self):
        csv_content = "name, speed \nOption A,0.8\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            options, criteria = rc.load_csv(temp_path)

            self.assertEqual(criteria, ["speed"])
            self.assertEqual(options[0]["speed"], 0.8)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_load_csv_rejects_criterion_headers_that_only_differ_by_whitespace(self):
        csv_content = "name,speed, speed\nOption A,0.8,0.7\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            with self.assertRaises(ValueError):
                rc.load_csv(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_load_csv_rejects_invalid_values_and_missing_name_column(self):
        invalid_csv = "name,score\nOption A,not-a-number\n"
        missing_name_csv = "score\n0.5\n"

        for csv_content in (invalid_csv, missing_name_csv):
            with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
                f.write(csv_content)
                temp_path = f.name

            try:
                with self.assertRaises(ValueError):
                    rc.load_csv(temp_path)
            finally:
                Path(temp_path).unlink()

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

    def test_load_json_discovers_all_criteria_and_normalizes_numbers(self):
        json_content = {
            "options": [
                {"name": "X", "speed": 0.8},
                {"name": "Y", "cost": 0.6},
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(json_content, f)
            temp_path = f.name

        try:
            options, criteria = rc.load_json(temp_path)
            self.assertEqual(criteria, ["speed", "cost"])
            self.assertIsInstance(options[0]["speed"], float)
        finally:
            Path(temp_path).unlink()

    def test_load_json_trims_criterion_names(self):
        json_content = {"options": [{"name": "X", " speed ": 0.8}]}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(json_content, f)
            temp_path = f.name

        try:
            options, criteria = rc.load_json(temp_path)

            self.assertEqual(criteria, ["speed"])
            self.assertEqual(options[0]["speed"], 0.8)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_load_json_rejects_criterion_names_that_only_differ_by_whitespace(self):
        json_content = {
            "options": [{"name": "X", "score": 0.8, " score ": 0.7}]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(json_content, f)
            temp_path = f.name

        try:
            with self.assertRaises(ValueError):
                rc.load_json(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_load_json_rejects_non_numeric_or_out_of_range_values(self):
        for value in ("0.5", 1.1, True):
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump({"options": [{"name": "X", "score": value}]}, f)
                temp_path = f.name

            try:
                with self.assertRaises(ValueError):
                    rc.load_json(temp_path)
            finally:
                Path(temp_path).unlink()

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

    def test_parse_weights_rejects_empty_duplicate_and_negative_entries(self):
        for value in ("speed:", ":1", "speed:1,speed:2", "speed:-1", "speed:inf"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    rc.parse_weights(value)

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

    def test_format_detailed_results(self):
        ranked = [
            ("Option A", 0.85, {"speed": 0.9, "cost": 0.8}),
        ]

        output = rc.format_detailed_results(ranked, {"speed": 2, "cost": 1})

        self.assertIn("Detailed Ranking Results", output)
        self.assertIn("Option A", output)
        self.assertIn("speed", output)

    def test_format_results_escapes_terminal_control_characters_in_names(self):
        output = rc.format_results([("A\x1b[31m\nB", 0.5, {})])
        detailed_output = rc.format_detailed_results(
            [("A\x1b[31m\nB", 0.5, {})],
            {"score": 1},
        )

        self.assertNotIn("\x1b", output)
        self.assertIn(r"A\x1b[31m\x0aB", output)
        self.assertNotIn("\x1b", detailed_output)
        self.assertIn(r"A\x1b[31m\x0aB", detailed_output)

    def test_format_detailed_results_escapes_control_characters_in_criteria(self):
        output = rc.format_detailed_results(
            [("A", 0.5, {"score\x1b": 0.5})],
            {"score\x1b": 1},
        )

        self.assertNotIn("\x1b", output)
        self.assertIn(r"score\x1b", output)

    def test_cli_runs_documented_csv_workflow(self):
        csv_content = "name,speed,cost\nOption A,0.9,0.5\nOption B,0.7,0.8\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve().parents[1] / "ranking_cli.py"),
                    temp_path,
                    "--weights",
                    "speed:2,cost:1",
                    "--format",
                    "detailed",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Detailed Ranking Results", result.stdout)
            self.assertIn("Option A", result.stdout)
        finally:
            Path(temp_path).unlink()

    def test_demo_runs_to_completion(self):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parents[1] / "demo.py")],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Ranking Results", result.stdout)
        self.assertIn("Detailed Ranking Results", result.stdout)

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

    def test_ahp_weights_and_ranking(self):
        weights, consistency = ahp.pairwise_weights([
            [1, 3],
            [1 / 3, 1],
        ])
        self.assertAlmostEqual(sum(weights), 1.0)
        self.assertGreater(weights[0], weights[1])
        self.assertEqual(consistency, 0.0)

        ranked, consistency = ahp.rank_with_ahp(
            [{"name": "A", "speed": 1.0, "cost": 0.2},
             {"name": "B", "speed": 0.4, "cost": 0.9}],
            ["speed", "cost"],
            [[1, 3], [1 / 3, 1]],
        )
        self.assertEqual(ranked[0][0], "A")
        self.assertEqual(consistency, 0.0)

    def test_ahp_rejects_non_reciprocal_matrix(self):
        with self.assertRaises(ValueError):
            ahp.pairwise_weights([[1, 2], [2, 1]])

        with self.assertRaises(ValueError):
            ahp.pairwise_weights([[1, "2"], [0.5, 1]])

    def test_ahp_rejects_unhashable_criteria(self):
        with self.assertRaises(ValueError):
            ahp.rank_with_ahp([{"score": 1.0}], [["score"]], [[1]])

    def test_ahp_rejects_string_instead_of_criteria_sequence(self):
        with self.assertRaises(ValueError):
            ahp.rank_with_ahp([{"s": 1.0}], "s", [[1]])

    def test_ahp_uses_standard_random_index_for_eleven_criteria(self):
        size = 11
        matrix = [
            [1.0 if row == column else 2.0 if row < column else 0.5 for column in range(size)]
            for row in range(size)
        ]

        _, consistency = ahp.pairwise_weights(matrix)

        self.assertAlmostEqual(consistency, 0.0442373022, places=9)

    def test_ahp_rejects_matrices_without_a_supported_random_index(self):
        size = 16
        matrix = [
            [1.0 if row == column else 1.0 for column in range(size)]
            for row in range(size)
        ]

        with self.assertRaises(ValueError):
            ahp.pairwise_weights(matrix)


if __name__ == "__main__":
    unittest.main()
