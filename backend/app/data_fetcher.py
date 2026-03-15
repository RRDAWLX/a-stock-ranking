import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import time
import random
from app import database


def get_recent_trade_dates_akshare(days=60):
    """使用akshare获取最近n个交易日"""
    for retry in range(3):
        try:
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


def fetch_stock_data(stock_code, start_date=None, end_date=None):
    """获取单只股票的历史数据（前复权）"""
    for retry in range(3):
        try:
            # 使用akshare获取日K前复权数据
            df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", adjust="qfq")
            if df is None or df.empty:
                return []

            # 打印列名以便调试
            print(f"股票 {stock_code} 列名: {df.columns.tolist()}")

            # 转换日期格式
            df['date'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')

            # 筛选日期范围
            if start_date:
                df = df[df['date'] >= start_date]
            if end_date:
                df = df[df['date'] <= end_date]

            # 返回需要的列 - 使用正确的列名
            result = []
            for _, row in df.iterrows():
                close = row['收盘'] if '收盘' in df.columns else None
                result.append({
                    'date': row['date'],
                    'close': float(close) if close is not None and pd.notna(close) else None,
                    'adj_factor': 1.0
                })

            return result
        except Exception as e:
            print(f"获取股票 {stock_code} 数据失败 (尝试 {retry+1}/3): {e}")
            if retry < 2:
                time.sleep(1)
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


def fetch_all_stocks_daily_data(start_date, end_date):
    """获取所有股票的日线数据"""
    stock_codes = database.get_all_stock_codes()
    total = len(stock_codes)
    success = 0
    failed = 0

    print(f"开始获取 {total} 只股票的数据 ({start_date} - {end_date})...")

    for i, code in enumerate(stock_codes):
        if (i + 1) % 50 == 0:
            print(f"进度: {i + 1}/{total}")

        try:
            data = fetch_stock_data(code, start_date, end_date)
            for item in data:
                if item['close'] is not None:
                    database.insert_daily_data(
                        code,
                        item['date'],
                        item['close'],
                        item['adj_factor']
                    )
            success += 1
        except Exception as e:
            failed += 1
            if failed <= 5:  # 只打印前几个错误
                print(f"获取 {code} 数据失败: {e}")

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


def full_update():
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
    if not fetch_all_stocks_daily_data(start_date, end_date):
        return False

    # 4. 更新元数据
    database.update_metadata('last_update', end_date)

    print("数据更新完成!")
    return True


def incremental_update():
    """增量更新：获取上次更新日期之后的新数据"""
    # 1. 检查并更新股票名称
    check_and_update_stock_names()

    # 2. 获取上次更新日期
    status = database.get_init_status()
    last_update = status.get('last_update')

    # 3. 获取最近的交易日
    trade_dates = get_recent_trade_dates_akshare(5)
    if not trade_dates:
        print("无法获取交易日历")
        return False

    # 如果没有上次更新，则获取60天数据
    if not last_update:
        return full_update()

    # 找出需要更新的日期
    new_dates = [d for d in trade_dates if d > last_update]
    if not new_dates:
        print("没有新数据需要更新")
        return True

    start_date = new_dates[0]
    end_date = new_dates[-1]

    print(f"增量更新: {start_date} - {end_date}")

    # 4. 获取新数据
    fetch_all_stocks_daily_data(start_date, end_date)

    # 5. 更新元数据
    database.update_metadata('last_update', end_date)

    print("增量更新完成!")
    return True