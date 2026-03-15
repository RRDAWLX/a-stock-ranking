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
    print(f"后端服务运行在端口: {port}")
    app.run(debug=True, host='0.0.0.0', port=port)