# AudiobookSmith Webhook Integration - Deployment Guide

## 🎯 Deployment to Production Server

This guide will help you deploy the webhook integration to your production server (websolutionsserver.net).

## 📋 Prerequisites

- SSH access to websolutionsserver.net
- Python 3.11 installed
- Flask installed (`pip3 install flask`)
- Sufficient disk space for file uploads
- Port 5001 available (or choose another port)

## 🚀 Step-by-Step Deployment

### Step 1: Copy Files to Production Server

```bash
# From your local machine or this sandbox
scp /home/ubuntu/audiobook_webhook_server.py user@websolutionsserver.net:/home/user/
scp /home/ubuntu/audiobook_processor.py user@websolutionsserver.net:/home/user/
```

### Step 2: Set Up Directory Structure

```bash
# SSH into your server
ssh user@websolutionsserver.net

# Create necessary directories
mkdir -p /home/user/audiobook_uploads
mkdir -p /home/user/logs

# Set permissions
chmod 755 /home/user/audiobook_uploads
chmod +x /home/user/audiobook_webhook_server.py
chmod +x /home/user/audiobook_processor.py
```

### Step 3: Install Dependencies

```bash
# Install Flask if not already installed
pip3 install flask

# Verify Python version
python3.11 --version
```

### Step 4: Configure the Server

Edit `audiobook_webhook_server.py` to update paths if needed:

```python
# Configuration
UPLOAD_FOLDER = "/home/user/audiobook_uploads"  # Update path
PROCESSOR_SCRIPT = "/home/user/audiobook_processor.py"  # Update path
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
```

### Step 5: Test the Server

```bash
# Run the server in foreground to test
python3.11 /home/user/audiobook_webhook_server.py

# In another terminal, test the health endpoint
curl http://localhost:5001/health
```

### Step 6: Set Up as a Service (Recommended)

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/audiobook-webhook.service
```

Add the following content:

```ini
[Unit]
Description=AudiobookSmith Webhook Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/user
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3.11 /home/user/audiobook_webhook_server.py
Restart=always
RestartSec=10
StandardOutput=append:/home/user/logs/webhook_server.log
StandardError=append:/home/user/logs/webhook_server_error.log

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable audiobook-webhook
sudo systemctl start audiobook-webhook
sudo systemctl status audiobook-webhook
```

### Step 7: Configure Nginx Reverse Proxy

Add this to your Nginx configuration:

```nginx
# /etc/nginx/sites-available/audiobooksmith

server {
    listen 80;
    server_name webhook.audiobooksmith.com;  # Or your chosen subdomain
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name webhook.audiobooksmith.com;
    
    # SSL certificates (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/webhook.audiobooksmith.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/webhook.audiobooksmith.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Increase upload size limit
    client_max_body_size 100M;
    
    # Proxy to Flask app
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long uploads
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

Enable the site and reload Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/audiobooksmith /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 8: Set Up SSL Certificate

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d webhook.audiobooksmith.com
```

### Step 9: Update Frontend Code

Update the webhook URL in your frontend code:

```javascript
// Before (sandbox URL)
const WEBHOOK_URL = "https://5001-ivhxzp207okmv86v56xhi-424900e9.manusvm.computer/webhook/audiobook-process";

// After (production URL)
const WEBHOOK_URL = "https://webhook.audiobooksmith.com/webhook/audiobook-process";
```

### Step 10: Test Production Deployment

```bash
# Test health endpoint
curl https://webhook.audiobooksmith.com/health

# Test file upload
curl -X POST "https://webhook.audiobooksmith.com/webhook/audiobook-process" \
  -F "email=test@example.com" \
  -F "bookTitle=Test Book" \
  -F "plan=free" \
  -F "bookFile=@/path/to/test.pdf"
```

## 🔒 Security Enhancements

### 1. Add API Key Authentication

Update `audiobook_webhook_server.py`:

```python
import os

API_KEY = os.environ.get('WEBHOOK_API_KEY', 'your-secret-key-here')

@app.before_request
def check_api_key():
    if request.path != '/health':
        api_key = request.headers.get('X-API-Key')
        if api_key != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
```

Update frontend code:

```javascript
const response = await fetch(WEBHOOK_URL, {
  method: 'POST',
  headers: {
    'X-API-Key': 'your-secret-key-here'
  },
  body: formData
});
```

### 2. Add Rate Limiting

```bash
pip3 install flask-limiter

# In audiobook_webhook_server.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

@app.route('/webhook/audiobook-process', methods=['POST'])
@limiter.limit("10 per minute")
def process_audiobook():
    # ... existing code
```

### 3. Add CORS Headers

```python
from flask_cors import CORS

# Allow only your domain
CORS(app, origins=["https://audiobooksmith.com"])
```

## 📊 Monitoring

### 1. Set Up Log Rotation

```bash
sudo nano /etc/logrotate.d/audiobook-webhook
```

```
/home/user/logs/webhook_server*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 ubuntu ubuntu
    sharedscripts
    postrotate
        systemctl reload audiobook-webhook > /dev/null 2>&1 || true
    endscript
}
```

### 2. Monitor Server Status

```bash
# Check service status
sudo systemctl status audiobook-webhook

