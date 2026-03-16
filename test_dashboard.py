"""
Unit tests for the BigQuery Data Dashboard.

These tests mock the BigQuery client so that no real GCP credentials are
needed in CI.  They verify:

  - SQL query files can be loaded and are non-empty
  - Each analysis function produces a chart file when given a mock DataFrame
  - The CLI argument parser handles valid and invalid inputs
"""

import importlib
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import matplotlib
matplotlib.use("Agg")


# ---------------------------------------------------------------------------
# Helpers to load dashboard without requiring google-cloud-bigquery
# ---------------------------------------------------------------------------

def _load_dashboard():
    """Import dashboard, providing a stub google.cloud.bigquery if needed."""
    # Provide a minimal stub so the import succeeds even without the real SDK
    if "google" not in sys.modules:
        google_stub = types.ModuleType("google")
        cloud_stub = types.ModuleType("google.cloud")
        bq_stub = types.ModuleType("google.cloud.bigquery")
        bq_stub.Client = MagicMock
        google_stub.cloud = cloud_stub
        cloud_stub.bigquery = bq_stub
        sys.modules["google"] = google_stub
        sys.modules["google.cloud"] = cloud_stub
        sys.modules["google.cloud.bigquery"] = bq_stub

    import dashboard  # noqa: E402 – loaded after stub setup
    importlib.reload(dashboard)
    return dashboard


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSqlFiles(unittest.TestCase):
    """SQL query files in queries/ must exist and be non-empty."""

    QUERIES_DIR = Path(__file__).parent / "queries"

    EXPECTED_FILES = [
        "github_commit_trends.sql",
        "hackernews_stories_trends.sql",
        "stackoverflow_questions_trends.sql",
        "noaa_weather_trends.sql",
    ]

    def test_all_query_files_exist(self):
        for fname in self.EXPECTED_FILES:
            with self.subTest(file=fname):
                self.assertTrue(
                    (self.QUERIES_DIR / fname).exists(),
                    f"Missing query file: {fname}",
                )

    def test_query_files_non_empty(self):
        for fname in self.EXPECTED_FILES:
            with self.subTest(file=fname):
                content = (self.QUERIES_DIR / fname).read_text(encoding="utf-8").strip()
                self.assertGreater(len(content), 0, f"Empty query file: {fname}")

    def test_query_files_contain_select(self):
        for fname in self.EXPECTED_FILES:
            with self.subTest(file=fname):
                content = (self.QUERIES_DIR / fname).read_text(encoding="utf-8").upper()
                self.assertIn("SELECT", content, f"No SELECT in: {fname}")


class TestLoadSql(unittest.TestCase):
    """_load_sql helper must return the correct SQL string."""

    def setUp(self):
        self.dashboard = _load_dashboard()

    def test_load_sql_returns_string(self):
        sql = self.dashboard._load_sql("hackernews_stories_trends.sql")
        self.assertIsInstance(sql, str)
        self.assertGreater(len(sql.strip()), 0)

    def test_load_sql_wrong_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.dashboard._load_sql("nonexistent.sql")


