import json
import os
from app.main import create_app

def get_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

if __name__ == '__main__':
    config = get_config()
    app = create_app()
    port = config['backend']['port']
    # 通过环境变量控制 debug 模式，生产环境应设置 FLASK_DEBUG=0 或不设置
    debug = os.environ.get('FLASK_DEBUG', '1').lower() in ('1', 'true', 'yes')
    print(f"后端服务运行在端口: {port} (debug={debug})")
    app.run(debug=debug, host='0.0.0.0', port=port)