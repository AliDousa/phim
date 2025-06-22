# Production Deployment Guide
# Public Health Intelligence Platform Backend

This guide provides comprehensive instructions for deploying the PHIP Backend to production environments with full monitoring, security, and high availability.

## 🚀 Quick Start

For immediate production deployment:

```bash
# 1. Clone and setup
git clone <repository-url>
cd phip-backend

# 2. Configure environment
cp .env.production .env.local
# Edit .env.local with your production values

# 3. Deploy
./scripts/deploy.sh
```

## 📋 Prerequisites

### System Requirements

**Minimum Production Requirements:**
- **CPU:** 4 cores
- **RAM:** 8GB
- **Storage:** 100GB SSD
- **OS:** Ubuntu 20.04+ / CentOS 8+ / RHEL 8+

**Recommended Production Setup:**
- **CPU:** 8+ cores
- **RAM:** 16GB+
- **Storage:** 500GB+ SSD with backup
- **Load Balancer:** Nginx/HAProxy
- **SSL Certificate:** Let's Encrypt or commercial

### Software Dependencies

```bash
# Docker & Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Optional: System monitoring tools
sudo apt install htop iotop ncdu
```

## 🔧 Configuration

### 1. Environment Configuration

**Required Environment Variables:**

```bash
# Security (CRITICAL - Change these!)
SECRET_KEY="your-super-secure-secret-key-min-32-chars"
POSTGRES_PASSWORD="your-secure-database-password"
REDIS_PASSWORD="your-secure-redis-password"

# Database
DATABASE_URL="postgresql://phip_user:password@postgres:5432/phip_db"

# External URLs
DOMAIN="yourdomain.com"
CORS_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
```

**Optional but Recommended:**

```bash
# Monitoring
SENTRY_DSN="your-sentry-dsn"
GRAFANA_PASSWORD="your-grafana-password"

# Email (for notifications)
MAIL_SERVER="smtp.gmail.com"
MAIL_USERNAME="your-email@gmail.com"
MAIL_PASSWORD="your-app-password"

# AWS S3 (for file storage)
AWS_ACCESS_KEY_ID="your-aws-key"
AWS_SECRET_ACCESS_KEY="your-aws-secret"
AWS_S3_BUCKET="your-bucket"
```

### 2. SSL/TLS Setup

**Option A: Let's Encrypt (Recommended)**

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal cron job
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

**Option B: Custom Certificate**

```bash
# Place your certificates
sudo mkdir -p /etc/nginx/ssl
sudo cp your-cert.pem /etc/nginx/ssl/cert.pem
sudo cp your-key.pem /etc/nginx/ssl/private.key
sudo chmod 600 /etc/nginx/ssl/private.key
```

### 3. Firewall Configuration

```bash
# UFW setup
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## 🚀 Deployment Methods

### Method 1: Automated Deployment (Recommended)

```bash
# Full automated deployment
./scripts/deploy.sh

# With custom environment
DEPLOY_ENV=production ./scripts/deploy.sh

# Deploy specific version
VERSION=v1.2.3 ./scripts/deploy.sh
```

### Method 2: Manual Docker Compose

```bash
# Start infrastructure services
docker-compose -f docker-compose.production.yml up -d postgres redis

# Wait for services to be ready
sleep 30

# Start application services
docker-compose -f docker-compose.production.yml up -d phip-backend celery-worker

# Start monitoring and proxy
docker-compose -f docker-compose.production.yml up -d nginx prometheus grafana
```

### Method 3: Kubernetes Deployment

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/ingress.yaml
```

## 📊 Monitoring & Observability

### Monitoring Stack

The production deployment includes a comprehensive monitoring stack:

| Service | URL | Purpose |
|---------|-----|---------|
| **Grafana** | `https://yourdomain.com:3000` | Dashboards and visualization |
| **Prometheus** | `https://yourdomain.com:9090` | Metrics collection |
| **Flower** | `https://yourdomain.com:5555` | Celery task monitoring |
| **Logs** | `/app/logs/` | Application logs |

### Key Metrics to Monitor

**Application Metrics:**
- Request rate and response time
- Error rate and status codes
- Active users and sessions
- Simulation success/failure rates
- Queue length and processing time

**Infrastructure Metrics:**
- CPU, memory, and disk usage
- Database connections and query performance
- Redis memory usage and hit rate
- SSL certificate expiry

**Business Metrics:**
- Daily active users
- Datasets processed per day
- Simulation completion rates
- API usage patterns

### Alerting

Alerts are configured for:

- 🔴 **Critical:** Service down, database unreachable
- 🟡 **Warning:** High response time, resource usage
- 🔵 **Info:** Security events, business anomalies

Configure Slack/email notifications:

```bash
# Add to docker-compose.production.yml
environment:
  SLACK_WEBHOOK_URL: "your-slack-webhook"
  ALERT_EMAIL: "admin@yourdomain.com"
```

## 🔒 Security Considerations

### Application Security

**✅ Implemented Features:**
- JWT authentication with secure tokens
- Rate limiting on all endpoints
- Input validation and sanitization
- SQL injection prevention
- XSS protection headers
- CSRF protection
- File upload security scanning

**🔧 Additional Recommendations:**

```bash
# 1. Enable fail2ban for SSH protection
sudo apt install fail2ban
sudo systemctl enable fail2ban

# 2. Regular security updates
sudo apt update && sudo apt upgrade -y

# 3. Database access restrictions
# Edit postgresql.conf:
listen_addresses = 'localhost'

# 4. Redis password protection
# Already configured in docker-compose
```

### Network Security

