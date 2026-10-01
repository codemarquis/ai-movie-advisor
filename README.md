# 🎬 AI Movie Advisor

[![CI](https://github.com/codemarquis/ai-movie-advisor/actions/workflows/ci.yml/badge.svg)](https://github.com/codemarquis/ai-movie-advisor/actions/workflows/ci.yml)

A movie discovery and recommendation app built with **Streamlit**, **PostgreSQL** and **scikit-learn**. Browse 50 well-known films with their real posters, filter by genre, mood, pace, year and rating, keep a watchlist, and get **collaborative-filtering recommendations** ("people who liked this also liked…"). It deploys to a single AWS EC2 host behind Nginx, with least-privilege database access.

![AI Movie Advisor: poster grid with filters](docs/screenshot.png)

---

## Features

| | |
|---|---|
| 🖼️ **Real posters** | Resolved per film from TMDB (with an API key) or Wikipedia (no key needed), with a title-card fallback |
| 🔍 **Search** | Title search that treats input literally (`%` and `_` are not wildcards), capped at 100 characters |
| 🎛️ **Filters** | Genres, year range (taken from the data), minimum rating, and an optional **mood & pace** match |
| 🤖 **Recommendations** | *Because of your watchlist* (item-based collaborative filtering) and *Top picks in your genres* |
| 📖 **Details** | Dialog with rating, number of user ratings and *People who liked this also liked* |
| ⭐ **Watchlist** | One-click add / remove, kept for the session |
| 🔐 **Zero trust** | Escaped output, https-only images, read-only app database role, hardened Nginx and Streamlit; see [Security](#security) |

![Details dialog with collaborative-filtering suggestions](docs/details.png)

---

## Architecture

The code is layered so each part has one job and depends only on the layers below it:

```mermaid
flowchart TB
    subgraph ui["UI · Streamlit"]
        app["app.py<br/>controller: wires data to components"]
        comps["components/<br/>sidebar · movie_tiles · movie_details<br/>safe.py: output escaping"]
    end

    subgraph svc["Services · pure logic"]
        rec["recommender.py<br/>item-based CF (cosine similarity)"]
        mood["mood.py<br/>genre mood/pace profiles"]
        posters["posters.py<br/>TMDB → Wikipedia → placeholder"]
    end

    subgraph data["Data access"]
        repo["repositories/movie_repository.py<br/>every SQL query · returns domain objects"]
        db["models/database.py<br/>tables · pooled engines · sessions"]
        domain["models/domain.py<br/>Movie · MovieFilters · RatingStats"]
    end

    config["config.py<br/>env / .env, validated"]
    scripts["scripts/<br/>init_db · update_posters · export_db · import_db"]
    pg[("PostgreSQL<br/>movies · ratings")]

    app --> comps
    app --> repo
    app --> rec
    repo --> mood
    repo --> db
    repo -.-> domain
    comps -.-> domain
    scripts --> repo
    scripts --> posters
    db --> config
    posters --> config
    db -->|"read-only (app)"| pg
    db -->|"read-write (scripts)"| pg
```

| Layer | Knows about | Never does |
|---|---|---|
| **UI** (`app.py`, `components/`) | domain objects, repository and service APIs | write SQL, open connections, trust strings as markup |
| **Services** (`services/`) | plain Python and pandas data | touch Streamlit or the database |
| **Data access** (`repositories/`, `models/`) | SQLAlchemy, PostgreSQL | return ORM rows or sessions to callers |
| **Config** (`config.py`) | environment variables | hard-code secrets or log them |
| **Admin scripts** (`scripts/`) | repository write functions | run with the web app's credentials |

### Request flow

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant N as Nginx
    participant S as Streamlit (app.py)
    participant R as Repository
    participant P as PostgreSQL (read-only role)
    participant C as Recommender (cached)

    U->>N: HTTPS / WebSocket
    N->>S: proxy to 127.0.0.1:8501 (rate-limited)
    S->>R: find_movies(filters) / search_movies(term)
    R->>P: parameterised SELECT
    P-->>R: rows
    R-->>S: Movie objects
    S-->>U: tiles (escaped text, https posters)
    U->>S: Details / watchlist
    S->>C: similar_to(id) / recommend_for(watchlist)
    C-->>S: movie ids
    S->>R: get_movies(ids)
    S-->>U: dialog + recommendations
```

### How recommendations work

- **Collaborative filtering** (`services/recommender.py`). Ratings become a user × movie matrix; **cosine similarity** between the movie columns says which films are rated alike. `similar_to(id)` powers the details dialog, and `recommend_for(watchlist)` sums similarity across everything you saved. The model is pure (no database access) and built once per hour from `ratings_frame()`.
- **Mood & pace** (`services/mood.py`). Each genre has a typical mood (light → dark) and pace (slow → fast). With *Match my mood & pace* on, only genres within one step of your sliders are shown.
- **Top picks in your genres.** The highest-rated films in each selected genre.

### Data

50 real films (title, year, genre). User ratings are **synthetic**: 300 simulated users with two favourite genres each, generated deterministically (`data/seed.py`), so every install gets the same data and the recommender has real taste patterns to learn. Each movie's rating and vote count are derived from those ratings.

---

## Quick start (local)

**Prerequisites:** Python 3.11+ and Docker (or any PostgreSQL 13+).

```bash
git clone https://github.com/codemarquis/ai-movie-advisor.git
cd ai-movie-advisor

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

docker run -d --name moviedb -p 5432:5432 \
  -e POSTGRES_USER=movie -e POSTGRES_PASSWORD=movie -e POSTGRES_DB=moviedb \
  postgres:16-alpine

cp .env.example .env
# local dev: set DATABASE_URL=postgresql://movie:movie@localhost:5432/moviedb
#            and remove ADMIN_DATABASE_URL (it falls back to DATABASE_URL)

python scripts/init_db.py      # tables + 50 movies + ratings + posters (safe to re-run)
streamlit run app.py           # → http://127.0.0.1:8501
```

### Configuration

| Variable | Required | Used by | Notes |
|---|---|---|---|
| `DATABASE_URL` | ✅ | web app | Every transaction is read-only. In production use the `ama_app` role from [`deployment/db_roles.sql`](deployment/db_roles.sql) |
| `ADMIN_DATABASE_URL` | – | scripts | Write access for seeding, imports and poster refreshes. Falls back to `DATABASE_URL` |
| `TMDB_API_KEY` | – | posters | Preferred poster source; without it posters come from Wikipedia |

Settings are read from the environment or a local `.env` (gitignored). Add `?sslmode=require` to the URLs for RDS or other managed PostgreSQL.

### Scripts

| Command | What it does |
|---|---|
| `python scripts/init_db.py` | Create tables and seed. Does nothing if movies already exist |
| `python scripts/init_db.py --reset` | Drop all tables and reseed (**destroys data**) |
| `python scripts/update_posters.py` | Re-resolve every poster URL in an existing database |
| `python scripts/export_db.py --out export` | Write `export/schema.sql` and `export/data.json` |
| `python scripts/import_db.py --file export/data.json` | Load an export; rejects unknown tables or columns; all-or-nothing |

### Movie posters

`services/posters.py` tries, in order: **TMDB** (if `TMDB_API_KEY` is set), then **Wikipedia's** page-summary API (`"Title (YEAR film)"`, then `"Title (film)"`, then `"Title"`, keeping only pages described as films), then a **title card**. Only `https://` image URLs are accepted, and failures are logged without secrets. Posters are hot-linked rather than stored; they belong to their studios and distributors.

---

## Security

The app treats every boundary as untrusted (zero trust):

| Threat | Control |
|---|---|
| HTML/Markdown injection through titles or genres | All text is escaped in `components/safe.py` before rendering; tested with hostile titles |
| Malicious image URLs (`javascript:`, `http:`) | Only `https://` posters are stored or rendered; anything else becomes a placeholder |
| SQL injection | SQLAlchemy parameterised queries only; search input is wildcard-escaped and length-capped |
| A compromised or buggy app writing data | The app's DB role can only `SELECT`, **and** every app transaction is `READ ONLY`; writes need the separate admin URL |
| Tampered import files | `import_db.py` allows only known tables and columns and uses parameterised inserts in one transaction |
| Leaking internals | Generic error messages in the UI (`showErrorDetails = "none"`); details go to server logs; the TMDB key is redacted from logs |
| Direct access bypassing the proxy | Streamlit binds `127.0.0.1` only; Nginx is the single entry point |
| Abuse / DoS | Nginx per-IP rate limiting and a 1 MB body limit; XSRF protection on |
| Secrets in git | `.env` is gitignored and `chmod 600` on servers; only `.env.example` is committed |
| Vulnerable dependencies | `pip-audit` runs in CI on every pull request |

---

## Deploying to AWS EC2

```mermaid
flowchart LR
    user([👤 User]) -->|"HTTPS :443"| nginx
    subgraph ec2["EC2 · Ubuntu 22.04/24.04 · SG: 22 (your IP), 80, 443"]
        nginx["Nginx<br/>TLS (certbot) · rate limit<br/>security headers"]
        sup["Supervisor<br/>runs as app user"]
        app["Streamlit<br/>127.0.0.1:8501"]
        env[".env (chmod 600)"]
        nginx --> app
        sup --> app
        app -.reads.-> env
    end
    app -->|"ama_app · read-only · sslmode=require"| rds[("Amazon RDS<br/>PostgreSQL")]
    admin(["🧑‍💻 Admin scripts"]) -->|"movie_admin"| rds
```

```bash
# On the instance, as the ubuntu user, from a clone of this repo:
./deployment/setup_ec2.sh           # nginx, supervisor, virtualenv, .env, configs
psql "$MASTER_URL" -v app_password=… -v admin_password=… -f deployment/db_roles.sql
nano .env                           # DATABASE_URL (ama_app), ADMIN_DATABASE_URL (movie_admin)
.venv/bin/python scripts/init_db.py
sudo supervisorctl restart ai-movie-advisor
sudo certbot --nginx -d your_domain.com
```

Full guide: **[`deployment/README.md`](deployment/README.md)**.

---

## Development

```bash
pip install -r requirements-dev.txt
ruff check .
pytest                                                    # unit tests (no DB needed)
TEST_DATABASE_URL=postgresql://movie:movie@localhost:5432/testdb pytest   # + integration tests
pip-audit -r requirements.txt
```

CI ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs ruff, shellcheck, `nginx -t`, the full test suite against PostgreSQL, and pip-audit on every pull request.

### Project structure

```
.
├── app.py                      # Streamlit controller (no SQL)
├── config.py                   # env/.env settings, validated
├── components/
│   ├── safe.py                 # output escaping, https-only posters
│   ├── sidebar.py              # filters → MovieFilters
│   ├── movie_tiles.py          # poster grid, watchlist / details buttons
│   └── movie_details.py        # details dialog body
├── models/
│   ├── domain.py               # Movie, MovieFilters, RatingStats
│   └── database.py             # tables, engines (read-only / admin), sessions
├── repositories/
│   └── movie_repository.py     # all queries and writes
├── services/
│   ├── recommender.py          # collaborative filtering (pure)
│   ├── mood.py                 # genre mood/pace profiles
│   ├── posters.py              # poster resolver
│   └── tmdb_service.py         # TMDB client (not yet used by the UI)
├── data/seed.py                # 50 real films + deterministic synthetic ratings
├── scripts/                    # init_db, update_posters, export_db, import_db
├── deployment/                 # setup_ec2.sh, nginx.conf, supervisor.conf, db_roles.sql
├── tests/                      # unit + integration tests
├── .streamlit/config.toml      # production-safe Streamlit settings
├── .env.example
└── schema.sql                  # reference DDL
```

### Database schema

```mermaid
erDiagram
    MOVIES ||--o{ RATINGS : "is rated in"
    MOVIES {
        int id PK
        string title
        string genre
        int year
        float rating "0-5"
        int votes
        string poster_url "https only"
    }
    RATINGS {
        int id PK
        int user_id
        int movie_id FK "indexed"
        float rating "0.5-5"
    }
```

---

## Roadmap

- [ ] Persist watchlists per signed-in user (currently per session)
- [ ] Use the TMDB client for overviews and a live catalogue
- [ ] Containerise (Dockerfile + compose) and add a deploy workflow
- [ ] Alembic migrations for schema changes on existing databases

---

## License

[MIT](LICENSE)
