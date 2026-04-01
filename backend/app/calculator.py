from app import database


def calculate_return_rate(stock_code, days):
    """
    计算股票近n日的收益率
    使用前复权价格计算
    """
    data = database.get_stock_daily_data(stock_code)

    if len(data) < days + 1:
        return None

    data = sorted(data, key=lambda x: x['date'])
    recent_data = data[-(days + 1):]

    if len(recent_data) < days + 1:
        return None

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
            return None
        weighted_return += return_rate * weight
        total_weight += weight

    if total_weight == 0:
        return None

    return weighted_return


def _load_history_data(date, need_days):
    """预加载所有股票的历史数据（优化：一次查询获取所有数据）

    Args:
        date: 截止日期
        need_days: 需要的历史数据天数

    Returns:
        (history_data, stock_names, stock_codes)
    """
    # 一次性获取所有股票名称（避免多次查询）
    stock_names = {}
    stocks = database.get_stock_list()
    for s in stocks:
        stock_names[s['code']] = s['name']

    # 获取最近30天有数据的股票
    stock_codes = database.get_stocks_with_recent_data(30)

    # 预加载所有股票的历史数据
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
                if current_code and len(current_data) >= need_days:
                    history_data[current_code] = current_data[-need_days:]
                current_code = row['stock_code']
                current_data = []
            if row['close'] is not None:
                current_data.append({'date': row['date'], 'close': row['close']})

        if current_code and len(current_data) >= need_days:
            history_data[current_code] = current_data[-need_days:]

    return history_data, stock_names, stock_codes


def _calculate_weighted_return_with_data(data, formula):
    """使用给定的历史数据计算加权收益"""
    max_days = max([days for days, _ in formula]) if formula else 0

    if len(data) < max_days + 1:
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


def _calculate_period_returns(data, formula):
    """计算各周期的收益率

    Returns:
        dict: {days: return_rate} 或 None（数据不足）
    """
    max_days = max([days for days, _ in formula]) if formula else 0

    if len(data) < max_days + 1:
        return None

    returns = {}
    for days, weight in formula:
        if len(data) < days + 1:
            return None

        old_price = data[-(days + 1)]['close']
        new_price = data[-1]['close']

        if old_price is None or new_price is None or old_price == 0:
            return None

        return_rate = (new_price - old_price) / old_price
        returns[days] = return_rate

    return returns


def calculate_all_stocks(formula):
    """
    计算所有股票的加权收益
    返回: (results, total_count)
    """
    # 一次性获取股票名称（避免多次查询）
    stock_names = {}
    stocks = database.get_stock_list()
    for s in stocks:
        stock_names[s['code']] = s['name']

    stock_codes = database.get_stocks_with_recent_data(30)
    max_days = max([days for days, _ in formula]) if formula else 0

    # 批量获取历史数据（优化：减少数据库查询次数）
    latest_date = database.get_latest_trade_date()
    if not latest_date:
        return [], 0

    history_data, _, _ = _load_history_data(latest_date, max_days + 1)

    results = []
    for code in stock_codes:
        data = history_data.get(code, [])
        if len(data) < max_days + 1:
            continue

        period_returns = _calculate_period_returns(data, formula)
        if period_returns is None:
            continue

        weighted_return = sum(period_returns.get(days, 0) * weight for days, weight in formula)
        name = stock_names.get(code, code)

        results.append({
            'code': code,
            'name': name,
            'return_rate': weighted_return,
            'period_returns': {str(days): rate for days, rate in period_returns.items()}
        })

    results.sort(key=lambda x: x['return_rate'], reverse=True)
    return results, len(results)


def calculate_ranking_by_date(formula, date):
    """
    计算指定日期的股票排行
    date: 交易日期
    """
    max_days = max([days for days, _ in formula]) if formula else 0
    need_days = max_days + 1

    # 使用优化后的数据加载函数
    history_data, stock_names, stock_codes = _load_history_data(date, need_days)

    results = []
    for code in stock_codes:
        data = history_data.get(code, [])
        if len(data) < need_days:
            continue

        return_rate = _calculate_weighted_return_with_data(data, formula)
        if return_rate is not None:
            results.append({
                'code': code,
                'name': stock_names.get(code, code),
                'return_rate': return_rate
            })

    results.sort(key=lambda x: x['return_rate'], reverse=True)
    return results


