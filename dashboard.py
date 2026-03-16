"""
BigQuery Data Dashboard
=======================
Queries public Google BigQuery datasets, analyzes trends,
and visualizes them using Pandas and Matplotlib.

Datasets used:
  - bigquery-public-data.hacker_news.stories
  - bigquery-public-data.stackoverflow.posts_questions
  - bigquery-public-data.noaa_gsod.gsod*
  - bigquery-public-data.github_repos.commits

Authentication:
  Set the environment variable GOOGLE_APPLICATION_CREDENTIALS to the path
  of your service-account JSON key, OR run `gcloud auth application-default
  login` to use user credentials.
  Set GOOGLE_CLOUD_PROJECT to your GCP project ID.

Usage:
  python dashboard.py [--project PROJECT_ID] [--output-dir OUTPUT_DIR] [--dataset DATASET]

  DATASET options: hackernews, stackoverflow, noaa, github, all (default: all)
"""

import argparse
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive backend for script usage
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

try:
    from google.cloud import bigquery
except ImportError:
    print("ERROR: google-cloud-bigquery is not installed.\n"
          "Run:  pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_sql(filename: str) -> str:
    """Load a SQL query from the queries/ directory next to this script."""
    queries_dir = Path(__file__).parent / "queries"
    return (queries_dir / filename).read_text(encoding="utf-8")


def _run_query(client: bigquery.Client, sql: str) -> pd.DataFrame:
    """Execute *sql* and return a Pandas DataFrame."""
    job = client.query(sql)
    return job.result().to_dataframe()


def _save_figure(fig: plt.Figure, output_dir: Path, name: str) -> None:
    """Save *fig* as a PNG to *output_dir*."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    print(f"  Saved: {path}")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Analysis functions
# ---------------------------------------------------------------------------

def analyze_hackernews(client: bigquery.Client, output_dir: Path) -> None:
    """Hacker News story submission and engagement trends by year."""
    print("\n[1/4] Analyzing Hacker News story trends …")
    sql = _load_sql("hackernews_stories_trends.sql")
    df = _run_query(client, sql)
    df = df.sort_values("story_year").reset_index(drop=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Hacker News Story Trends (2010–2022)", fontsize=14, fontweight="bold")

    # Total stories per year
    axes[0].bar(df["story_year"], df["total_stories"], color="steelblue", edgecolor="white")
    axes[0].set_title("Total Stories Submitted per Year")
    axes[0].set_xlabel("Year")
    axes[0].set_ylabel("Number of Stories")
    axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    axes[0].tick_params(axis="x", rotation=45)

    # Average score & comments per year
    ax2 = axes[1].twinx()
    axes[1].plot(df["story_year"], df["avg_score"], color="darkorange", marker="o", label="Avg Score")
    ax2.plot(df["story_year"], df["avg_comments"], color="forestgreen", marker="s",
             linestyle="--", label="Avg Comments")
    axes[1].set_title("Average Score & Comments per Year")
    axes[1].set_xlabel("Year")
    axes[1].set_ylabel("Average Score", color="darkorange")
    ax2.set_ylabel("Average Comments", color="forestgreen")
    lines1, labels1 = axes[1].get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    axes[1].legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=9)
    axes[1].tick_params(axis="x", rotation=45)

    plt.tight_layout()
    _save_figure(fig, output_dir, "hackernews_trends.png")


def analyze_stackoverflow(client: bigquery.Client, output_dir: Path) -> None:
    """Stack Overflow question volume and quality trends by year."""
    print("\n[2/4] Analyzing Stack Overflow question trends …")
    sql = _load_sql("stackoverflow_questions_trends.sql")
    df = _run_query(client, sql)
    df = df.sort_values("question_year").reset_index(drop=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Stack Overflow Question Trends (2010–2022)", fontsize=14, fontweight="bold")

    # Total questions per year
    axes[0].bar(df["question_year"], df["total_questions"], color="salmon", edgecolor="white")
    axes[0].set_title("Total Questions per Year")
    axes[0].set_xlabel("Year")
    axes[0].set_ylabel("Number of Questions")
    axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    axes[0].tick_params(axis="x", rotation=45)

    # Avg views per year
    axes[1].fill_between(df["question_year"], df["avg_views"], alpha=0.5, color="mediumpurple")
    axes[1].plot(df["question_year"], df["avg_views"], color="mediumpurple", marker="o")
    axes[1].set_title("Average Views per Question per Year")
    axes[1].set_xlabel("Year")
    axes[1].set_ylabel("Average View Count")
    axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    axes[1].tick_params(axis="x", rotation=45)

    plt.tight_layout()
    _save_figure(fig, output_dir, "stackoverflow_trends.png")


def analyze_noaa_weather(client: bigquery.Client, output_dir: Path) -> None:
    """NOAA GSOD global temperature and precipitation trends by year."""
    print("\n[3/4] Analyzing NOAA global weather trends …")
    sql = _load_sql("noaa_weather_trends.sql")
    df = _run_query(client, sql)
    df = df.sort_values("year").reset_index(drop=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Global Weather Trends – NOAA GSOD (2000–2022)", fontsize=14, fontweight="bold")

    # Temperature trend
    axes[0].plot(df["year"], df["avg_temp_fahrenheit"], color="tomato", marker="o", label="Avg Temp")
    axes[0].fill_between(df["year"], df["avg_min_temp"], df["avg_max_temp"],
                         alpha=0.2, color="tomato", label="Min–Max Range")
    axes[0].set_title("Average Global Temperature (°F)")
    axes[0].set_xlabel("Year")
    axes[0].set_ylabel("Temperature (°F)")
    axes[0].legend(fontsize=9)
    axes[0].tick_params(axis="x", rotation=45)

    # Rainy days trend
    axes[1].bar(df["year"], df["rainy_days"], color="cornflowerblue", edgecolor="white")
    axes[1].set_title("Total Rainy Station-Days per Year")
    axes[1].set_xlabel("Year")
    axes[1].set_ylabel("Station-Days with Precipitation")
    axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    axes[1].tick_params(axis="x", rotation=45)

    plt.tight_layout()
    _save_figure(fig, output_dir, "noaa_weather_trends.png")


def analyze_github(client: bigquery.Client, output_dir: Path) -> None:
    """GitHub commit activity trends by year."""
    print("\n[4/4] Analyzing GitHub commit trends …")
    sql = _load_sql("github_commit_trends.sql")
    df = _run_query(client, sql)
    df = df.sort_values("commit_year").reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.suptitle("GitHub Public Repo Commit Trends (2010–2022)", fontsize=14, fontweight="bold")

    ax.fill_between(df["commit_year"], df["total_commits"], alpha=0.4, color="mediumseagreen")
    ax.plot(df["commit_year"], df["total_commits"], color="mediumseagreen", marker="o")
    ax.set_title("Total Commits per Year")
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of Commits")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.tick_params(axis="x", rotation=45)

    plt.tight_layout()
    _save_figure(fig, output_dir, "github_commit_trends.png")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="BigQuery Data Dashboard – query, analyze, and visualize public datasets."
    )
    parser.add_argument(
        "--project",
        default=os.environ.get("GOOGLE_CLOUD_PROJECT", ""),
        help="GCP project ID to bill for query costs (can also be set via GOOGLE_CLOUD_PROJECT).",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory where chart PNG files are saved (default: ./output).",
    )
    parser.add_argument(
        "--dataset",
        choices=["hackernews", "stackoverflow", "noaa", "github", "all"],
        default="all",
        help="Which dataset analysis to run (default: all).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.project:
        print(
            "ERROR: GCP project ID is required.\n"
            "Pass --project PROJECT_ID or set the GOOGLE_CLOUD_PROJECT environment variable.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"BigQuery Data Dashboard")
    print(f"  Project : {args.project}")
    print(f"  Output  : {args.output_dir}")
    print(f"  Dataset : {args.dataset}")

    client = bigquery.Client(project=args.project)
    output_dir = Path(args.output_dir)

    runners = {
        "hackernews": analyze_hackernews,
        "stackoverflow": analyze_stackoverflow,
        "noaa": analyze_noaa_weather,
        "github": analyze_github,
    }

    if args.dataset == "all":
        for fn in runners.values():
            fn(client, output_dir)
    else:
        runners[args.dataset](client, output_dir)

    print(f"\nDone! Charts saved to: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
