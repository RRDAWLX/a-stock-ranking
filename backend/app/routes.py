from flask import Blueprint, request, jsonify
from app import database, data_fetcher, calculator
import threading

api = Blueprint('api', __name__)

# 更新任务状态（线程安全）
update_task_lock = threading.Lock()
update_task = {
    'running': False,
    'progress': 0,
    'message': '',
    'error': None
}

# 输入验证常量
MAX_FORMULA_ITEMS = 10
MIN_DAYS = 1
MAX_DAYS = 365


def validate_formula(formula_spec, require_weight_sum=False):
    """验证公式参数

    Args:
        formula_spec: 公式列表 [{"days": 1, "weight": 0.5}, ...]
        require_weight_sum: 是否要求权重总和为1.0

    Returns:
        (is_valid, error_message)
    """
    if not formula_spec:
        return False, '公式不能为空'

    if not isinstance(formula_spec, list):
        return False, '公式格式错误'

    if len(formula_spec) > MAX_FORMULA_ITEMS:
        return False, f'公式项数不能超过{MAX_FORMULA_ITEMS}'

    total_weight = 0
    for item in formula_spec:
        if not isinstance(item, dict):
            return False, '公式项格式错误'

        days = item.get('days')
        weight = item.get('weight')

        if days is None or weight is None:
            return False, '公式项缺少days或weight字段'

        if not isinstance(days, int) or days < MIN_DAYS or days > MAX_DAYS:
            return False, f'天数必须在{MIN_DAYS}-{MAX_DAYS}之间'

        if not isinstance(weight, (int, float)) or weight < 0 or weight > 1:
            return False, '权重必须在0-1之间'

        total_weight += weight

    if require_weight_sum and abs(total_weight - 1.0) > 0.01:
        return False, '权重总和必须为1.0'

    return True, None


def api_success(data=None):
    """返回成功的API响应"""
    response = {'success': True}
    if data is not None:
        response['data'] = data
    return jsonify(response)


def api_error(code, message, status_code=400):
    """返回错误的API响应"""
    return jsonify({
        'success': False,
        'error': {'code': code, 'message': message}
    }), status_code


def run_update_async():
    """异步执行数据更新"""
    global update_task
    with update_task_lock:
        update_task['running'] = True
        update_task['progress'] = 0
        update_task['message'] = '开始更新...'
        update_task['error'] = None

    # 创建进度回调函数
    def update_progress(progress):
        with update_task_lock:
            update_task['progress'] = progress

    try:
        with update_task_lock:
            update_task['message'] = '正在更新...'
            update_task['progress'] = 50
        success = data_fetcher.incremental_update(update_progress)
        with update_task_lock:
            if success:
                update_task['message'] = '更新完成'
                update_task['progress'] = 100
            else:
                update_task['error'] = '更新失败'
    except Exception as e:
        with update_task_lock:
            update_task['error'] = str(e)
    finally:
        with update_task_lock:
            update_task['running'] = False


@api.route('/api/init-status', methods=['GET'])
def init_status():
    """获取初始化状态"""
    status = database.get_init_status()
    completeness = database.get_data_completeness()
    status.update(completeness)
    return api_success(status)


@api.route('/api/data-completeness', methods=['GET'])
def get_data_completeness():
    """获取数据完整性状态"""
    completeness = database.get_data_completeness()
    return api_success(completeness)


@api.route('/api/weighted-return/calculate', methods=['POST'])
def calculate_weighted_return():
    """根据自定义公式计算加权收益并返回排行"""
    data = request.get_json()

    if not data:
        return api_error('INVALID_REQUEST', '无效的请求数据')

    formula_spec = data.get('formula', [])

    # 使用默认公式时跳过验证
    if not formula_spec:
        formula_spec = [
            {'days': 1, 'weight': 0.1},
            {'days': 5, 'weight': 0.4},
            {'days': 20, 'weight': 0.5}
        ]
    else:
        is_valid, error_msg = validate_formula(formula_spec, require_weight_sum=False)
        if not is_valid:
            return api_error('INVALID_FORMULA', error_msg)

    formula = [(item['days'], item['weight']) for item in formula_spec]

    # 验证limit参数
    limit = data.get('limit')
    if limit is not None:
        if not isinstance(limit, int) or limit < 1:
            return api_error('INVALID_LIMIT', 'limit必须为正整数')

    results, total_count = calculator.calculate_all_stocks(formula)

    if limit:
        results = results[:limit]

    return api_success({
        'formula': formula_spec,
        'total': len(results),
        'total_count': total_count,
        'items': results
    })


