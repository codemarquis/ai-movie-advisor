# Deploying AI Movie Advisor on AWS EC2

One Ubuntu instance runs Nginx and the Streamlit app (kept alive by Supervisor). PostgreSQL runs on Amazon RDS (recommended) or on the same instance.

```
Internet ──HTTPS──▶ Nginx :443 ──▶ Streamlit 127.0.0.1:8501 ──read-only──▶ PostgreSQL
                    (TLS, rate limit,     (Supervisor,            (ama_app role)
                     security headers)     unprivileged user)
```

## 1. Launch the instance

- Ubuntu Server 22.04 or 24.04 LTS, t3.small or larger
- Security group inbound rules:
  - **22** from **your IP only**
  - **80** and **443** from anywhere
- **Do not** open 8501. Streamlit listens on 127.0.0.1 and is reached only through Nginx.

For RDS: put the database in private subnets, allow **5432 only from the instance's security group**, and use `?sslmode=require` in both database URLs.

## 2. Install

```bash
ssh ubuntu@<instance>
git clone https://github.com/codemarquis/ai-movie-advisor.git
cd ai-movie-advisor
./deployment/setup_ec2.sh                       # add INSTALL_LOCAL_POSTGRES=1 for a single-box setup
```

The script stops on the first error and refuses to run as root. It:
- installs Nginx, Supervisor and a Python virtualenv
- creates `.env` from `.env.example` with `chmod 600`
- installs the Nginx site and the Supervisor program for this checkout's path and user

## 3. Database roles (least privilege)

```bash
psql "postgresql://<master-user>@<host>/moviedb?sslmode=require" \
  -v app_password='<strong-password-1>' -v admin_password='<strong-password-2>' \
  -f deployment/db_roles.sql
```

| Role | Used by | Can do |
|---|---|---|
| `movie_admin` | `ADMIN_DATABASE_URL`: seeding, imports, poster refresh | Create and write tables |
| `ama_app` | `DATABASE_URL`: the web app | `SELECT` only; every transaction read-only |

## 4. Configure and seed

```bash
nano .env
#   DATABASE_URL=postgresql://ama_app:<pw1>@<host>:5432/moviedb?sslmode=require
#   ADMIN_DATABASE_URL=postgresql://movie_admin:<pw2>@<host>:5432/moviedb?sslmode=require
#   TMDB_API_KEY=            # optional

.venv/bin/python scripts/init_db.py             # safe to re-run
sudo supervisorctl restart ai-movie-advisor
```

## 5. Domain and TLS

```bash
sudo sed -i 's/your_domain.com/movies.example.com/' /etc/nginx/sites-available/ai-movie-advisor
sudo nginx -t && sudo systemctl reload nginx
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d movies.example.com
```

Then uncomment the `Strict-Transport-Security` header in the Nginx site and reload.

## Operations

| Task | Command |
|---|---|
| App status | `sudo supervisorctl status ai-movie-advisor` |
| App logs | `tail -f /var/log/supervisor/ai-movie-advisor.err.log` |
| Nginx logs | `tail -f /var/log/nginx/access.log /var/log/nginx/error.log` |
| Update | `git pull && .venv/bin/pip install -r requirements.txt && sudo supervisorctl restart ai-movie-advisor` |
| Refresh posters | `.venv/bin/python scripts/update_posters.py` |
| Backup data | `.venv/bin/python scripts/export_db.py --out ~/backups/$(date +%F)` |

## Scaling out

Run more instances from the same AMI behind an **Application Load Balancer**, with sticky sessions (Streamlit keeps per-session state over a WebSocket). They all share the RDS database. Since the app only reads, an RDS read replica can take the `DATABASE_URL` traffic.
