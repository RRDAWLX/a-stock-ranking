from flask import Blueprint, request, jsonify
from app import database, data_fetcher, calculator
import threading

api = Blueprint('api', __name__)

# 更新任务状态
update_task = {
    'running': False,
    'progress': 0,
    'message': '',
    'error': None
}


def run_update_async():
    """异步执行数据更新"""
    global update_task
    update_task['running'] = True
    update_task['progress'] = 0
    update_task['message'] = '开始更新...'
    update_task['error'] = None

    # 创建进度回调函数
    def update_progress(progress):
        update_task['progress'] = progress

    try:
        update_task['message'] = '正在更新...'
        update_task['progress'] = 50
        success = data_fetcher.incremental_update(update_progress)
        if success:
            update_task['message'] = '更新完成'
            update_task['progress'] = 100
        else:
            update_task['error'] = '更新失败'
    except Exception as e:
        update_task['error'] = str(e)
    finally:
        update_task['running'] = False


@api.route('/api/init-status', methods=['GET'])
def init_status():
    """获取初始化状态"""
    status = database.get_init_status()
    # 添加数据完整性信息
    completeness = database.get_data_completeness()
    status.update(completeness)
    return jsonify(status)


@api.route('/api/data-completeness', methods=['GET'])
def get_data_completeness():
    """获取数据完整性状态"""
    completeness = database.get_data_completeness()
    return jsonify(completeness)


@api.route('/api/weighted-return/calculate', methods=['POST'])
def calculate_weighted_return():
    """根据自定义公式计算加权收益并返回排行"""
    data = request.get_json()

    if not data:
        return jsonify({'error': '无效的请求数据'}), 400

    # 解析公式: [{"days": 1, "weight": 0.1}, {"days": 5, "weight": 0.4}, ...]
    formula_spec = data.get('formula', [])
    if not formula_spec:
        # 使用默认公式
        formula_spec = [
            {'days': 1, 'weight': 0.1},
            {'days': 5, 'weight': 0.4},
            {'days': 20, 'weight': 0.5}
        ]

    # 转换为计算器需要的格式
    formula = [(item['days'], item['weight']) for item in formula_spec]

    # 可选参数: limit
    limit = data.get('limit')

    # 计算所有股票收益
    results, total_count = calculator.calculate_all_stocks(formula)

    # 如果指定了limit
    if limit:
        results = results[:limit]

    return jsonify({
        'formula': formula_spec,
        'total': len(results),
        'total_count': total_count,
        'data': results
    })


@api.route('/api/weighted-return/heatmap', methods=['POST'])
def get_weighted_return_heatmap():
    """获取加权收益热力图数据"""
    data = request.get_json() or {}

    # 解析公式
    formula_spec = data.get('formula', [])
    if not formula_spec:
        formula_spec = [
            {'days': 1, 'weight': 0.1},
            {'days': 5, 'weight': 0.4},
            {'days': 20, 'weight': 0.5}
        ]

    formula = [(item['days'], item['weight']) for item in formula_spec]
    days = data.get('days', 10)

    heatmap_data = calculator.get_heatmap_data(formula, days)

    # 获取最新日期的参与股票数量
    dates = list(heatmap_data.keys())
    total_count = heatmap_data[dates[-1]]['total_count'] if dates else 0

    # 转换数据格式，保持向后兼容
    data = {date: item['data'] for date, item in heatmap_data.items()}

    return jsonify({
        'formula': formula_spec,
        'dates': dates,
        'total_count': total_count,
        'data': data
    })


@api.route('/api/update-data', methods=['POST'])
def update_data():
    """手动触发数据更新（异步）"""
    global update_task

    if update_task['running']:
        return jsonify({
            'success': False,
            'message': '已有更新任务在运行中'
        }), 400

    # 启动异步更新任务
    thread = threading.Thread(target=run_update_async)
    thread.start()

    return jsonify({
        'success': True,
        'message': '更新任务已启动',
        'async': True
    })


@api.route('/api/update-status', methods=['GET'])
def get_update_status():
    """获取更新任务状态"""
    global update_task
    return jsonify({
        'running': update_task['running'],
        'progress': update_task['progress'],
        'message': update_task['message'],
        'error': update_task['error']
    })


@api.route('/api/cancel-update', methods=['POST'])
def cancel_update():
    """取消/重置更新任务"""
    global update_task
    update_task['running'] = False
    update_task['progress'] = 0
    update_task['message'] = ''
    update_task['error'] = None
    return jsonify({
        'success': True,
        'message': '更新任务已取消'
    })


@api.route('/api/latest-date', methods=['GET'])
def latest_date():
    """获取最新交易日期"""
    date = calculator.get_latest_trading_date()
    return jsonify({'date': date})


@api.route('/api/weighted-rank/calculate', methods=['POST'])
def calculate_weighted_rank():
    """根据自定义公式计算加权收益排行分"""
    data = request.get_json()

    if not data:
        return jsonify({'error': '无效的请求数据'}), 400

    # 解析公式: [{"days": 1, "weight": 0.5}, {"days": 20, "weight": 0.5}, ...]
    formula_spec = data.get('formula', [])
    if not formula_spec:
        return jsonify({'error': '公式不能为空'}), 400

    # 验证权重总和
    total_weight = sum(item.get('weight', 0) for item in formula_spec)
    if abs(total_weight - 1.0) > 0.01:
        return jsonify({'error': '权重总和必须为1.0'}), 400

    # 转换为计算器需要的格式
    formula = [(item['days'], item['weight']) for item in formula_spec]

    # 可选参数: limit
    limit = data.get('limit')

    # 计算所有股票加权排行分
    results, total_count = calculator.calculate_weighted_ranking_score(formula)

    # 如果指定了limit
    if limit:
        results = results[:limit]

    return jsonify({
        'formula': formula_spec,
        'total': len(results),
        'total_count': total_count,
        'data': results
    })


@api.route('/api/weighted-rank/heatmap', methods=['POST'])
def get_weighted_rank_heatmap():
    """获取加权排行分热力图数据"""
    data = request.get_json() or {}

    # 解析公式
    formula_spec = data.get('formula', [])
    if not formula_spec:
        formula_spec = [
            {'days': 1, 'weight': 0.1},
            {'days': 5, 'weight': 0.4},
            {'days': 20, 'weight': 0.5}
        ]

    formula = [(item['days'], item['weight']) for item in formula_spec]
    days = data.get('days', 10)

    heatmap_data = calculator.get_weighted_rank_heatmap_data(formula, days)

    # 获取最新日期的参与股票数量
    dates = list(heatmap_data.keys())
    total_count = heatmap_data[dates[-1]]['total_count'] if dates else 0

    # 转换数据格式，保持向后兼容
    data = {date: item['data'] for date, item in heatmap_data.items()}

    return jsonify({
        'formula': formula_spec,
        'dates': dates,
        'total_count': total_count,
        'data': data
    })