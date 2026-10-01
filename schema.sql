-- Reference DDL, generated from models/database.py by scripts/export_db.py.
-- The app creates these tables itself (scripts/init_db.py).


CREATE TABLE movies (
	id SERIAL NOT NULL, 
	title VARCHAR NOT NULL, 
	genre VARCHAR NOT NULL, 
	year INTEGER NOT NULL, 
	rating FLOAT, 
	votes INTEGER, 
	poster_url VARCHAR, 
	PRIMARY KEY (id), 
	CONSTRAINT movies_rating_range CHECK (rating IS NULL OR (rating >= 0 AND rating <= 5))
)

;


CREATE TABLE ratings (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	movie_id INTEGER NOT NULL, 
	rating FLOAT NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ratings_rating_range CHECK (rating >= 0.5 AND rating <= 5), 
	FOREIGN KEY(movie_id) REFERENCES movies (id)
)

;

CREATE INDEX ix_ratings_movie_id ON ratings (movie_id);