def get_heatmap_data(formula, days=10):
    """
    获取热力图数据
    返回: {date: {data: [stock1, stock2, ...], total_count: n}}
    """
    trade_dates = database.get_recent_trade_dates(days)

    heatmap = {}
    for date in trade_dates:
        ranking = calculate_ranking_by_date(formula, date)
        heatmap[date] = {
            'data': ranking[:10],
            'total_count': len(ranking)
        }

    return heatmap


def get_latest_trading_date():
    """获取最新交易日期"""
    return database.get_latest_trade_date()


def _calculate_weighted_ranking_core(formula, history_data, stock_names, stock_codes):
    """计算加权排行分的核心逻辑（消除重复代码）

    Returns:
        (results, total_count)
    """
    max_days = max([days for days, _ in formula]) if formula else 0
    need_days = max_days + 1

    # 计算每只股票在各周期的收益率
    stock_returns = {}
    for code in stock_codes:
        data = history_data.get(code, [])
        if len(data) < need_days:
            continue

        returns = _calculate_period_returns(data, formula)
        if returns is not None:
            stock_returns[code] = returns

    # 为每个周期分别计算排行
    period_rankings = {}
    for days, weight in formula:
        period_data = []
        for code, returns in stock_returns.items():
            if days in returns:
                period_data.append({
                    'code': code,
                    'return_rate': returns[days]
                })

        period_data.sort(key=lambda x: x['return_rate'], reverse=True)

        rankings = {}
        current_rank = 1
        for i, item in enumerate(period_data):
            if i > 0 and period_data[i-1]['return_rate'] != item['return_rate']:
                current_rank = i + 1
            rankings[item['code']] = current_rank

        period_rankings[days] = rankings

    # 计算加权排行分
    results = []
    for code, returns in stock_returns.items():
        ranking_score = 0
        rank_details = {}

        for days, weight in formula:
            rank = period_rankings[days].get(code, 0)
            if rank > 0:
                ranking_score += rank * weight
                rank_details[f'rank_{days}'] = rank

        if ranking_score > 0:
            results.append({
                'code': code,
                'name': stock_names.get(code, code),
                'ranking_score': ranking_score,
                'rank_details': rank_details
            })

    results.sort(key=lambda x: x['ranking_score'])
    return results, len(results)


def calculate_weighted_ranking_score(formula):
    """
    计算加权收益排行分
    formula: [(days1, weight1), (days2, weight2), ...]
    返回: (results, total_count)
    """
    latest_date = database.get_latest_trade_date()
    if not latest_date:
        return [], 0

    max_days = max([days for days, _ in formula]) if formula else 0
    need_days = max_days + 1

    # 使用优化后的数据加载
    history_data, stock_names, stock_codes = _load_history_data(latest_date, need_days)

    return _calculate_weighted_ranking_core(formula, history_data, stock_names, stock_codes)


def calculate_weighted_ranking_score_by_date(formula, date):
    """
    计算指定日期的股票加权排行分
    date: 交易日期
    """
    max_days = max([days for days, _ in formula]) if formula else 0
    need_days = max_days + 1

    # 使用优化后的数据加载
    history_data, stock_names, stock_codes = _load_history_data(date, need_days)

    return _calculate_weighted_ranking_core(formula, history_data, stock_names, stock_codes)


def get_weighted_rank_heatmap_data(formula, days=10):
    """
    获取加权排行分热力图数据
    返回: {date: {data: [stock1, stock2, ...], total_count: n}}
    """
    trade_dates = database.get_recent_trade_dates(days)

    heatmap = {}
    for date in trade_dates:
        ranking, _ = calculate_weighted_ranking_score_by_date(formula, date)
        heatmap[date] = {
            'data': ranking[:10],
            'total_count': len(ranking)
        }

    return heatmap