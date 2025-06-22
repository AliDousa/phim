# Production Deployment Guide

This guide covers deploying the Public Health Intelligence Platform backend to production environments.

## Quick Start (Docker)

### Prerequisites
- Docker and Docker Compose
- 2GB+ RAM
- 10GB+ disk space

### Deploy with Docker
```bash
# Clone repository
git clone <repository-url>
cd backend

# Set environment variables
export SECRET_KEY="your-super-secret-key-here"

# Build and start
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f phip-backend
```

The API will be available at `http://localhost:5000`

## Manual Deployment

### 1. Server Requirements

**Minimum:**
- Python 3.8+
- 2GB RAM
- 5GB disk space
- Ubuntu 20.04+ / CentOS 8+ / similar

**Recommended:**
- Python 3.11+
- 4GB RAM
- 20GB disk space
- Load balancer (nginx/Apache)
- SSL certificate

### 2. System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv git nginx -y

# Create application user
sudo adduser phip --disabled-password
sudo usermod -aG www-data phip
```

### 3. Application Setup

```bash
# Switch to app user
sudo su - phip

# Clone repository
git clone <repository-url> /home/phip/app
cd /home/phip/app/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn  # Production WSGI server
```

### 4. Environment Configuration

Create `/home/phip/app/backend/.env`:
```bash
# Security
SECRET_KEY=your-super-secret-key-change-this
FLASK_ENV=production

# Database (use PostgreSQL in production)
DATABASE_URL=postgresql://user:password@localhost/phip

# Optional: Redis for caching
REDIS_URL=redis://localhost:6379/0

# File uploads
MAX_CONTENT_LENGTH=104857600  # 100MB
```

### 5. Database Setup (PostgreSQL)

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Create database and user
sudo -u postgres createuser phip
sudo -u postgres createdb phip -O phip
sudo -u postgres psql -c "ALTER USER phip PASSWORD 'secure-password';"

# Update .env with connection string
DATABASE_URL=postgresql://phip:secure-password@localhost/phip
```

### 6. Application Service

Create `/etc/systemd/system/phip.service`:
```ini
[Unit]
Description=PHIP Backend API
After=network.target

[Service]
Type=notify
User=phip
Group=www-data
WorkingDirectory=/home/phip/app/backend
Environment=PATH=/home/phip/app/backend/venv/bin
EnvironmentFile=/home/phip/app/backend/.env
ExecStart=/home/phip/app/backend/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 4 --timeout 300 --keep-alive 2 --max-requests 1000 --max-requests-jitter 100 src.main:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable phip
sudo systemctl start phip
sudo systemctl status phip
```

### 7. Reverse Proxy (Nginx)

Create `/etc/nginx/sites-available/phip`:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # Static files (if serving frontend)
    location / {
        root /home/phip/app/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    # File upload size
    client_max_body_size 100M;
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/phip /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## SSL Certificate

### Using Let's Encrypt (Recommended)
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Monitoring and Logging

### 1. Application Logs
```bash
# Service logs
sudo journalctl -u phip -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 2. Health Monitoring
```bash
# Create health check script
cat > /home/phip/health_check.sh << 'EOF'
#!/bin/bash
if curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "API is healthy"
    exit 0
else
    echo "API is down"
    exit 1
fi
EOF

chmod +x /home/phip/health_check.sh

# Add to crontab for monitoring
*/5 * * * * /home/phip/health_check.sh || systemctl restart phip
```

### 3. Log Rotation
Create `/etc/logrotate.d/phip`:
```
/home/phip/app/backend/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 phip phip
    postrotate
        systemctl reload phip
    endscript
}
```

## Performance Optimization

### 1. Database Optimization
```sql
-- Create indexes for better performance
CREATE INDEX idx_datasets_user_id ON datasets(user_id);
CREATE INDEX idx_simulations_user_id ON simulations(user_id);
CREATE INDEX idx_data_points_dataset_timestamp ON data_points(dataset_id, timestamp);
CREATE INDEX idx_forecasts_simulation_target ON forecasts(simulation_id, target_date);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM simulations WHERE user_id = 1;
```

### 2. Application Tuning
```bash
# Gunicorn configuration
# Adjust workers: 2 * CPU_CORES + 1
--workers 4

