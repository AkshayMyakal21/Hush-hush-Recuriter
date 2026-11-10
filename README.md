# HushHush Recruiter

A recruiter tool that discovers and ranks candidates from GitHub for a chosen role. It collects public profile data through the GitHub API, scores candidates on a set of activity signals, groups them with unsupervised clustering, trains a classifier on those groups, and presents the results in an interactive Streamlit dashboard.

## Setup

```bash
# create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# install dependencies
pip install -r requirements.txt
```

Create a `.env` file in the project root (see `.env.example`) with your GitHub token:

```
GITHUB_TOKEN=your_token_here
```

## Running

```bash
# 1. collect data, score, cluster, and train the model (fills hushhush.db + model.joblib)
python main.py        # prompts you to enter a role

# 2. launch the dashboard
streamlit run app.py
```

`main.py` asks for a role from the list defined in `config.py`
(`software_engineer`, `data_scientist`, `ml engineer`, `backend engineer`, `cloud engineer`)
and searches GitHub with role-specific queries.

## Email Notifications

The dashboard has a **Notify Selected Candidates** section that emails the list of
selected candidates to a chosen address (defaults to the one in `NOTIFY_EMAIL`).
The same notification is also sent automatically at the end of `python main.py`
whenever SMTP credentials are configured.

Add the following to your `.env` file (see `.env.example`). For Gmail, `SMTP_PASSWORD`
must be a [Google App Password](https://support.google.com/accounts/answer/185833),
not your normal login password:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
NOTIFY_EMAIL=vivekchaudhary1816@gmail.com
```

If `SMTP_USER` / `SMTP_PASSWORD` are not set, the pipeline simply skips the email
step and the dashboard shows a clear error when you click send. No extra packages
are required — email sending uses Python's built-in `smtplib`.

## GitHub Data Points

| Field | Description |
|-------|-------------|
| `username` | GitHub username |
| `followers` | Total followers the candidate has |
| `profile_url` | URL to the candidate's profile |
| `public_repos` | Number of public repositories |
| `total_stars` | Total stars across the candidate's repos |
| `total_forks` | Total forks across the candidate's repos |
| `commit_count` | Public commit activity in the last 90 days |
| `top_language` | Most-used language across repos |
| `github_score` | Weighted score computed from the signals above |
| `is_selected` | Whether the candidate was selected |

## Quickstart & Deployment Guide

### 1. Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
- A GitHub Personal Access Token (`ghp_...`).

### 2. Environment Configuration
Ensure you have a `.env` file in the root folder containing your GitHub token:
```env
GITHUB_TOKEN=ghp_your_personal_access_token_here
```

### 3. Initial Setup & Candidate Fetch (One-Time)
Initialize local database records and train the classifier model before launching the web UI:
```bash
# Create local storage files for volume mounting
touch hushhush.db model.joblib

# Interactively run the candidate ingestion pipeline inside Docker
docker compose run --rm recruiter-app python main.py
```

### 4. Deploying & Updating the Dashboard (CD)
Whenever you commit and push new features to GitHub, run the automated deployment script:
#### Using Git Bash:
chmod +x deploy.sh
./deploy.sh

Access the live recruiter dashboard in your browser at:
http://localhost:8501

Re-run Pipeline to Fetch New Candidates
docker compose run --rm recruiter-app python main.py

## System Archicture

                  +---------------------------+
                  |   Role Input (config.py)  |
                  |  role -> search queries   |
                  +-------------+-------------+
                                |
                                v
                  +---------------------------+
                  |  GitHub API Client (async)|
                  |  github_api_client.py     |
                  |  search users / repos /   |
                  |  events, batched          |
                  +-------------+-------------+
                                |
                                v
                  +---------------------------+
                  |   Parsing (parser_api.py) |
                  |  extract followers, repos,|
                  |  stars, forks, top lang,  |
                  |  90-day commit count      |
                  +-------------+-------------+
                                |
                                v
                  +---------------------------+
                  |   Scoring (scorer.py)     |
                  |  min-max normalize +      |
                  |  weighted github_score    |
                  +-------------+-------------+
                                |
                                v
                  +---------------------------+
                  |  Clustering (clustering.py)|
                  |  KMeans (k=2) on log-scale|
                  |  features -> strong group |
                  |  = is_selected            |
                  +-------------+-------------+
                                |
                                v
                  +---------------------------+
                  |   Rule filter (main.py)   |
                  |  commit_count < 30        |
                  |  -> not selected          |
                  +-------------+-------------+
                                |
                                v
                  +---------------------------+
                  |   Storage (database.py)   |
                  |  SQLite: candidates,      |
                  |  scores, candidate_queries|
                  +-------------+-------------+
                                |
                                v
                  +---------------------------+
                  |  Classifier (classifier.py)|
                  |  RandomForest trained on  |
                  |  cluster labels -> verdict|
                  |  + confidence %           |
                  +-------------+-------------+
                                |
                                v
                  +---------------------------+
                  |   Dashboard (app.py)      |
                  |  Streamlit: metrics,      |
                  |  ranked table, filters,   |
                  |  top-10 score chart       |
                  +-------------+-------------+
                                |
                                v
                DOCKER & CI/CD DEPLOYMENT PIPELINE
                                |
                                v
                  +---------------------------+
                  |  GitHub Actions CI        |
                  |  .github/workflows/ci.yml |
                  |  - flake8 syntax check    |
                  |  - SQLite DB schema test  |
                  |  - Docker image build test|
                  +-------------+-------------+
                                |
                        (On Push / Merge)
                                |
                                v
                  +---------------------------+
                  |  1-Command CD Script      |
                  |  deploy.sh / deploy.ps1   |
                  |  - git pull origin main   |
                  |  - rebuild Docker image   |
                  |  - restart container      |
                  +-------------+-------------+
                                |
                                v
                  +---------------------------+
                  |  Docker Container         |
                  |  Dockerfile + compose.yml |
                  |  - Python 3.10-slim env   |
                  |  - Mounts hushhush.db     |
                  |  - Mounts model.joblib    |
                  |  - Exposes Port 8501      |
                  +---------------------------+

## Project Structure

| File | Responsibility |
|------|----------------|
| `main.py` | Orchestrates the full pipeline end to end |
| `config.py` | Role-to-query mapping and query builder |
| `api_integration/github_api_client.py` | Async GitHub API client |
| `api_integration/parser_api.py` | Parses raw API responses into candidate features |
| `models.py` | `Candidate` dataclass |
| `scorer.py` | Feature normalization and weighted scoring |
| `clustering.py` | KMeans clustering and strong-cluster selection |
| `classifier.py` | RandomForest training, prediction, and confidence |
| `database.py` | SQLite schema and read/write helpers |
| `notifier.py` | Builds and sends the selected-candidate email over SMTP |
| `app.py` | Streamlit dashboard |
| `Dockerfile` | Defines the Python 3.10 container environment, dependency installation, and Streamlit execution. |
| `.dockerignore` | Keeps build contexts lightweight by ignoring `.git`, `.venv`, `__pycache__`, and `.env`. |
| `docker-compose.yml` | Manages container configuration, port mapping (`8501:8501`), `.env` loading, and persistent file volume mounting. |
| `.github/workflows/ci.yml` | GitHub Actions workflow for linting code, validating database tables, and testing Docker image builds. |
| `deploy.sh` | Bash script for 1-command deployment in Git Bash / Linux environments. |
| `deploy.ps1` | Native PowerShell script for 1-command deployment in Windows environments. |
| `requirements.txt` | *(Updated)* Fixed version compatibility constraints for Python 3.10 (`numpy==1.26.4`, `pandas==2.2.2`). |

---

