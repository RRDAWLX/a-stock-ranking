# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A股股票收益排行系统 - A web application for analyzing and ranking Chinese A-shares based on weighted return calculations and weighted ranking scores.

**支持的股票市场：**
- 沪市主板（6开头）
- 科创板（688开头）
- 深市主板（00/002/003开头）
- 创业板（30开头）
- 北交所（83/87/88/92开头）

## Commands

### First-time setup
```bash
# Backend dependencies
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend dependencies
cd frontend
npm install
```

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

Production/deployment environment variables:
- `VITE_BACKEND_HOST` — backend hostname (default: `localhost`), set in `vite.config.js` define
- `FLASK_DEBUG` — Flask debug mode (default: `1`), set to `0` for production

## Database

SQLite at `data/stocks.db`, two tables:
- `stocks` — stock code (PK) and name
- `daily_data` — stock_code, date, close price; unique on (stock_code, date)

No ORM, uses raw `sqlite3` with `sqlite3.Row` for dict-like access.

## Architecture

### Backend (Flask)
- `backend/run.py` - Entry point, reads config and starts server
- `backend/app/main.py` - Flask app factory, blueprint registration
- `backend/app/routes.py` - API endpoints with input validation
- `backend/app/database.py` - SQLite database operations (raw sqlite3, no ORM)
- `backend/app/calculator.py` - Weighted return calculation logic and weighted ranking score logic
- `backend/app/data_fetcher.py` - Stock data fetching via akshare API
  - 支持东财(`stock_zh_a_hist`)、腾讯(`stock_zh_a_hist_tx`)两个数据接口自动切换
  - 北交所股票只使用东财接口（腾讯接口不支持北交所）
  - 内置限流保护：接口连续失败3次自动禁用60秒，请求间隔指数退避（0.5-1.5s基础延迟 × 1.0-4.0倍数）
  - 交易日历缓存1小时，股票列表带内存缓存

### Frontend (React + Vite)
- `frontend/src/main.jsx` - Router configuration with react-router-dom
- `frontend/src/App.jsx` - Layout component (header, navigation)
- `frontend/src/context/AppContext.jsx` - Shared state management via React Context
- `frontend/src/api.js` - Backend API calls, backend port injected via vite define
- `frontend/src/pages/` - Route pages (WeightedReturnHeatmapPage, WeightedReturnRankingPage, WeightedRankPage, WeightedRankHeatmapPage)
- `frontend/src/components/` - Reusable UI components (WeightedReturnFormulaForm, WeightedReturnHeatmap, WeightedReturnRankingTable, WeightedRankTable, WeightedRankHeatmap)
- `frontend/src/utils/stockUrl.js` - Generate Xueqiu stock detail page URLs

### Key Data Flow

**加权收益 (Weighted Return):**
1. Frontend calls `/api/weighted-return/calculate` with formula: `[{days, weight}, ...]`
2. Backend calculates weighted return: `sum(return_rate[days] * weight)`
3. Results sorted by return rate, returned as ranking list or heatmap data

**加权排行分 (Weighted Ranking Score):**
1. Frontend calls `/api/weighted-rank/calculate` with formula: `[{days, weight}, ...]`
2. Backend calculates ranking for each period, then computes weighted ranking score: `sum(rank[days] * weight)`
3. Results sorted by ranking score (lower is better), returned as ranking list or heatmap data

**两者关键区别：** 加权排行分API要求权重总和必须为1.0（`require_weight_sum=True`），加权收益API无此限制。

### Pages

1. **加权收益热力图 (Weighted Return Heatmap)** - Shows top 10 stocks by weighted return over recent 10 trading days
2. **加权收益排行 (Weighted Return Ranking)** - Shows current ranking by weighted return
3. **加权排行分热力图 (Weighted Rank Heatmap)** - Shows top 10 stocks by weighted ranking score over recent 10 trading days
4. **加权排行分 (Weighted Ranking Score)** - Shows ranking by weighted score based on period rankings

### Data Completeness
- Status bar shows count of stocks with incomplete/no data
- Each page displays number of stocks participating in calculation
- Latest update date is dynamically fetched from database via `/api/init-status`

### Async Data Update
Data update operations (`/api/update-data`) run asynchronously in background threads due to long execution time (5000+ stocks). Progress is polled via `/api/update-status`.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/init-status` | GET | Get system init status with data completeness info |
| `/api/data-completeness` | GET | Get data completeness status |
| `/api/weighted-return/calculate` | POST | Calculate weighted return ranking |
| `/api/weighted-return/heatmap` | POST | Get weighted return heatmap data |
| `/api/weighted-rank/calculate` | POST | Calculate weighted ranking score |
| `/api/weighted-rank/heatmap` | POST | Get weighted ranking score heatmap data |
| `/api/update-data` | POST | Trigger async data update |
| `/api/update-status` | GET | Get update task status |
| `/api/cancel-update` | POST | Cancel update task |
| `/api/latest-date` | GET | Get latest trading date |

## Project Structure

```
├── backend/app/             # Flask 后端（见 Architecture 部分说明）
├── frontend/src/            # React 前端（见 Architecture 部分说明）
├── data/                    # SQLite 数据库 (stocks.db)
├── config.json              # 端口配置（前后端共用）
└── start.sh                 # 同时启动前后端
```

## Notes

- 数据使用不复权价格计算（adjust=""）
- 北交所股票代码识别：83/87/88/92开头
- 股票详情链接指向雪球网 (xueqiu.com)