@api.route('/api/weighted-return/heatmap', methods=['POST'])
def get_weighted_return_heatmap():
    """获取加权收益热力图数据"""
    data = request.get_json() or {}

    formula_spec = data.get('formula', [])

    if not formula_spec:
        formula_spec = [
            {'days': 1, 'weight': 0.1},
            {'days': 5, 'weight': 0.4},
            {'days': 20, 'weight': 0.5}
        ]
    else:
        is_valid, error_msg = validate_formula(formula_spec, require_weight_sum=False)
        if not is_valid:
            return api_error('INVALID_FORMULA', error_msg)

    formula = [(item['days'], item['weight']) for item in formula_spec]

    # 验证days参数
    days = data.get('days', 10)
    if not isinstance(days, int) or days < 1 or days > 100:
        return api_error('INVALID_DAYS', 'days必须在1-100之间')

    heatmap_data = calculator.get_heatmap_data(formula, days)

    dates = list(heatmap_data.keys())
    total_count = heatmap_data[dates[-1]]['total_count'] if dates else 0
    heatmap_items = {date: item['data'] for date, item in heatmap_data.items()}

    return api_success({
        'formula': formula_spec,
        'dates': dates,
        'total_count': total_count,
        'items': heatmap_items
    })


@api.route('/api/update-data', methods=['POST'])
def update_data():
    """手动触发数据更新（异步）"""
    global update_task

    with update_task_lock:
        if update_task['running']:
            return api_error('TASK_RUNNING', '已有更新任务在运行中')

        thread = threading.Thread(target=run_update_async)
        thread.start()

    return api_success({'message': '更新任务已启动', 'async': True})


@api.route('/api/update-status', methods=['GET'])
def get_update_status():
    """获取更新任务状态"""
    global update_task
    with update_task_lock:
        return api_success({
            'running': update_task['running'],
            'progress': update_task['progress'],
            'message': update_task['message'],
            'error': update_task['error']
        })


@api.route('/api/cancel-update', methods=['POST'])
def cancel_update():
    """取消/重置更新任务"""
    global update_task
    with update_task_lock:
        update_task['running'] = False
        update_task['progress'] = 0
        update_task['message'] = ''
        update_task['error'] = None
    return api_success({'message': '更新任务已取消'})


@api.route('/api/latest-date', methods=['GET'])
def latest_date():
    """获取最新交易日期"""
    date = calculator.get_latest_trading_date()
    return api_success({'date': date})


@api.route('/api/weighted-rank/calculate', methods=['POST'])
def calculate_weighted_rank():
    """根据自定义公式计算加权收益排行分"""
    data = request.get_json()

    if not data:
        return api_error('INVALID_REQUEST', '无效的请求数据')

    formula_spec = data.get('formula', [])

    # 加权排行分必须提供公式且权重总和为1
    is_valid, error_msg = validate_formula(formula_spec, require_weight_sum=True)
    if not is_valid:
        return api_error('INVALID_FORMULA', error_msg)

    formula = [(item['days'], item['weight']) for item in formula_spec]

    limit = data.get('limit')
    if limit is not None:
        if not isinstance(limit, int) or limit < 1:
            return api_error('INVALID_LIMIT', 'limit必须为正整数')

    results, total_count = calculator.calculate_weighted_ranking_score(formula)

    if limit:
        results = results[:limit]

    return api_success({
        'formula': formula_spec,
        'total': len(results),
        'total_count': total_count,
        'items': results
    })


@api.route('/api/weighted-rank/heatmap', methods=['POST'])
def get_weighted_rank_heatmap():
    """获取加权排行分热力图数据"""
    data = request.get_json() or {}

    formula_spec = data.get('formula', [])

    if not formula_spec:
        formula_spec = [
            {'days': 1, 'weight': 0.1},
            {'days': 5, 'weight': 0.4},
            {'days': 20, 'weight': 0.5}
        ]
    else:
        is_valid, error_msg = validate_formula(formula_spec, require_weight_sum=False)
        if not is_valid:
            return api_error('INVALID_FORMULA', error_msg)

    formula = [(item['days'], item['weight']) for item in formula_spec]

    days = data.get('days', 10)
    if not isinstance(days, int) or days < 1 or days > 100:
        return api_error('INVALID_DAYS', 'days必须在1-100之间')

    heatmap_data = calculator.get_weighted_rank_heatmap_data(formula, days)

    dates = list(heatmap_data.keys())
    total_count = heatmap_data[dates[-1]]['total_count'] if dates else 0
    heatmap_items = {date: item['data'] for date, item in heatmap_data.items()}

    return api_success({
        'formula': formula_spec,
        'dates': dates,
        'total_count': total_count,
        'items': heatmap_items
    })