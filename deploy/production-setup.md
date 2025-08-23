# Comet Hunter Production Setup Guide

## Prerequisites
- Linux server (Ubuntu 20.04+ recommended)
- Docker & Docker Compose installed
- Nginx installed
- Domain: comethunter.skywu.me pointed to your server IP

## Complete Deployment Steps

### 1. Connect to your Ubuntu server
```bash
ssh root@your-server-ip
```

### 2. Install Node.js and npm
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
node --version
npm --version
```

### 3. Install Docker & Docker Compose
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
#   Try following if `sudo usermod ... USER` fails
#   sudo groupadd docker
#   sudo usermod -aG docker $USER
#   newgrp docker

# Install Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin
```

### 4. Install Nginx
```bash
sudo apt update && sudo apt install nginx
```

### 5. Clone and setup project
```bash
# Clone your repository
git clone https://github.com/SkyWuZJU/CometInvitationHunter comet-hunter
cd comet-hunter

# Configure environment
mkdir -p config                # Create config directory if it doesn't exist
nano config/production.env     # Add your API keys

# Build frontend
cd frontend
npm install
npm run build
cd ..

# Create nginx site configuration (serves built files directly)
sudo tee /etc/nginx/sites-available/comethunter > /dev/null << 'EOF'
server {
    listen 80;
    server_name comethunter.skywu.me;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name comethunter.skywu.me;

    ssl_certificate /etc/letsencrypt/live/comethunter.skywu.me/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/comethunter.skywu.me/privkey.pem;

    root /home/admin/comet-hunter/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /assets/ {
        root /home/admin/comet-hunter/frontend/dist;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable the site and remove default to avoid conflicts
sudo ln -sf /etc/nginx/sites-available/comethunter /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

### 6. Deploy
```bash
# Start backend only (frontend is served directly by nginx)
docker-compose build backend
docker-compose up -d backend

# Verify deployment
docker-compose ps
curl https://comethunter.skywu.me/api/health
```

### 7. Setup SSL (after DNS points to server)
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d comethunter.skywu.me
# Select option 2 to redirect HTTP to HTTPS when prompted
```

### 8. Verify deployment
```bash
# Test API endpoint
curl https://comethunter.skywu.me/api/health

# Test frontend
curl -I https://comethunter.skywu.me/

# Check browser at https://comethunter.skywu.me/
```

## Manual Steps (if needed)

### Install Docker
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### Install Nginx
```bash
sudo apt update && sudo apt install nginx
```

### SSL with Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d comethunter.skywu.me
```

## Update Process
```bash
# Pull latest changes
git pull origin main

# Build frontend if updated
cd frontend
npm install
npm run build
cd ..

# Reload nginx if frontend changed
sudo nginx -t && sudo systemctl reload nginx

# Update backend
docker-compose build backend
docker-compose up -d backend
```

## Check Status
```bash
docker-compose ps
docker-compose logs backend
curl http://localhost:8000/api/health
```