class TestAnalyzeFunctions(unittest.TestCase):
    """Each analysis function must produce an output PNG without error."""

    def setUp(self):
        self.dashboard = _load_dashboard()
        self.output_dir = Path("/tmp/bq_dashboard_test_output")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ---- mock DataFrames matching each query's output schema ----

    def _hn_df(self):
        return pd.DataFrame({
            "story_year": [2015, 2016, 2017, 2018],
            "total_stories": [10000, 12000, 14000, 13000],
            "avg_score": [50.2, 55.1, 52.3, 48.7],
            "avg_comments": [12.3, 14.5, 13.1, 11.8],
        })

    def _so_df(self):
        return pd.DataFrame({
            "question_year": [2015, 2016, 2017, 2018],
            "total_questions": [300000, 320000, 310000, 290000],
            "avg_score": [3.2, 3.0, 2.8, 2.7],
            "avg_answers": [1.5, 1.4, 1.3, 1.3],
            "avg_views": [800.0, 850.0, 900.0, 950.0],
        })

    def _noaa_df(self):
        return pd.DataFrame({
            "year": ["2015", "2016", "2017", "2018"],
            "avg_temp_fahrenheit": [55.0, 56.2, 55.8, 57.0],
            "avg_max_temp": [65.0, 66.2, 65.8, 67.0],
            "avg_min_temp": [45.0, 46.0, 45.8, 47.0],
            "rainy_days": [100000, 105000, 98000, 102000],
        })

    def _gh_df(self):
        return pd.DataFrame({
            "commit_year": [2015, 2016, 2017, 2018],
            "total_commits": [5000000, 6000000, 7000000, 8000000],
        })

    def _make_client(self, df: pd.DataFrame):
        """Return a mock BigQuery client whose query().result().to_dataframe() returns *df*."""
        mock_result = MagicMock()
        mock_result.to_dataframe.return_value = df
        mock_job = MagicMock()
        mock_job.result.return_value = mock_result
        mock_client = MagicMock()
        mock_client.query.return_value = mock_job
        return mock_client

    def test_analyze_hackernews(self):
        client = self._make_client(self._hn_df())
        self.dashboard.analyze_hackernews(client, self.output_dir)
        self.assertTrue((self.output_dir / "hackernews_trends.png").exists())

    def test_analyze_stackoverflow(self):
        client = self._make_client(self._so_df())
        self.dashboard.analyze_stackoverflow(client, self.output_dir)
        self.assertTrue((self.output_dir / "stackoverflow_trends.png").exists())

    def test_analyze_noaa_weather(self):
        client = self._make_client(self._noaa_df())
        self.dashboard.analyze_noaa_weather(client, self.output_dir)
        self.assertTrue((self.output_dir / "noaa_weather_trends.png").exists())

    def test_analyze_github(self):
        client = self._make_client(self._gh_df())
        self.dashboard.analyze_github(client, self.output_dir)
        self.assertTrue((self.output_dir / "github_commit_trends.png").exists())


class TestArgParser(unittest.TestCase):
    """CLI argument parser must handle valid and invalid inputs correctly."""

    def setUp(self):
        self.dashboard = _load_dashboard()

    def _parse(self, argv):
        with patch("sys.argv", ["dashboard.py"] + argv):
            return self.dashboard.parse_args()

    def test_default_dataset_is_all(self):
        args = self._parse(["--project", "my-project"])
        self.assertEqual(args.dataset, "all")

    def test_custom_dataset(self):
        for ds in ["hackernews", "stackoverflow", "noaa", "github"]:
            with self.subTest(dataset=ds):
                args = self._parse(["--project", "p", "--dataset", ds])
                self.assertEqual(args.dataset, ds)

    def test_invalid_dataset_raises(self):
        with self.assertRaises(SystemExit):
            self._parse(["--project", "p", "--dataset", "invalid"])

    def test_project_from_env(self):
        with patch.dict(os.environ, {"GOOGLE_CLOUD_PROJECT": "env-project"}):
            importlib.reload(self.dashboard)
            args = self._parse([])
            self.assertEqual(args.project, "env-project")

    def test_output_dir_default(self):
        args = self._parse(["--project", "p"])
        self.assertEqual(args.output_dir, "output")

    def test_custom_output_dir(self):
        args = self._parse(["--project", "p", "--output-dir", "/tmp/charts"])
        self.assertEqual(args.output_dir, "/tmp/charts")


class TestMainMissingProject(unittest.TestCase):
    """main() must exit with an error when no project ID is provided."""

    def setUp(self):
        self.dashboard = _load_dashboard()

    def test_missing_project_exits(self):
        with patch("sys.argv", ["dashboard.py"]), \
             patch.dict(os.environ, {}, clear=True), \
             self.assertRaises(SystemExit) as ctx:
            # Reload so env-var default is re-evaluated
            importlib.reload(self.dashboard)
            # Remove GOOGLE_CLOUD_PROJECT so project is empty
            os.environ.pop("GOOGLE_CLOUD_PROJECT", None)
            with patch.object(self.dashboard, "parse_args",
                              return_value=MagicMock(project="", dataset="all",
                                                     output_dir="output")):
                self.dashboard.main()
        self.assertEqual(ctx.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
