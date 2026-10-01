# 🎬 AI Movie Advisor

A movie discovery and recommendation app built with **Streamlit**, **PostgreSQL** and **scikit-learn**. Browse a catalogue, filter by genre, year and rating, search by title, get genre-based recommendations and keep a watchlist. It ships with an AWS EC2 deployment (Nginx reverse proxy + Supervisor).

![AI Movie Advisor screenshot](docs/screenshot.png)

---

## Features

| | |
|---|---|
| 🔍 **Search** | Case-insensitive title search (`ILIKE`) against PostgreSQL |
| 🎛️ **Filters** | Multi-genre selection, year range and minimum rating, applied as SQL filters |
| 🤖 **Recommendations** | Top-rated picks for every selected genre; item-based collaborative filtering engine included (see below) |
| ⭐ **Watchlist** | Per-session watchlist kept in Streamlit session state |
| 🖼️ **Real posters** | Resolved at seed time from TMDB (with an API key) or Wikipedia (no key needed), with a title-card fallback |
| 🗄️ **Persistence** | SQLAlchemy models over PostgreSQL, with a seed script that generates 100 movies and ~5,000 ratings |
| ☁️ **Deployable** | Scripts and configs for Ubuntu on EC2: Nginx, Supervisor, security headers, optional TLS via Certbot |

---

## Architecture

```mermaid
flowchart LR
    user([👤 User<br/>browser])

    subgraph ec2["☁️ AWS EC2 · Ubuntu 22.04"]
        direction LR
        nginx["Nginx :80<br/>reverse proxy<br/>WebSocket upgrade<br/>security headers"]
        subgraph sup["Supervisor"]
            app["Streamlit app :5000<br/><code>app.py</code>"]
        end
        subgraph code["Application layers"]
            direction TB
            ui["UI components<br/><code>components/</code><br/>sidebar · tiles · details"]
            logic["Query helpers<br/><code>utils/data_processing.py</code><br/>filter · search · stats"]
            rec["Recommender<br/><code>models/recommender.py</code><br/>pandas + cosine similarity"]
            orm["SQLAlchemy models<br/><code>models/database.py</code>"]
        end
        pg[("PostgreSQL<br/>movies · ratings")]
    end

    seed["Seed script<br/><code>scripts/init_db.py</code><br/>mock movies + ratings"]
    posters["Poster resolver<br/><code>services/posters.py</code>"]
    tmdb[("TMDB API")]
    wiki[("Wikipedia<br/>page-summary API")]
    tmdbsvc["TMDB service<br/><code>services/tmdb_service.py</code>"]

    user -->|HTTP / WebSocket| nginx --> app
    app --> ui & logic & rec
    logic --> orm
    rec --> orm
    orm --> pg
    seed --> orm
    seed --> posters
    posters -->|"with TMDB_API_KEY"| tmdb
    posters -->|"no key: fallback"| wiki
    user -. "poster images" .-> wiki
    tmdbsvc -. "optional · not yet wired into the UI" .-> tmdb
```

**Request flow:** the browser talks to Nginx, which proxies HTTP and Streamlit's WebSocket to the app on port 5000. Supervisor keeps the Streamlit process running and restarts it on failure. Each interaction re-runs `app.py`, which reads the sidebar filters, queries PostgreSQL through SQLAlchemy and renders movie tiles.

---

## How recommendations work

There are two engines in `models/recommender.py`:

