-- Schema created by models/database.py (SQLAlchemy). Kept here for reference.

CREATE TABLE movies (
    id          INTEGER PRIMARY KEY,
    title       VARCHAR NOT NULL,
    genre       VARCHAR NOT NULL,
    year        INTEGER NOT NULL,
    rating      FLOAT,
    votes       INTEGER DEFAULT 0,
    poster_url  VARCHAR
);

CREATE TABLE ratings (
    id        INTEGER PRIMARY KEY,
    user_id   INTEGER NOT NULL,
    movie_id  INTEGER NOT NULL REFERENCES movies(id),
    rating    FLOAT NOT NULL
);
