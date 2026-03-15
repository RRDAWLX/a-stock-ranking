# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A股股票收益排行系统 - A web application for analyzing and ranking Chinese A-shares based on weighted return calculations.

## Commands

### Start both services (recommended)
```bash
./start.sh
```
Stops with Ctrl+C.

### Start services individually

**Backend:**
```bash
cd backend
source venv/bin/activate
python run.py
```

**Frontend:**
```bash
cd frontend
npm run dev
```

### Build frontend for production
```bash
cd frontend
npm run build
```

## Configuration

Port configuration is centralized in `config.json` at the project root:
```json
{
  "frontend": { "port": 3001 },
  "backend": { "port": 5001 }
}
```
Both `vite.config.js` and `run.py` read from this file.

## Architecture

### Backend (Flask)
- `backend/run.py` - Entry point, reads config and starts server
- `backend/app/main.py` - Flask app factory, blueprint registration
- `backend/app/routes.py` - API endpoints
- `backend/app/database.py` - SQLAlchemy database operations
- `backend/app/calculator.py` - Weighted return calculation logic
- `backend/app/data_fetcher.py` - Stock data fetching via akshare API

### Frontend (React + Vite)
- `frontend/src/main.jsx` - Router configuration with react-router-dom
- `frontend/src/App.jsx` - Layout component (header, navigation)
- `frontend/src/context/AppContext.jsx` - Shared state management via React Context
- `frontend/src/api.js` - Backend API calls, backend port injected via vite define
- `frontend/src/pages/` - Route pages (WeightedReturnHeatmapPage, WeightedReturnRankingPage)
- `frontend/src/components/` - Reusable UI components (WeightedReturnFormulaForm, WeightedReturnHeatmap, WeightedReturnRankingTable)

### Key Data Flow
1. Frontend calls `/api/weighted-return/calculate` with formula: `[{days, weight}, ...]`
2. Backend calculates weighted return: `sum(return_rate[days] * weight)`
3. Results sorted by return rate, returned as ranking list or heatmap data

### Async Data Update
Data update operations (`/api/update-data`) run asynchronously in background threads due to long execution time (5000+ stocks). Progress is polled via `/api/update-status`.