1. **Genre-based (used by the *AI Recommendations* tab).** For each selected genre, it returns the two highest-rated movies in that genre.
2. **Item-based collaborative filtering (`get_similar_movies`).** On startup it loads every rating into a pandas **user × movie** matrix, transposes it, and computes **cosine similarity** between movies with scikit-learn. `get_similar_movies(movie_id, n)` returns the *n* movies whose rating patterns are most similar, so "people who rated this highly also rated these highly". This engine is implemented but not yet surfaced in the UI (see [Roadmap](#roadmap)).

---

## Tech stack

| Layer | Technology |
|---|---|
| UI | Streamlit 1.42+ |
| Data / ML | pandas, NumPy, scikit-learn (cosine similarity), Plotly |
| Persistence | PostgreSQL, SQLAlchemy 2.x, psycopg2 |
| External data | TMDB API via `tmdbv3api` (optional) |
| Hosting | AWS EC2 (Ubuntu), Nginx, Supervisor, Certbot |

---

## Quick start (local)

**Prerequisites:** Python 3.11+, and Docker (or any PostgreSQL 13+).

```bash
git clone https://github.com/codemarquis/ai-movie-advisor.git
cd ai-movie-advisor

# 1. Python environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. PostgreSQL (throwaway container)
docker run -d --name moviedb -p 5432:5432 \
  -e POSTGRES_USER=movie -e POSTGRES_PASSWORD=movie -e POSTGRES_DB=moviedb \
  postgres:16-alpine

# 3. Configure and seed
export DATABASE_URL=postgresql://movie:movie@localhost:5432/moviedb
python scripts/init_db.py          # creates tables, 100 movies, ~5k ratings, fetches posters

# 4. Run
streamlit run app.py               # → http://localhost:8501
```

> `init_db.py` inserts movies with fixed IDs, so run it once against an empty database.
> To refresh posters in a database you've already seeded, run `python scripts/update_posters.py`.

### Movie posters

`services/posters.py` resolves a real poster for each title when the database is seeded:

1. **TMDB**, if `TMDB_API_KEY` is set (free key at [themoviedb.org](https://www.themoviedb.org/settings/api)).
2. **Wikipedia**'s page-summary API otherwise. It needs no key; the lead image of a film's article is its theatrical poster, and the resolver tries `"<Title> (film)"` before the bare title so it doesn't pick up a novel's page.
3. A **title card** from placehold.co if both fail, so a tile is never blank. Failures are logged to stderr.

Posters are hot-linked, not stored in the repo; they belong to their respective studios and distributors.

### Configuration

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | ✅ | SQLAlchemy URL, e.g. `postgresql://user:pass@host:5432/moviedb` |
| `TMDB_API_KEY` | – | Optional. Preferred poster source (and used by `services/tmdb_service.py`); without it posters come from Wikipedia |

---

## Deploying to AWS EC2

```mermaid
flowchart TB
    dev([💻 Developer]) -->|ssh + git clone| ec2
    subgraph ec2["EC2 instance · Security group: 22, 80, 443"]
        setup["deployment/setup_ec2.sh<br/>apt: python, postgresql, nginx, supervisor<br/>pip install -r requirements.txt"]
        setup --> nginxconf["nginx.conf → sites-enabled"]
        setup --> supconf["supervisor.conf → conf.d"]
        supconf --> st["streamlit run app.py :5000"]
        nginxconf --> st
        st --> db[("PostgreSQL<br/>(local, or Amazon RDS)")]
    end
    certbot["certbot --nginx<br/>(optional TLS)"] -.-> nginxconf
```

Step by step: see **[`deployment/README.md`](deployment/README.md)**. In short:

1. Launch Ubuntu 22.04 (t2.small or larger) with ports 22, 80 and 443 open.
2. Clone the repo and run `./deployment/setup_ec2.sh`.
3. Set `DATABASE_URL` (and optionally `TMDB_API_KEY`) for Supervisor, set your domain in `deployment/nginx.conf`, then run `python scripts/init_db.py`.
4. Optionally add TLS with `sudo certbot --nginx -d your_domain.com`.

To scale out, run more Streamlit processes on extra ports and add them to the `upstream streamlit_app` block in `nginx.conf`, or put several instances behind an AWS Application Load Balancer with **Amazon RDS** as the shared database.

---

## Project structure

```
.
├── app.py                     # Streamlit entry point: layout, tabs, wiring
├── components/
│   ├── sidebar.py             # genre / mood / pace / year / rating filters
│   ├── movie_tiles.py         # poster grid, watchlist + details actions
│   └── movie_details.py       # detail card + rating histogram (Plotly)
├── models/
│   ├── database.py            # SQLAlchemy models: Movie, Rating
│   └── recommender.py         # genre + collaborative-filtering recommender
├── services/
│   ├── posters.py             # poster URL resolver: TMDB → Wikipedia → title card
│   └── tmdb_service.py        # TMDB client with Streamlit caching
├── utils/
│   └── data_processing.py     # filter / search / rating-stats queries
├── data/
│   └── mock_movies.py         # mock catalogue + ratings generator
├── scripts/
│   ├── init_db.py             # create tables and seed data (with posters)
│   ├── update_posters.py      # refresh posters in an existing database
│   ├── export_db.py           # dump schema + data
│   └── import_db.py           # restore schema + data
├── deployment/
│   ├── setup_ec2.sh           # one-shot EC2 provisioning
│   ├── nginx.conf             # reverse proxy + security headers
│   ├── supervisor.conf        # keeps Streamlit running
│   └── README.md              # deployment guide
├── schema.sql                 # reference DDL
├── requirements.txt
└── pyproject.toml
```

---

## Database schema

```mermaid
erDiagram
    MOVIES ||--o{ RATINGS : "is rated in"
    MOVIES {
        int id PK
        string title
        string genre
        int year
        float rating
        int votes
        string poster_url
    }
    RATINGS {
        int id PK
        int user_id
        int movie_id FK
        float rating
    }
```

---

## Roadmap

- [ ] Surface collaborative filtering as "Because you liked…" on the details view
- [ ] Wire the TMDB service in for overviews and live catalogues
- [ ] Implement the *mood* and *pace* filters (the sliders exist; the data doesn't yet)
- [ ] Persist watchlists per user instead of per session
- [ ] Update `export_db.py` / `import_db.py` for SQLAlchemy 2.x (`engine.execute` was removed)
- [ ] Containerise (Dockerfile + compose) and add CI

---

## License

[MIT](LICENSE)