```bash
# 1. Restrict Docker network access
# Edit /etc/docker/daemon.json
{
  "icc": false,
  "userland-proxy": false
}

# 2. Use Docker secrets for passwords
echo "your-secret" | docker secret create db_password -

# 3. Regular vulnerability scanning
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image your-image:tag
```

## 🔄 Backup & Recovery

### Automated Backups

Backups are automatically created:

- **Database:** Daily at 2 AM UTC
- **Application Data:** Daily 
- **Uploaded Files:** Daily
- **Retention:** 30 days

### Manual Backup

```bash
# Create immediate backup
./scripts/deploy.sh backup

# Restore from backup
./scripts/deploy.sh restore

# Restore specific backup
BACKUP_VERSION=20240101_120000 ./scripts/deploy.sh restore
```

### Disaster Recovery

**RTO (Recovery Time Objective):** 15 minutes  
**RPO (Recovery Point Objective):** 1 hour

**Recovery Steps:**

1. **Infrastructure Failure:**
   ```bash
   # Restore from infrastructure as code
   ./scripts/deploy.sh --force-rebuild
   ```

2. **Data Corruption:**
   ```bash
   # Restore from latest backup
   ./scripts/deploy.sh restore
   ```

3. **Application Issues:**
   ```bash
   # Rollback to previous version
   ./scripts/rollback.sh
   ```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

The included CI/CD pipeline provides:

- **Continuous Integration:**
  - Code quality checks (Black, Flake8)
  - Security scanning (Bandit, Safety)
  - Unit and integration tests
  - Coverage reporting

- **Continuous Deployment:**
  - Automated builds on push
  - Staging deployment on develop branch
  - Production deployment on tags
  - Rollback capabilities

### Manual Deployment

```bash
# Create and push a release tag
git tag -a v1.2.3 -m "Release version 1.2.3"
git push origin v1.2.3

# The CI/CD pipeline will automatically:
# 1. Run tests
# 2. Build Docker images
# 3. Deploy to production
# 4. Run health checks
# 5. Create GitHub release
```

## 🚨 Troubleshooting

### Common Issues

**1. Service Won't Start**
```bash
# Check logs
docker-compose -f docker-compose.production.yml logs phip-backend

# Check system resources
df -h
free -m
```

**2. Database Connection Issues**
```bash
# Test database connectivity
docker-compose -f docker-compose.production.yml exec postgres \
  psql -U phip_user -d phip_db -c "SELECT 1;"

# Check PostgreSQL logs
docker-compose -f docker-compose.production.yml logs postgres
```

**3. High Memory Usage**
```bash
# Check container resource usage
docker stats

# Scale down workers if needed
docker-compose -f docker-compose.production.yml up -d --scale celery-worker=2
```

**4. SSL Certificate Issues**
```bash
# Check certificate validity
openssl x509 -in /etc/nginx/ssl/cert.pem -text -noout

# Test SSL configuration
sudo nginx -t
```

### Performance Optimization

**Database Optimization:**
```sql
-- Check slow queries
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC LIMIT 10;

-- Create missing indexes
CREATE INDEX CONCURRENTLY idx_missing_index ON table_name(column_name);
```

**Application Optimization:**
```bash
# Increase worker processes
export GUNICORN_WORKERS=8
docker-compose -f docker-compose.production.yml up -d phip-backend

# Scale Celery workers
docker-compose -f docker-compose.production.yml up -d --scale celery-worker=4
```

## 📞 Support & Maintenance

### Regular Maintenance Tasks

**Daily:**
- [ ] Check application health dashboard
- [ ] Review error logs for anomalies
- [ ] Verify backup completion

**Weekly:**
- [ ] Update Docker images
- [ ] Review security logs
- [ ] Check disk space usage
- [ ] Analyze performance metrics

**Monthly:**
- [ ] Update system packages
- [ ] Review and rotate logs
- [ ] Test backup restoration
- [ ] Security vulnerability scan
- [ ] Performance review and optimization

### Getting Help

**For Production Issues:**

1. **Check Status Page:** `https://yourdomain.com/health`
2. **Review Monitoring:** Grafana dashboards
3. **Check Logs:** `/app/logs/` directory
4. **Emergency Contacts:** Configure in alerting

**For Development Issues:**

1. Check the main [README.md](README.md)
2. Review API documentation
3. Check GitHub issues
4. Contact development team

### Scaling Guidelines

**Vertical Scaling (Scale Up):**
```bash
# Increase resources in docker-compose.yml
services:
  phip-backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
```

**Horizontal Scaling (Scale Out):**
```bash
# Add more workers
docker-compose -f docker-compose.production.yml up -d --scale celery-worker=6

# Load balancer configuration needed for multiple backend instances
```

---

## 🏁 Conclusion

This production deployment provides:

- ✅ **High Availability:** Multi-container architecture with health checks
- ✅ **Security:** Comprehensive security measures and monitoring
- ✅ **Scalability:** Horizontal and vertical scaling capabilities
- ✅ **Monitoring:** Full observability stack with alerting
- ✅ **Automation:** CI/CD pipeline with automated testing and deployment
- ✅ **Backup & Recovery:** Automated backups with disaster recovery procedures

**Next Steps:**
1. Customize configuration for your environment
2. Set up monitoring alerts
3. Configure backup destinations
4. Test disaster recovery procedures
5. Train your operations team

For additional support, refer to the [main documentation](README.md) or contact the development team.

---

**Version:** 1.0.0  
**Last Updated:** January 2024  
**Tested On:** Ubuntu 22.04, Docker 24.0+, Docker Compose 2.20+