from flask import Flask
from routes import contents, user  # 라우트 파일 import
from flask_cors import CORS

app = Flask(__name__)

CORS(app)

# 블루프린트 등록
app.register_blueprint(contents.bp)
# app.register_blueprint(user.bp)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)