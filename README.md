# CyberTrace — Digital Footprint & Privacy Risk Analyzer

> **Understand Your Digital Footprint. Take Control of Your Privacy.**

CyberTrace is an educational privacy self-assessment platform built entirely with
Python and Streamlit. It walks users through a structured questionnaire across
six digital-privacy categories, computes a transparent weighted risk score,
visualizes exposure, generates personalized recommendations, and produces a
downloadable PDF report — all without any paid APIs or external AI services.

---

## ⚠️ What this tool is (and is not)

CyberTrace evaluates **information the user supplies** and **risk inferred from
it**. It does **not**:

- Search data-breach databases or confirm breach status
- Monitor the dark web
- Operate as a people-search engine
- Scrape or log into social media accounts
- Fetch or verify any URL you enter (format-validated only)
- Predict identity theft or guarantee safety

See the in-app **About & Limitations** page for full details.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend / UI | Python 3.11+, Streamlit |
| Data | Pandas, SQLite (default), SQLAlchemy (ORM / DB abstraction) |
| Visualization | Plotly |
| PDF Reports | ReportLab |
| Auth | bcrypt (password hashing) |
| Testing | pytest |

No PHP, Node.js, React, or MySQL dependency. Runs on Python + Streamlit alone.

---

## Project Structure

```
cybertrace/
├── app.py                      # Main Streamlit entrypoint (navigation/routing)
├── requirements.txt
├── .streamlit/
│   ├── config.toml             # Theme configuration
│   └── secrets.toml.example    # Template — copy to secrets.toml, never commit it
├── app/
│   ├── core/                   # Pure business logic (no Streamlit/DB imports except session.py/auth.py)
│   │   ├── questions.py        # Question bank (6 categories, weights, risk mappings)
│   │   ├── scoring.py          # Authoritative weighted scoring engine
│   │   ├── recommendations.py  # Rule-based recommendation engine
│   │   ├── profile_audit.py    # Manual profile privacy-audit scoring
│   │   ├── pdf_report.py       # ReportLab PDF generation
│   │   ├── auth.py             # Registration/login/session management
│   │   └── session.py          # In-progress assessment session-state helpers
│   ├── db/
│   │   ├── models.py           # SQLAlchemy ORM models
│   │   ├── connection.py       # Engine/session factory + storage backend selection
│   │   └── repository.py       # User-scoped data access functions
│   ├── ui/
│   │   ├── styles.py           # Custom CSS (dark navy/cyan theme)
│   │   ├── charts.py           # Plotly chart builders
│   │   └── components.py       # Reusable Streamlit UI components
│   └── pages/                  # One module per sidebar page
├── tests/                      # pytest unit & integration tests
└── data/                       # Local SQLite file lives here (gitignored)
```

---

## Local Setup

```bash
# 1. Clone and enter the project
git clone <your-fork-url> cybertrace
cd cybertrace

# 2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Configure a hosted database — see "Storage" below.
#    Skip this step to use the local SQLite fallback.
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# 5. Run the app
streamlit run app.py
```

The app will be available at `http://localhost:8501`.

---

## Running Tests

```bash
pip install -r requirements.txt   # includes pytest
pytest tests/ -v
```

Test coverage includes:
- **`test_scoring.py`** — the weighted scoring formula, all 4 risk-level
  boundaries (0/24/25/49/50/74/75/100), "Not applicable" exclusion, reverse
  scoring, and score-bounds enforcement (26 tests).
- **`test_recommendations.py`** — recommendation generation traceability,
  priority sorting, and reverse-scored question handling (11 tests).
- **`test_profile_audit.py`** — URL scheme validation and manual profile
  audit scoring (15 tests).
- **`test_auth_validation.py`** — username/password validation rules and
  bcrypt hash/verify round-trips.
- **`test_db_repository.py`** — assessment save/retrieve round-trips,
  historical-immutability on re-assessment, and **strict per-user ownership
  isolation** (a user can never read, modify, or delete another user's data).

---

## Storage & Persistence — Important Notes for Deployment

CyberTrace uses **SQLite by default** for simplicity and zero-config local
development. A `SQLAlchemy`-based abstraction layer (`app/db/connection.py`)
means swapping to a hosted database requires **no code changes** — only a
configuration change.

### ⚠️ Streamlit Community Cloud storage warning

**Local SQLite storage on Streamlit Community Cloud is not guaranteed to
persist.** The underlying filesystem is ephemeral and can be wiped on
redeploys, restarts, or sleep/wake cycles. The app displays an in-app warning
whenever it detects it is running without a hosted database configured (see
the **About & Limitations** page).

### Using a hosted database (recommended for real deployments)

1. Provision any SQLAlchemy-compatible database (e.g. Postgres on Supabase,
   Neon, Railway, or your own server).
2. In Streamlit Community Cloud, open your app's **Settings → Secrets** and
   add:
   ```toml
   [database]
   url = "postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME"
   ```
3. Redeploy. CyberTrace will automatically detect and use the hosted
   database — no code changes needed.

**Never commit real credentials.** `.streamlit/secrets.toml` is listed in
`.gitignore`; only the `.example` template is committed.

---

## Deploying to Streamlit Community Cloud

1. Push this repository to GitHub (public or private).
2. Go to [share.streamlit.io](https://share.streamlit.io) and click **New app**.
3. Select your repository, branch, and set the main file path to `app.py`.
4. (Optional but recommended) Add your `[database]` secret as described above.
5. Click **Deploy**.

---

## Security & Privacy Design Notes

- Passwords are hashed with **bcrypt** (12 rounds) and never stored or logged
  in plaintext.
- Every database query that touches a user's assessment or profile-audit data
  filters strictly by `user_id` — verified in `tests/test_db_repository.py`.
- All SQL goes through SQLAlchemy's parameterized ORM layer; no raw
  string-built queries.
- Profile URLs are validated for scheme (`http`/`https` only) but are **never
  fetched** by the backend.
- No arbitrary server-side URL fetching, no scraping, no third-party
  authentication.
- Account deletion permanently cascades to all owned assessments,
  recommendations-completion records, and profile audits.
- `st.session_state` is used only for UI convenience (current page, in-progress
  answers); every actual data read/write re-verifies ownership against the
  database, so session state alone is never treated as an authorization
  mechanism.

---

## License / Disclaimer

CyberTrace is an educational tool provided as-is, without warranty. It is not
a substitute for professional cybersecurity, legal, or identity-protection
advice.
