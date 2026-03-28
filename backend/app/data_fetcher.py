import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import time
import random
from app import database


# ========== 历史数据接口配置 ==========
def get_history_interfaces():
    """定义可用的历史数据接口，按优先级排序"""
    return [
        {
            'name': 'stock_zh_a_hist',
            'func': lambda code: ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq"),
            'date_col': '日期',
            'close_col': '收盘',
        },
        {
            'name': 'stock_zh_a_hist_em',
            'func': lambda code: ak.stock_zh_a_hist_em(symbol=code, period="daily", adjust="qfq"),
            'date_col': '日期',
            'close_col': '收盘',
        },
        {
            'name': 'stock_zh_a_hist_sina',
            'func': lambda code: ak.stock_zh_a_hist_sina(symbol=code),
            'date_col': 'date',
            'close_col': 'close',
        },
    ]


def is_rate_limit_error(e):
    """判断是否是限流错误"""
    error_msg = str(e).lower()
    return any(keyword in error_msg for keyword in [
        'too many requests', '429', 'rate limit', '请求过于频繁',
        '访问频率过高', 'too frequent', '频繁'
    ])


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
                    'close': float(close),
                    'adj_factor': 1.0
                })
        except Exception:
            continue

    return result


def fetch_stock_data(stock_code, start_date=None, end_date=None):
    """获取单只股票的历史数据（前复权），支持接口自动切换"""
    interfaces = get_history_interfaces()
    last_error = None

    for interface in interfaces:
        interface_name = interface['name']

        for retry in range(3):
            try:
                # 添加请求间隔，避免触发限流
                if retry > 0 or interface_name != 'stock_zh_a_hist':
                    time.sleep(random.uniform(0.5, 1.5))

                # 调用接口
                df = interface['func'](stock_code)

                if df is None or df.empty:
                    # 接口返回空数据，尝试下一个接口
                    break

                # 解析数据
                result = parse_interface_data(df, interface)

                # 筛选日期范围
                if start_date:
                    result = [r for r in result if r['date'] >= start_date]
                if end_date:
                    result = [r for r in result if r['date'] <= end_date]

                if result:
                    print(f"[{interface_name}] 股票 {stock_code} 获取 {len(result)} 条数据")
                    return result

                # 数据为空，尝试下一个接口
                break

            except Exception as e:
                last_error = e
                error_type = type(e).__name__

                if is_rate_limit_error(e):
                    # 限流时等待更长时间
                    wait_time = 30 + random.uniform(0, 30)
                    print(f"[{interface_name}] 触发限流，股票 {stock_code}，等待 {wait_time:.1f}s")
                    time.sleep(wait_time)
                else:
                    # 普通错误，短暂等待后重试
                    wait_time = (2 ** retry) + random.uniform(0, 1)
                    print(f"[{interface_name}] 股票 {stock_code} 失败 ({error_type}): {e}")
                    if retry < 2:
                        time.sleep(wait_time)

                # 如果是限流错误，直接跳过当前接口
                if is_rate_limit_error(e):
                    break

    # 所有接口都失败
    return []


def get_recent_trade_dates_akshare(days=60):
    """使用akshare获取最近n个交易日"""
    for retry in range(3):
        try:
            # 添加请求间隔
            if retry > 0:
                time.sleep(random.uniform(1, 3))

            # 获取上证指数历史数据来获取交易日历
            index_df = ak.stock_zh_index_daily(symbol="sh000001")
            if index_df is None or index_df.empty:
                return []

            # 按日期降序排列，取前days个
            dates = index_df['date'].tail(days).tolist()
            # 转换为字符串格式
            return [str(d) for d in sorted(dates)]
        except Exception as e:
            print(f"获取交易日历失败 (尝试 {retry+1}/3): {e}")
            if retry < 2:
                time.sleep(2)
    return []


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
                database.upsert_stock(code, name, None)
                count += 1

            print(f"已更新 {count} 只股票")
            return True
        except Exception as e:
            print(f"初始化股票列表失败 (尝试 {retry+1}/3): {e}")
            if retry < 2:
                time.sleep(2)
    return False


