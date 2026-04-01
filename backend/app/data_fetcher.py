import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import time
import random
from app import database


# ========== 历史数据接口配置 ==========
def get_history_interfaces(stock_code=None):
    """定义可用的历史数据接口，按优先级排序

    Args:
        stock_code: 股票代码，用于判断是否是北交所股票
                   北交所股票(83/87/88开头)只使用东财接口，腾讯接口不支持
    """
    interfaces = [
        {
            'name': 'stock_zh_a_hist',
            'func': lambda code, start, end: ak.stock_zh_a_hist(
                symbol=code, period="daily", start_date=start, end_date=end, adjust=""
            ),
            'date_col': '日期',
            'close_col': '收盘',
        },
    ]

    # 北交所股票(83/87/88开头)只使用东财接口，腾讯接口不支持北交所
    if stock_code and (stock_code.startswith('83') or stock_code.startswith('87') or stock_code.startswith('88')):
        return interfaces

    # 非北交所股票，添加腾讯接口作为备用
    interfaces.append({
        'name': 'stock_zh_a_hist_tx',
        'func': lambda code, start, end: ak.stock_zh_a_hist_tx(
            symbol=_add_market_prefix(code), start_date=start, end_date=end, adjust=""
        ),
        'date_col': 'date',
        'close_col': 'close',
    })

    return interfaces


def _add_market_prefix(code):
    """为股票代码添加市场标识 (腾讯接口需要)

    市场标识:
    - 6 开头: 沪市 (sh)
    - 83/87/88 开头: 北交所 (bj) - 注意: 腾讯接口不支持北交所，此函数仅用于代码转换
    - 其他: 深市 (sz)，包括创业板(30)、主板(00/002/003)
    """
    if code.startswith('6'):
        return f'sh{code}'
    elif code.startswith('83') or code.startswith('87') or code.startswith('88'):
        return f'bj{code}'
    else:
        return f'sz{code}'


def parse_interface_data(df, interface_info):
    """解析不同接口返回的数据格式"""
    result = []
    date_col = interface_info.get('date_col', '日期')
    close_col = interface_info.get('close_col', '收盘')

    for _, row in df.iterrows():
        try:
            date_str = str(row.get(date_col, ''))
            # 转换日期格式
            if '-' in date_str:
                date = date_str[:10]
            else:
                date = pd.to_datetime(date_str).strftime('%Y-%m-%d')

            close = row.get(close_col)
            if close is not None:
                result.append({
                    'date': date,
                    'close': float(close)
                })
        except Exception:
            continue

    return result


def fetch_stock_data(stock_code, start_date=None, end_date=None):
    """获取单只股票的历史数据（不复权），支持接口自动切换

    Args:
        stock_code: 股票代码 (不带市场标识)
        start_date: 开始日期 (YYYY-MM-DD 格式)
        end_date: 结束日期 (YYYY-MM-DD 格式)
    """
    # 转换日期格式为 YYYYMMDD (akshare 接口需要)
    start_str = start_date.replace('-', '') if start_date else '19000101'
    end_str = end_date.replace('-', '') if end_date else '20500101'

    interfaces = get_history_interfaces(stock_code)

    for interface in interfaces:
        interface_name = interface['name']

        try:
            df = interface['func'](stock_code, start_str, end_str)

            if df is None or df.empty:
                # 接口返回空数据，尝试下一个接口
                continue

            # 解析数据
            result = parse_interface_data(df, interface)

            # 筛选日期范围 (再次过滤确保精确)
            if start_date:
                result = [r for r in result if r['date'] >= start_date]
            if end_date:
                result = [r for r in result if r['date'] <= end_date]

            if result:
                print(f"[{interface_name}] 股票 {stock_code} 获取 {len(result)} 条数据")
                return result

        except Exception as e:
            error_type = type(e).__name__
            print(f"[{interface_name}] 股票 {stock_code} 失败 ({error_type}): {e}")

    # 所有接口都失败
    return []


# 交易日历缓存
_trade_dates_cache = None
_trade_dates_cache_time = 0
CACHE_EXPIRE_SECONDS = 3600  # 缓存有效期1小时


