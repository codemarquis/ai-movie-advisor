# Movie Recommender System

A Streamlit-based movie recommendation system with TMDB integration, collaborative filtering, and interactive UI.

## Features
- Real-time movie data from TMDB API
- Interactive genre and mood-based filtering
- Personalized movie recommendations
- Watchlist functionality
- Responsive movie tile display

## Local Development Setup

### Prerequisites
- Python 3.11+
- PostgreSQL
- TMDB API Key

### Installation Steps

1. Clone the repository:
```bash
git clone <your-repository-url>
cd movie-recommender
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Required packages:
- streamlit
- pandas
- plotly
- psycopg2-binary
- scikit-learn
- sqlalchemy
- tmdbv3api

3. Set up environment variables:
Create a `.env` file with:
```
DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<database>
TMDB_API_KEY=your_tmdb_api_key
```

4. Initialize the database:
```bash
python scripts/init_db.py
```

5. Run the application:
```bash
streamlit run app.py
```

## Database Schema

The application uses PostgreSQL with the following schema:

```sql
-- Movies table
CREATE TABLE movies (
    id INTEGER PRIMARY KEY,
    title VARCHAR NOT NULL,
    genre VARCHAR NOT NULL,
    year INTEGER NOT NULL,
    rating FLOAT,
    votes INTEGER DEFAULT 0,
    poster_url VARCHAR
);

-- Ratings table
CREATE TABLE ratings (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    movie_id INTEGER NOT NULL REFERENCES movies(id),
    rating FLOAT NOT NULL
);
```

## AWS EC2 Deployment

### 1. Launch EC2 Instance
- Use Ubuntu Server 22.04 LTS
- t2.micro for testing, t2.small/medium for production
- Configure Security Group:
  - Allow SSH (port 22)
  - Allow HTTP (port 80)
  - Allow HTTPS (port 443)
  - Allow Custom TCP (port 5000) for Streamlit

### 2. Install Dependencies
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-dev postgresql postgresql-contrib nginx -y
```

### 3. Set Up PostgreSQL
```bash
sudo -u postgres psql
CREATE DATABASE moviedb;
CREATE USER movieuser WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE moviedb TO movieuser;
```

### 4. Configure Nginx as Load Balancer
```nginx
upstream streamlit {
    server localhost:5000;
    # Add more servers here for load balancing
}

server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://streamlit;
        proxy_http_version 1.1;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
```

### 5. Set Up SSL (Optional)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your_domain.com
```

### 6. Run Application with Supervisor
Create `/etc/supervisor/conf.d/streamlit.conf`:
```ini
[program:streamlit]
directory=/path/to/app
command=streamlit run app.py --server.port 5000 --server.address 0.0.0.0
autostart=true
autorestart=true
stderr_logfile=/var/log/streamlit/streamlit.err.log
stdout_logfile=/var/log/streamlit/streamlit.out.log
```

## File Structure
```
.
├── .streamlit/
│   └── config.toml
├── components/
│   ├── movie_details.py
│   ├── movie_tiles.py
│   └── sidebar.py
├── data/
│   └── mock_movies.py
├── models/
│   ├── database.py
│   └── recommender.py
├── scripts/
│   └── init_db.py
├── services/
│   └── tmdb_service.py
├── utils/
│   └── data_processing.py
└── app.py
```

## Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `TMDB_API_KEY`: TMDB API key for fetching movie data
- `PGHOST`: PostgreSQL host
- `PGPORT`: PostgreSQL port
- `PGUSER`: PostgreSQL username
- `PGPASSWORD`: PostgreSQL password
- `PGDATABASE`: PostgreSQL database name

## Scaling Considerations
1. Use connection pooling for database connections
2. Implement caching for TMDB API responses
3. Set up multiple EC2 instances behind the load balancer
4. Use Amazon RDS for managed PostgreSQL
5. Implement Redis for session management

## Maintenance
- Regular database backups
- Monitor application logs
- Update dependencies regularly
- Check TMDB API quota usage
