#!/usr/bin/env bash
# Provision an Ubuntu 22.04 / 24.04 host for AI Movie Advisor.
# Run from a clone of the repository, as the (non-root) user that will run the app:
#     ./deployment/setup_ec2.sh
# Set INSTALL_LOCAL_POSTGRES=1 to also install PostgreSQL on this machine
# (otherwise point DATABASE_URL at Amazon RDS or another server).
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP_USER="$(id -un)"
if [ "$APP_USER" = "root" ]; then
  echo "Run this as the unprivileged user that will own the app, not root." >&2
  exit 1
fi

packages=(python3-venv python3-dev nginx supervisor)
if [ "${INSTALL_LOCAL_POSTGRES:-0}" = "1" ]; then
  packages+=(postgresql postgresql-contrib)
fi
sudo apt-get update
sudo apt-get install -y "${packages[@]}"

# Python dependencies in a virtualenv (system pip is blocked on Ubuntu 24.04).
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

# Secrets live in .env, readable by the app user only.
if [ ! -f "$APP_DIR/.env" ]; then
  cp "$APP_DIR/.env.example" "$APP_DIR/.env"
fi
chmod 600 "$APP_DIR/.env"

# Nginx reverse proxy.
sudo cp "$APP_DIR/deployment/nginx.conf" /etc/nginx/sites-available/ai-movie-advisor
sudo ln -sf /etc/nginx/sites-available/ai-movie-advisor /etc/nginx/sites-enabled/ai-movie-advisor
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

# Supervisor keeps Streamlit running as $APP_USER.
sed -e "s#__APP_DIR__#$APP_DIR#g" -e "s#__APP_USER__#$APP_USER#g" \
  "$APP_DIR/deployment/supervisor.conf" | sudo tee /etc/supervisor/conf.d/ai-movie-advisor.conf >/dev/null
sudo supervisorctl reread
sudo supervisorctl update

cat <<NEXT
Setup complete. Next:
  1. Edit $APP_DIR/.env (DATABASE_URL, ADMIN_DATABASE_URL, optional TMDB_API_KEY)
  2. Create least-privilege roles:  psql ... -f deployment/db_roles.sql
  3. Seed the database:            $APP_DIR/.venv/bin/python scripts/init_db.py
  4. Restart the app:              sudo supervisorctl restart ai-movie-advisor
  5. Set server_name in /etc/nginx/sites-available/ai-movie-advisor, then:
                                   sudo certbot --nginx -d your_domain.com
NEXT
