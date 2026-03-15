from app import database


def calculate_return_rate(stock_code, days):
    """
    计算股票近n日的收益率
    使用前复权价格计算
    """
    # 获取最近n+1天的数据（需要前一天的收盘价作为基准）
    data = database.get_stock_daily_data(stock_code)

    if len(data) < days + 1:
        return None  # 数据不足

    # 按日期排序（升序）
    data = sorted(data, key=lambda x: x['date'])

    # 获取最近days+1天的数据
    recent_data = data[-(days + 1):]

    if len(recent_data) < days + 1:
        return None

    # 计算收益率: (最新收盘价 - days天前收盘价) / days天前收盘价
    old_price = recent_data[0]['close']
    new_price = recent_data[-1]['close']

    if old_price is None or new_price is None or old_price == 0:
        return None

    return_rate = (new_price - old_price) / old_price
    return return_rate


def calculate_weighted_return(stock_code, formula):
    """
    根据加权公式计算股票收益
    formula: [(days1, weight1), (days2, weight2), ...]
    例如: [(1, 0.1), (5, 0.4), (20, 0.5)]
    """
    total_weight = 0
    weighted_return = 0

    for days, weight in formula:
        return_rate = calculate_return_rate(stock_code, days)
        if return_rate is None:
            return None  # 如果任何一项数据不足，返回None
        weighted_return += return_rate * weight
        total_weight += weight

    if total_weight == 0:
        return None

    return weighted_return


def calculate_all_stocks(formula):
    """
    计算所有股票的加权收益
    返回: [(stock_code, name, return_rate), ...]
    """
    # 获取最近有数据的股票
    stock_codes = database.get_stocks_with_recent_data(30)

    results = []
    for code in stock_codes:
        return_rate = calculate_weighted_return(code, formula)
        if return_rate is not None:
            # 获取股票名称
            stocks = database.get_stock_list()
            name = next((s['name'] for s in stocks if s['code'] == code), code)
            results.append({
                'code': code,
                'name': name,
                'return_rate': return_rate
            })

    # 按收益率降序排列
    results.sort(key=lambda x: x['return_rate'], reverse=True)
    return results


def calculate_ranking_by_date(formula, date):
    """
    计算指定日期的股票排行
    date: 交易日期
    """
    # 一次性获取所有股票名称
    stock_names = {}
    stocks = database.get_stock_list()
    for s in stocks:
        stock_names[s['code']] = s['name']

    # 获取该日期有数据的所有股票
    with database.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT stock_code FROM daily_data
            WHERE date = ?
        """, [date])

        stock_codes = [row['stock_code'] for row in cursor.fetchall()]

    # 优化：一次性获取所有股票在该日期之前的历史数据
    history_data = {}
    with database.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT stock_code, date, close FROM daily_data
            WHERE date <= ?
            ORDER BY stock_code, date
        """, [date])

        current_code = None
        current_data = []
        for row in cursor:
            if row['stock_code'] != current_code:
                if current_code and len(current_data) >= 21:
                    history_data[current_code] = current_data[-21:]
                current_code = row['stock_code']
                current_data = []
            if row['close'] is not None:
                current_data.append({'date': row['date'], 'close': row['close']})

        if current_code and len(current_data) >= 21:
            history_data[current_code] = current_data[-21:]

    # 计算收益
    results = []
    for code in stock_codes:
        data = history_data.get(code, [])
        if len(data) < 21:
            continue

        return_rate = calculate_weighted_return_with_data(data, formula)
        if return_rate is not None:
            results.append({
                'code': code,
                'name': stock_names.get(code, code),
                'return_rate': return_rate
            })

    results.sort(key=lambda x: x['return_rate'], reverse=True)
    return results


def calculate_weighted_return_with_data(data, formula):
    """
    使用给定的历史数据计算加权收益
    data: 已按日期升序排列的历史数据列表
    """
    if len(data) < 21:
        return None

    total_weight = 0
    weighted_return = 0

    for days, weight in formula:
        if len(data) < days + 1:
            return None

        old_price = data[-(days + 1)]['close']
        new_price = data[-1]['close']

        if old_price is None or new_price is None or old_price == 0:
            return None

        return_rate = (new_price - old_price) / old_price
        weighted_return += return_rate * weight
        total_weight += weight

    if total_weight == 0:
        return None

    return weighted_return


def get_heatmap_data(formula, days=10):
    """
    获取热力图数据
    返回: {date: [stock1, stock2, ...]} 每个日期收益前10的股票
    """
    # 获取最近days个交易日期
    trade_dates = database.get_recent_trade_dates(days)

    heatmap = {}
    for date in trade_dates:
        ranking = calculate_ranking_by_date(formula, date)
        # 取前10名
        heatmap[date] = ranking[:10]

    return heatmap


def get_latest_trading_date():
    """获取最新交易日期"""
    return database.get_latest_trade_date()