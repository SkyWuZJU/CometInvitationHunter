#!/bin/bash

# Comet Hunter Production Deployment Script
# Simple manual deployment for MVP

set -e

echo "🚀 Starting Comet Hunter deployment..."

# Update production config
echo "📋 Updating production configuration..."
DOMAIN=${DOMAIN:-yourdomain.com}
APP_URL="https://${DOMAIN}"
sed -i "s|CORS_ORIGINS=https://yourdomain.com|CORS_ORIGINS=${APP_URL}|g" config/production.env

# Build and start services
echo "🔧 Building Docker containers..."
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check health
echo "🔍 Checking service health..."
if curl -f http://localhost:8000/api/health; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    exit 1
fi

# Build frontend
echo "🎨 Building frontend..."
cd frontend
npm install
npm run build
cd ..

# Setup nginx for domain
echo "⚙️  Setting up nginx configuration..."
sudo cp nginx.conf /etc/nginx/sites-available/comethunter
sudo ln -sf /etc/nginx/sites-available/comethunter /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

echo "✅ Deployment complete!"
echo "🌐 Access your app at: ${APP_URL}"
echo ""
echo "To update in the future:"
echo "  git pull origin main"
echo "  ./deploy.sh"