def get_recent_trade_dates_akshare(days=60):
    """使用akshare获取最近n个交易日（缓存1小时）"""
    global _trade_dates_cache, _trade_dates_cache_time

    current_time = time.time()

    # 检查缓存是否有效（未过期）
    if _trade_dates_cache is not None and (current_time - _trade_dates_cache_time) < CACHE_EXPIRE_SECONDS:
        return _trade_dates_cache[-days:] if days <= len(_trade_dates_cache) else _trade_dates_cache

    # 缓存过期，重新获取
    old_cache = _trade_dates_cache  # 保留旧缓存以便失败时使用

    for retry in range(3):
        try:
            if retry > 0:
                time.sleep(random.uniform(1, 3))

            index_df = ak.stock_zh_index_daily(symbol="sh000001")
            if index_df is None or index_df.empty:
                break  # 尝试使用旧缓存

            # 获取所有日期并转换为字符串
            dates = [str(d) for d in index_df['date'].tolist()]
            # 按日期升序排序（旧→新）
            all_dates = tuple(sorted(dates))

            # 更新缓存
            _trade_dates_cache = all_dates
            _trade_dates_cache_time = current_time

            # 取最后 days 个（即最近的 days 个交易日）
            return all_dates[-days:] if days <= len(all_dates) else all_dates
        except Exception as e:
            print(f"获取交易日历失败 (尝试 {retry+1}/3): {e}")
            if retry < 2:
                time.sleep(2)

    # 获取失败，返回旧缓存（如果有）
    if old_cache is not None:
        return old_cache[-days:] if days <= len(old_cache) else old_cache

    return ()


def init_stock_list():
    """初始化股票列表"""
    for retry in range(3):
        try:
            print("正在获取A股股票列表...")
            # 使用 stock_info_a_code_name 接口获取股票代码和名称
            df = ak.stock_info_a_code_name()
            if df is None or df.empty:
                print("获取股票列表失败")
                return False

            count = 0
            for _, row in df.iterrows():
                code = row['code']
                name = row['name']
                # 简单获取代码，不获取上市日期
                database.upsert_stock(code, name)
                count += 1

            print(f"已更新 {count} 只股票")
            return True
        except Exception as e:
            print(f"初始化股票列表失败 (尝试 {retry+1}/3): {e}")
            if retry < 2:
                time.sleep(2)
    return False




def fetch_all_stocks_daily_data(start_date, end_date, progress_callback=None):
    """获取所有股票的日线数据"""
    stock_codes = database.get_all_stock_codes()
    total = len(stock_codes)
    success = 0
    failed = 0
    failed_stocks = []

    print(f"开始获取 {total} 只股票的数据 ({start_date} - {end_date})...")

    for i, code in enumerate(stock_codes):
        if (i + 1) % 50 == 0:
            print(f"进度: {i + 1}/{total}")

        # 每获取1只股票更新一次进度 (30% -> 99%)
        if progress_callback:
            progress = 30 + (i + 1) / total * 69
            progress_callback(round(progress, 2))

        # 添加请求间隔，避免触发限流
        if i > 0:
            time.sleep(random.uniform(0.3, 1.0))

        try:
            data = fetch_stock_data(code, start_date, end_date)
            if data:
                for item in data:
                    if item['close'] is not None:
                        database.insert_daily_data(
                            code,
                            item['date'],
                            item['close']
                        )
                success += 1
            else:
                failed_stocks.append(code)
                failed += 1
        except Exception as e:
            failed_stocks.append(code)
            failed += 1
            if failed <= 5:
                print(f"获取 {code} 数据失败: {e}")

    # 重试失败的股票
    if failed_stocks:
        print(f"开始重试 {len(failed_stocks)} 只失败的股票...")
        retry_failed = []
        for code in failed_stocks:
            time.sleep(random.uniform(2, 4))  # 重试时间隔更长
            try:
                data = fetch_stock_data(code, start_date, end_date)
                if data:
                    for item in data:
                        if item['close'] is not None:
                            database.insert_daily_data(
                                code, item['date'], item['close']
                            )
                    success += 1
                    failed -= 1
                    print(f"重试成功: {code}")
                else:
                    retry_failed.append(code)
            except:
                pass

        if retry_failed:
            print(f"重试后仍有 {len(retry_failed)} 只股票失败")

    print(f"完成! 成功: {success}, 失败: {failed}")
    return success > 0


