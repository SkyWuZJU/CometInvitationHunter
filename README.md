# Comet Invitation Hunter

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