def generate_test_data():
    """生成测试数据"""
    print("生成测试数据...")
    # 生成50只测试股票
    test_stocks = [
        ('600000', '浦发银行'),
        ('600016', '民生银行'),
        ('600019', '宝钢股份'),
        ('600028', '中国石化'),
        ('600030', '中信证券'),
        ('600036', '招商银行'),
        ('600048', '保利发展'),
        ('600104', '上汽集团'),
        ('600176', '中国巨石'),
        ('600519', '贵州茅台'),
        ('600887', '伊利股份'),
        ('601012', '隆基绿能'),
        ('601088', '上海机场'),
        ('601166', '兴业银行'),
        ('601288', '农业银行'),
        ('601318', '中国平安'),
        ('601398', '工商银行'),
        ('601857', '中国石油'),
        ('601988', '中国银行'),
        ('603259', '药明康德'),
        ('000001', '平安银行'),
        ('000002', '万科A'),
        ('000063', '中兴通讯'),
        ('000333', '美的集团'),
        ('000651', '格力电器'),
        ('000858', '五粮液'),
        ('002594', '比亚迪'),
        ('002714', '牧原股份'),
        ('300750', '宁德时代'),
        ('300059', '东方财富'),
    ]

    # 生成最近60个交易日的日期
    today = datetime.now()
    dates = []
    for i in range(60, 0, -1):
        date = today - timedelta(days=i)
        if date.weekday() < 5:  # 跳过周末
            dates.append(date.strftime('%Y-%m-%d'))

    for code, name in test_stocks:
        database.upsert_stock(code, name, None)

        # 生成随机价格数据
        base_price = random.uniform(10, 500)
        for date in dates:
            # 添加随机波动
            change = random.uniform(-0.05, 0.05)
            base_price = base_price * (1 + change)
            database.insert_daily_data(code, date, round(base_price, 2), 1.0)

    database.update_metadata('last_update', dates[-1])
    print(f"测试数据生成完成: {len(test_stocks)} 只股票, {len(dates)} 天数据")
    return True


def use_test_data():
    """使用测试数据"""
    return generate_test_data()


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
                            item['close'],
                            item['adj_factor']
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
                                code, item['date'], item['close'], item['adj_factor']
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
            database.upsert_stock(code, name, None)
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
    """增量更新：为每只股票单独获取缺失的数据"""
    # 1. 检查并更新股票名称
    check_and_update_stock_names()

    # 2. 获取最新的交易日
    trade_dates = get_recent_trade_dates_akshare(5)
    if not trade_dates:
        print("无法获取交易日历")
        return False
    end_date = trade_dates[-1]

    # 3. 检查系统是否已有数据
    system_latest = database.get_latest_trade_date()
    if not system_latest:
        # 没有数据，执行完整更新
        return full_update(progress_callback)

    # 检查是否有新数据
    new_trade_dates = [d for d in trade_dates if d > system_latest]
    if not new_trade_dates:
        print("没有新数据需要更新...")
        return True

    start_date = new_trade_dates[0]
    print(f"增量更新: {start_date} - {end_date}")

    # 4. 获取所有股票列表
    stock_codes = database.get_all_stock_codes()
    total = len(stock_codes)
    success = 0
    failed = 0
    no_data_count = 0  # 没有历史数据的股票数量

    # 5. 逐只股票获取数据
    for i, code in enumerate(stock_codes):
        if (i + 1) % 100 == 0:
            print(f"进度: {i + 1}/{total}")

        # 更新进度 (50% -> 99%)
        if progress_callback:
            progress = 50 + (i + 1) / total * 49
            progress_callback(round(progress, 2))

        # 获取该股票在数据库中最近一个有数据的日期
        stock_latest = database.get_stock_latest_date(code)

        if stock_latest:
            # 有历史数据：从最近日期（不含）到最新日期
            stock_start = None  # 让 API 自动处理
            stock_end = end_date
        else:
            # 没有历史数据：获取最近60个交易日
            no_data_count += 1
            recent_60_dates = get_recent_trade_dates_akshare(60)
            if recent_60_dates:
                stock_start = recent_60_dates[0]
                stock_end = recent_60_dates[-1]
            else:
                continue

        # 添加请求间隔，避免触发限流
        if i > 0:
            time.sleep(random.uniform(0.3, 1.0))

        try:
            # 确定获取范围
            if stock_latest:
                # 有数据：从数据库最新日期的下一个交易日起
                # 找出 stock_latest 在 new_trade_dates 中的下一个位置
                fetch_start = stock_latest
            else:
                # 无数据：使用60天
                fetch_start = stock_start
                fetch_end = stock_end

            data = fetch_stock_data(code, fetch_start, fetch_end)
            if data:
                for item in data:
                    if item['close'] is not None:
                        database.insert_daily_data(
                            code, item['date'], item['close'], item['adj_factor']
                        )
                success += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            if failed <= 5:
                print(f"获取 {code} 数据失败: {e}")

    print(f"增量更新完成! 成功: {success}, 失败: {failed}, 无历史数据: {no_data_count}")
    return True