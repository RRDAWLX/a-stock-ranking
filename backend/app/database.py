import sqlite3
from datetime import datetime
from contextlib import contextmanager
from pathlib import Path
from functools import lru_cache

DB_PATH = Path(__file__).parent.parent.parent / "data" / "stocks.db"

# 股票列表缓存
_stock_list_cache = None


@contextmanager
def get_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """初始化数据库表"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # 股票基本信息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                list_date TEXT
            )
        """)

        # 每日行情表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                date TEXT NOT NULL,
                close REAL,
                adj_factor REAL,
                UNIQUE(stock_code, date)
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stock_date ON daily_data(stock_code, date)
        """)

        conn.commit()


def get_init_status():
    """获取初始化状态"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # 检查是否有股票数据
        cursor.execute("SELECT COUNT(*) as count FROM stocks")
        stock_count = cursor.fetchone()["count"]

        # 获取最新更新日期（从 daily_data 表中获取最近一个有数据的日期）
        last_update = get_latest_trade_date()

        # 检查是否有数据
        has_data = stock_count > 0

        return {
            "initialized": has_data,
            "stock_count": stock_count,
            "last_update": last_update
        }


def get_latest_trade_date():
    """获取最新的交易日期"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(date) as max_date FROM daily_data")
        row = cursor.fetchone()
        return row["max_date"] if row and row["max_date"] else None


def get_stock_data_dates(stock_code):
    """获取指定股票的所有日期"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT date FROM daily_data WHERE stock_code = ? ORDER BY date", (stock_code,))
        return [row["date"] for row in cursor.fetchall()]


def get_stock_latest_date(stock_code):
    """获取指定股票在数据库中最近一个有数据的日期"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(date) as max_date FROM daily_data WHERE stock_code = ?", (stock_code,))
        row = cursor.fetchone()
        return row["max_date"] if row and row["max_date"] else None


def get_data_completeness():
    """获取数据完整性状态"""
    latest_date = get_latest_trade_date()
    if not latest_date:
        return {
            "total_stocks": 0,
            "complete_stocks": 0,
            "incomplete_stocks": 0,
            "missing_stocks": 0,
            "latest_date": None
        }

    with get_connection() as conn:
        cursor = conn.cursor()

        # 获取所有股票数量
        cursor.execute("SELECT COUNT(*) as count FROM stocks")
        total_stocks = cursor.fetchone()["count"]

        # 获取数据完整的股票数量（最新日期等于系统最新日期）
        cursor.execute("""
            SELECT COUNT(DISTINCT stock_code) as count
            FROM daily_data
            WHERE date = ?
        """, (latest_date,))
        complete_stocks = cursor.fetchone()["count"]

        # 获取没有数据的股票数量
        cursor.execute("""
            SELECT COUNT(*) as count FROM stocks
            WHERE code NOT IN (SELECT DISTINCT stock_code FROM daily_data)
        """)
        missing_stocks = cursor.fetchone()["count"]

        # 数据不完整但有数据的股票数量
        incomplete_stocks = total_stocks - complete_stocks - missing_stocks

        return {
            "total_stocks": total_stocks,
            "complete_stocks": complete_stocks,
            "incomplete_stocks": incomplete_stocks,
            "missing_stocks": missing_stocks,
            "latest_date": latest_date
        }


def get_stock_list():
    """获取所有股票列表（带缓存）"""
    global _stock_list_cache
    if _stock_list_cache is None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT code, name, list_date FROM stocks ORDER BY code")
            _stock_list_cache = [dict(row) for row in cursor.fetchall()]
    return _stock_list_cache


def clear_stock_cache():
    """清除股票列表缓存"""
    global _stock_list_cache
    _stock_list_cache = None


def get_stock_daily_data(stock_code, start_date=None, end_date=None):
    """获取股票历史数据"""
    with get_connection() as conn:
        cursor = conn.cursor()

        query = "SELECT date, close, adj_factor FROM daily_data WHERE stock_code = ?"
        params = [stock_code]

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date"

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def get_all_stock_codes():
    """获取所有股票代码"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT code FROM stocks")
        return [row["code"] for row in cursor.fetchall()]


def get_all_stock_latest_dates():
    """一次性获取所有股票的最新日期"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.stock_code, MAX(d.date) as max_date
            FROM daily_data d
            GROUP BY d.stock_code
        """)
        return {row["stock_code"]: row["max_date"] for row in cursor.fetchall()}


def insert_daily_data_batch(data_list):
    """批量插入每日行情数据"""
    if not data_list:
        return
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT OR REPLACE INTO daily_data (stock_code, date, close, adj_factor)
            VALUES (?, ?, ?, ?)
        """, data_list)
        conn.commit()


def upsert_stock(code, name, list_date=None):
    """插入或更新股票信息"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO stocks (code, name, list_date)
            VALUES (?, ?, ?)
            ON CONFLICT(code) DO UPDATE SET
                name = excluded.name,
                list_date = excluded.list_date
        """, (code, name, list_date))
        conn.commit()


def insert_daily_data(stock_code, date, close, adj_factor):
    """插入每日行情数据"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO daily_data (stock_code, date, close, adj_factor)
            VALUES (?, ?, ?, ?)
        """, (stock_code, date, close, adj_factor))
        conn.commit()


def get_stocks_with_recent_data(days=30):
    """获取最近n天有数据的股票"""
    latest_date = get_latest_trade_date()
    if not latest_date:
        return []

    # 计算days天前的日期
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT stock_code FROM daily_data
            WHERE date >= (
                SELECT DISTINCT date FROM daily_data
                ORDER BY date DESC
                LIMIT 1 OFFSET ?
            )
        """, [days - 1])
        return [row["stock_code"] for row in cursor.fetchall()]


def get_recent_trade_dates(days=10):
    """获取最近n个交易日期"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT date FROM daily_data
            ORDER BY date DESC
            LIMIT ?
        """, [days])
        dates = [row["date"] for row in cursor.fetchall()]
        return list(reversed(dates))  # 返回升序排列