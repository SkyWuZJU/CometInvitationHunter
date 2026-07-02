# Comet Invitation Hunter

<!-- hy-mt2-i18n:start -->
[English](./README.md) | [中文](./README_zh-CN.md)
<!-- hy-mt2-i18n:end -->


A system to monitor Twitter for invitation codes and automatically respond to them.

## Project Structure

```
├── backend/          # FastAPI backend service
├── frontend/         # TypeScript/Vite frontend
├── monitor/          # Background monitoring service
├── config/           # Environment configuration files
└── setup_env.sh      # Environment setup script
```

## Setup

1. Run the setup script to create Python virtual environment:
   ```bash
   ./setup_env.sh
   ```

2. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

## Development

1. Activate Python virtual environment:
   ```bash
   source venv/bin/activate
   ```

2. Start backend server:
   ```bash
   cd backend
   uvicorn main:app --reload --port 8000
   ```

3. Start frontend development server:
   ```bash
   cd frontend
   npm run dev
   ```

## Configuration

- Development: `config/development.env`
- Production: `config/production.env`

## Production Deployment
Files Related:
- Dockerfile - Lightweight container setup
- docker-compose.yml - Service orchestration
- nginx.conf - Reverse proxy configuration
- deploy.sh - One-command deployment script
- deploy/production-setup.md - Complete setup guide

Key Features:
- Uses SQLite for simplicity (no external DB needed)
- Single Docker container for backend
- Nginx serves frontend + proxies API
- Manual updates via ./deploy.sh
- Configured for comethunter.skywu.me

To Deploy:
1. Upload to your Linux server
2. Run ./deploy.sh
3. Add SSL with certbot --nginx -d comethunter.skywu.me
