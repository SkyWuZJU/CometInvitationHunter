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

# Make deploy script executable
chmod +x deploy.sh

# Configure environment
mkdir -p config                # Create config directory if it doesn't exist
nano config/production.env     # Add your API keys
```

### 6. Deploy
```bash
./deploy.sh
```

### 7. Setup SSL (after DNS points to server)
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d comethunter.skywu.me
```

### 8. Verify deployment
```bash
curl http://comethunter.skywu.me/api/health
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
git pull origin main
./deploy.sh
```

## Check Status
```bash
docker-compose ps
docker-compose logs backend
curl http://localhost:8000/api/health
```