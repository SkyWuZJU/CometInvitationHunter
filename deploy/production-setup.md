# Comet Hunter Production Setup Guide

## Prerequisites
- Linux server (Ubuntu 20.04+ recommended)
- Docker & Docker Compose installed
- Nginx installed
- Domain: comethunter.skywu.me pointed to your server IP

## Quick Setup

1. **Clone and prepare**
   ```bash
   git clone [your-repo] comet-hunter
   cd comet-hunter
   chmod +x deploy.sh
   ```

2. **Configure environment**
   ```bash
   # Edit production.env with your actual keys
   nano config/production.env
   ```

3. **Deploy**
   ```bash
   ./deploy.sh
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