from flask import Flask
from flask_cors import CORS
from app import database, routes

app = Flask(__name__)
CORS(app)

# 注册路由
app.register_blueprint(routes.api)


@app.route('/')
def index():
    return {'message': 'A股股票收益排行系统 API', 'version': '1.0'}


def create_app():
    # 初始化数据库
    database.init_db()
    return app