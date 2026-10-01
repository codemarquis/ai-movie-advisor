# Deployment Instructions

## Local Development
1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Set up environment variables in `.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/moviedb
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

## EC2 Deployment

### 1. Launch EC2 Instance
- Use Ubuntu Server 22.04 LTS
- t2.small or larger recommended
- Configure security group to allow ports 22, 80, 443, and 5000

### 2. Initial Setup
1. SSH into your instance
2. Clone the repository
3. Run the setup script:
```bash
chmod +x deployment/setup_ec2.sh
./deployment/setup_ec2.sh
```

### 3. Configure Environment
1. Create `.env` file with your environment variables
2. Update `deployment/nginx.conf` with your domain name
3. Initialize the database:
```bash
python scripts/init_db.py
```

### 4. Load Balancer Setup
The Nginx configuration in `deployment/nginx.conf` includes load balancer settings.
To add more servers:

1. Update the upstream block in nginx.conf:
```nginx
upstream streamlit_app {
    server 127.0.0.1:5000;
    server 127.0.0.1:5001;  # Add more servers as needed
}
```

2. Update Supervisor configuration to run multiple Streamlit instances on different ports.

### 5. SSL Configuration (Optional)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your_domain.com
```

### 6. Monitoring
- Check application logs:
```bash
tail -f /var/log/supervisor/streamlit.out.log
```
- Monitor Nginx access:
```bash
tail -f /var/log/nginx/access.log
```
