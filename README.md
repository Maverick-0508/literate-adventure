# BigQuery Data Dashboard

Query public Google BigQuery datasets, analyze trends, and visualize them
using **Pandas** and **Matplotlib**.  SQL queries are authored and run
directly from **VS Code** using the [SQLtools](https://marketplace.visualstudio.com/items?itemName=mtxr.sqltools)
extension with the [SQLtools BigQuery driver](https://marketplace.visualstudio.com/items?itemName=mtxr.sqltools-driver-bigquery).

---

## Datasets

| Dataset | BigQuery path |
|---------|--------------|
| Hacker News | `bigquery-public-data.hacker_news.stories` |
| Stack Overflow | `bigquery-public-data.stackoverflow.posts_questions` |
| NOAA GSOD weather | `bigquery-public-data.noaa_gsod.gsod*` |
| GitHub repos | `bigquery-public-data.github_repos.commits` |

---

## Project structure

```
.
├── dashboard.py                  # Main Python dashboard script
├── requirements.txt              # Python dependencies
├── queries/
│   ├── hackernews_stories_trends.sql
│   ├── stackoverflow_questions_trends.sql
│   ├── noaa_weather_trends.sql
│   └── github_commit_trends.sql
├── test_dashboard.py             # Unit tests (no GCP credentials needed)
└── .vscode/
    ├── settings.json             # SQLtools BigQuery connection settings
    └── extensions.json           # Recommended VS Code extensions
```

---

## Prerequisites

- Python 3.9+
- A Google Cloud project (queries run against public datasets; billing is per
  byte scanned, but most queries here scan only a few GB)
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) **or** a
  service-account JSON key

---

## Setup

### 1 – Install Python dependencies

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2 – Authenticate with Google Cloud

**Option A – user credentials (recommended for local development)**

```bash
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT=your-gcp-project-id
```

**Option B – service-account key**

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
export GOOGLE_CLOUD_PROJECT=your-gcp-project-id
```

### 3 – Configure VS Code SQLtools

Open the project in VS Code.  When prompted, install the recommended
extensions (`mtxr.sqltools` and `mtxr.sqltools-driver-bigquery`).

The connection is pre-configured in `.vscode/settings.json` and reads
`GOOGLE_CLOUD_PROJECT` / `GOOGLE_APPLICATION_CREDENTIALS` from your
environment.  Open any `.sql` file in `queries/` and press
**Ctrl + E, Ctrl + E** (or click *Run on active connection*) to execute it.

---

## Running the dashboard

```bash
# Run all analyses (outputs PNGs to ./output/)
python dashboard.py --project your-gcp-project-id

# Run a single dataset analysis
python dashboard.py --project your-gcp-project-id --dataset hackernews

# Choose a custom output directory
python dashboard.py --project your-gcp-project-id --output-dir ./charts
```

Available `--dataset` values: `hackernews`, `stackoverflow`, `noaa`, `github`, `all`

Charts are saved as PNG files in the output directory:

| File | Contents |
|------|----------|
| `hackernews_trends.png` | Story volume, avg score & comments by year |
| `stackoverflow_trends.png` | Question volume and avg view count by year |
| `noaa_weather_trends.png` | Global avg temperature and rainy days by year |
| `github_commit_trends.png` | Total public commits by year |

---

## Running the tests

No GCP credentials are needed – the tests mock the BigQuery client.

```bash
python -m pytest test_dashboard.py -v
# or
python -m unittest test_dashboard -v
```

---

## Environment variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_CLOUD_PROJECT` | GCP project ID used for query billing |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service-account JSON key (optional if using `gcloud auth`) |