# Memory limits
--max-requests 1000
--max-requests-jitter 100

# Timeouts for long simulations
--timeout 300
```

### 3. Caching (Redis)
```bash
# Install Redis
sudo apt install redis-server -y

# Configure in application
export REDIS_URL=redis://localhost:6379/0
```

## Security Best Practices

### 1. Firewall Configuration
```bash
# UFW setup
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 2. Application Security
- Use strong `SECRET_KEY` (64+ characters)
- Enable rate limiting
- Validate all inputs
- Use HTTPS only
- Regular security updates

### 3. Database Security
```bash
# PostgreSQL security
sudo nano /etc/postgresql/*/main/postgresql.conf
# Set: listen_addresses = 'localhost'

sudo nano /etc/postgresql/*/main/pg_hba.conf
# Use md5 authentication
```

## Backup Strategy

### 1. Database Backup
```bash
# Create backup script
cat > /home/phip/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/phip/backups"
mkdir -p $BACKUP_DIR

# Database backup
pg_dump phip > $BACKUP_DIR/db_$DATE.sql
gzip $BACKUP_DIR/db_$DATE.sql

# Files backup
tar -czf $BACKUP_DIR/files_$DATE.tar.gz /home/phip/app/backend/data

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /home/phip/backup.sh

# Schedule daily backups
0 2 * * * /home/phip/backup.sh
```

### 2. Disaster Recovery
- Store backups off-site
- Test restore procedures
- Document recovery steps
- Monitor backup success

## Scaling

### 1. Horizontal Scaling
- Use load balancer (nginx/HAProxy)
- Shared database (PostgreSQL cluster)
- Shared file storage (NFS/S3)
- Container orchestration (Kubernetes)

### 2. Vertical Scaling
- Increase server resources
- Optimize database queries
- Add caching layers
- Use CDN for static files

## Troubleshooting

### Common Issues

**1. Service Won't Start**
```bash
# Check logs
sudo journalctl -u phip -n 50

# Check dependencies
source /home/phip/app/backend/venv/bin/activate
python -c "import src.main"

# Check permissions
ls -la /home/phip/app/backend/
```

**2. Database Connection Issues**
```bash
# Test connection
sudo -u phip psql -h localhost -U phip -d phip

# Check service status
sudo systemctl status postgresql
```

**3. High Memory Usage**
```bash
# Monitor processes
htop
ps aux | grep gunicorn

# Restart service
sudo systemctl restart phip
```

**4. Slow API Responses**
```bash
# Check database queries
sudo -u postgres psql phip
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC LIMIT 10;

# Monitor system resources
iostat 1
vmstat 1
```

### Performance Monitoring
```bash
# Install monitoring tools
pip install flask-monitoring-dashboard

# Monitor with htop
sudo apt install htop iotop -y

# Database monitoring
sudo apt install postgresql-contrib -y
# Enable pg_stat_statements in postgresql.conf
```

## Maintenance

### Regular Tasks
- [ ] Update dependencies monthly
- [ ] Review security logs weekly
- [ ] Database maintenance quarterly
- [ ] Backup testing monthly
- [ ] Performance review quarterly

### Update Procedure
```bash
# 1. Backup current version
/home/phip/backup.sh

# 2. Update code
cd /home/phip/app
git pull origin main

# 3. Update dependencies
source backend/venv/bin/activate
pip install -r backend/requirements.txt

# 4. Run migrations (if any)
python backend/migrate.py

# 5. Restart service
sudo systemctl restart phip

# 6. Verify health
curl http://localhost:5000/api/health
```

## Support

For production support:
1. Check logs first
2. Review this deployment guide
3. Consult the main README.md
4. Create detailed issue report

---

**Remember**: Always test deployments in a staging environment first!