def check_and_update_stock_names():
    """检查并更新股票名称变化"""
    try:
        df = ak.stock_info_a_code_name()
        if df is None or df.empty:
            return False

        updated = 0
        for _, row in df.iterrows():
            code = row['code']
            name = row['name']
            database.upsert_stock(code, name)
            updated += 1

        print(f"已更新 {updated} 只股票信息")
        return True
    except Exception as e:
        print(f"检查股票名称失败: {e}")
        return False


def full_update(progress_callback=None):
    """完整更新：先更新股票列表，再获取所有股票数据"""
    # 1. 更新股票列表
    if not init_stock_list():
        return False

    # 2. 获取最近60个交易日
    trade_dates = get_recent_trade_dates_akshare(60)
    if not trade_dates:
        print("无法获取交易日历")
        return False

    start_date = trade_dates[0]
    end_date = trade_dates[-1]

    print(f"数据日期范围: {start_date} - {end_date}")

    # 3. 获取所有股票数据
    if not fetch_all_stocks_daily_data(start_date, end_date, progress_callback):
        return False

    # last_update 现在直接从 daily_data 表获取，不需要更新 metadata

    print("数据更新完成!")
    return True


def incremental_update(progress_callback=None):
    """更新数据：为每只股票单独获取缺失的数据"""
    # 1. 检查并更新股票名称
    check_and_update_stock_names()

    # 2. 获取最新的交易日（同时获取60天用于新股票）
    trade_dates = get_recent_trade_dates_akshare(60)
    if not trade_dates:
        print("无法获取交易日历")
        return False
    latest_date = trade_dates[-1]
    start_date_60 = trade_dates[0]

    # 3. 检查系统是否已有数据
    system_latest = database.get_latest_trade_date()
    if not system_latest:
        # 没有数据，执行完整更新
        return full_update(progress_callback)

    print(f"最新交易日: {latest_date}, 数据库最新: {system_latest}")

    # 4. 一次性获取所有股票的最新日期（避免逐个查询）
    stock_latest_dates = database.get_all_stock_latest_dates()

    # 5. 收集需要更新的股票和获取范围
    stocks_to_update = []
    for code, stock_latest in stock_latest_dates.items():
        if stock_latest >= latest_date:
            # 已有最新日期的数据，跳过
            continue
        # 需要更新
        stocks_to_update.append((code, stock_latest, latest_date))

    # 6. 检查没有历史数据的股票（从 stocks 表中获取）
    stocks_with_data = set(stock_latest_dates.keys())
    all_stock_codes = database.get_all_stock_codes()
    stocks_without_data = [code for code in all_stock_codes if code not in stocks_with_data]

    for code in stocks_without_data:
        stocks_to_update.append((code, start_date_60, latest_date))

    need_update_count = len(stocks_to_update)
    print(f"需要更新 {need_update_count} 只股票")

    if need_update_count == 0:
        print("所有股票已是最新数据")
        return True

    success = 0
    failed = 0

    # 7. 逐只股票获取数据
    for i, (code, fetch_start, fetch_end) in enumerate(stocks_to_update):
        if (i + 1) % 100 == 0:
            print(f"进度: {i + 1}/{need_update_count}")

        # 更新进度 (50% -> 99%)
        if progress_callback:
            progress = 50 + (i + 1) / need_update_count * 49
            progress_callback(round(progress, 2))

        # 添加请求间隔，避免触发限流
        if i > 0:
            time.sleep(random.uniform(0.3, 1.0))

        try:
            data = fetch_stock_data(code, fetch_start, fetch_end)
            if data:
                # 批量插入数据
                insert_data = [
                    (code, item['date'], item['close'])
                    for item in data if item['close'] is not None
                ]
                if insert_data:
                    database.insert_daily_data_batch(insert_data)
                success += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            if failed <= 5:
                print(f"获取 {code} 数据失败: {e}")

    print(f"数据更新完成! 成功: {success}, 失败: {failed}")
    return True