# View logs
tail -f /home/user/logs/webhook_server.log

# Check disk space
df -h /home/user/audiobook_uploads

# Monitor file uploads
watch -n 5 'ls -lh /home/user/audiobook_uploads | tail -10'
```

### 3. Set Up Alerts

Create a monitoring script:

```bash
#!/bin/bash
# /home/user/monitor_webhook.sh

# Check if service is running
if ! systemctl is-active --quiet audiobook-webhook; then
    echo "Webhook server is down!" | mail -s "ALERT: Webhook Down" admin@audiobooksmith.com
    sudo systemctl start audiobook-webhook
fi

# Check disk space
DISK_USAGE=$(df -h /home/user/audiobook_uploads | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "Disk usage is at ${DISK_USAGE}%" | mail -s "ALERT: High Disk Usage" admin@audiobooksmith.com
fi
```

Add to crontab:

```bash
crontab -e

# Add this line to run every 5 minutes
*/5 * * * * /home/user/monitor_webhook.sh
```

## 🧹 Maintenance

### Clean Up Old Files

```bash
# Delete files older than 7 days
find /home/user/audiobook_uploads -type f -mtime +7 -delete

# Add to crontab for automatic cleanup
crontab -e

# Run daily at 2 AM
0 2 * * * find /home/user/audiobook_uploads -type f -mtime +7 -delete
```

### Backup Configuration

```bash
# Backup webhook server code
cp /home/user/audiobook_webhook_server.py /home/user/backups/audiobook_webhook_server_$(date +%Y%m%d).py

# Backup processor code
cp /home/user/audiobook_processor.py /home/user/backups/audiobook_processor_$(date +%Y%m%d).py
```

## 🔄 Updates and Rollback

### Update the Server

```bash
# Stop the service
sudo systemctl stop audiobook-webhook

# Backup current version
cp /home/user/audiobook_webhook_server.py /home/user/backups/

# Deploy new version
scp new_audiobook_webhook_server.py user@websolutionsserver.net:/home/user/audiobook_webhook_server.py

# Start the service
sudo systemctl start audiobook-webhook

# Check status
sudo systemctl status audiobook-webhook
```

### Rollback

```bash
# Stop the service
sudo systemctl stop audiobook-webhook

# Restore backup
cp /home/user/backups/audiobook_webhook_server_YYYYMMDD.py /home/user/audiobook_webhook_server.py

# Start the service
sudo systemctl start audiobook-webhook
```

## 📈 Performance Optimization

### 1. Use Gunicorn for Production

```bash
pip3 install gunicorn

# Update systemd service
ExecStart=/usr/bin/gunicorn -w 4 -b 127.0.0.1:5001 --timeout 300 audiobook_webhook_server:app
```

### 2. Add Redis Queue for Long Processing

```bash
pip3 install redis rq

# Create worker script
# /home/user/audiobook_worker.py
from rq import Worker, Queue, Connection
import redis

redis_conn = redis.Redis()

if __name__ == '__main__':
    with Connection(redis_conn):
        worker = Worker(['audiobook'])
        worker.work()
```

## ✅ Deployment Checklist

- [ ] Files copied to production server
- [ ] Directory structure created
- [ ] Dependencies installed
- [ ] Configuration updated
- [ ] Service file created
- [ ] Service enabled and started
- [ ] Nginx reverse proxy configured
- [ ] SSL certificate obtained
- [ ] Frontend code updated
- [ ] Production deployment tested
- [ ] API key authentication added
- [ ] Rate limiting configured
- [ ] CORS headers set
- [ ] Log rotation configured
- [ ] Monitoring set up
- [ ] Backup strategy implemented
- [ ] Maintenance scripts created

## 🎉 Post-Deployment

After successful deployment:

1. **Test thoroughly** with real book files
2. **Monitor logs** for the first few days
3. **Check disk space** regularly
4. **Review error rates** and optimize
5. **Document any custom configurations**
6. **Train team** on monitoring and troubleshooting

## 📞 Support

If you encounter issues:

1. Check service status: `sudo systemctl status audiobook-webhook`
2. Review logs: `tail -f /home/user/logs/webhook_server.log`
3. Test health endpoint: `curl https://webhook.audiobooksmith.com/health`
4. Verify Nginx configuration: `sudo nginx -t`
5. Check disk space: `df -h`

---

**Deployment Status**: Ready for Production  
**Estimated Deployment Time**: 1-2 hours  
**Difficulty**: Intermediate
