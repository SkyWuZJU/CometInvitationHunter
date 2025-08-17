# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Comet Invitation Hunter** is a system that monitors Twitter/X for Comet browser invitation codes and automatically notifies verified users via email. The system has three main components:

- **Backend**: FastAPI service handling user verification and OAuth
- **Monitor**: Background service continuously scanning Twitter for invitations
- **Frontend**: Simple TypeScript/Vite dashboard for monitoring status

## Architecture

### Core Services
- **FastAPI Backend** (`backend/main.py`): REST API with user verification via Twitter OAuth, health checks, and debug endpoints
- **Monitoring Service** (`monitor/main.py`): Async service that searches Twitter, classifies posts, and sends email notifications
- **Database**: SQLite with SQLAlchemy ORM storing users, posts, and email batches

### Key Modules
- **Post Classification**: Uses regex patterns to identify free vs conditional invitations
- **Email Notifications**: Uses Resend API for batched email delivery to verified users
- **Twitter Integration**: OAuth for user verification + Utools API for monitoring

## Development Commands

### Setup
```bash
# Initial setup
./setup_env.sh

# Frontend dependencies
cd frontend && npm install
```

### Running Services
```bash
# Backend (choose one method)
cd backend && uvicorn main:app --reload --port 8000
# OR
python backend/start_backend.py

# Frontend
cd frontend && npm run dev

# Monitor Service
cd monitor && python main.py
```

### Testing
```bash
# Run all tests
cd backend && python run_all_tests.py

# Individual test files
cd backend && python test_database.py
python test_email_system.py
python test_monitor_integration.py

# Specific component tests
python backend/test_api.py
python backend/test_monitor_service.py
python backend/test_utools_client.py
```

### Environment Configuration
- Development: `config/development.env`
- Production: `config/production.env`
- Required keys: `UTOOLS_API_KEY`, `RESEND_API_KEY`, `TWITTER_CONSUMER_KEY`, `TWITTER_CONSUMER_SECRET`

## Configuration Files

### Search Configuration
- **Keywords**: `backend/search_config.py` - Twitter search terms
- **Patterns**: `backend/classification_patterns.py` - Regex for invitation detection
- **Intervals**: Configurable via env vars or imported modules

### Database Schema
- **users**: Verified email addresses
- **posts**: Processed Twitter posts with classification
- **email_batches**: Notification history tracking

## Key API Endpoints

- `POST /api/auth/twitter/init` - Start OAuth flow
- `POST /api/users/verify` - Complete verification via Twitter OAuth
- `POST /api/users/check-follow` - Verify user follows @0xSky99
- `GET /api/health` - Service health check
- `GET /` - API documentation and status

## Monitoring Service Flow

1. **Search**: Uses Utools API to search Twitter with configured keywords
2. **Deduplicate**: Removes already-processed tweets
3. **Classify**: Identifies free vs conditional invitations
4. **Store**: Saves new posts to database
5. **Notify**: Sends batched emails to all verified users