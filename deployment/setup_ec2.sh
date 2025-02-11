#!/bin/bash

# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required system dependencies
sudo apt install -y \
    python3-pip \
    python3-dev \
    postgresql \
    postgresql-contrib \
    nginx \
    supervisor

# Create directory for the application
sudo mkdir -p /var/log/supervisor
sudo mkdir -p /var/www/movie-recommender
sudo chown -R ubuntu:ubuntu /var/www/movie-recommender

# Install Python packages
pip3 install -r requirements.txt

# Copy Nginx configuration
sudo cp deployment/nginx.conf /etc/nginx/sites-available/movie-recommender
sudo ln -s /etc/nginx/sites-available/movie-recommender /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Copy Supervisor configuration
sudo cp deployment/supervisor.conf /etc/supervisor/conf.d/movie-recommender.conf

# Restart services
sudo systemctl restart nginx
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart all

echo "Setup complete! Don't forget to:"
echo "1. Configure your environment variables"
echo "2. Initialize the database"
echo "3. Update the Nginx configuration with your domain name"
