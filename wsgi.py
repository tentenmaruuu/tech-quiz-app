from waitress import serve
from app import app  # app.py から Flask の app を読み込む

if __name__ == '__main__':
    # print の中身をシンプルな文字列だけにする（またはこの行を消す）
    print("Server started") 
    
    # サーバーを起動
    serve(app, host='0.0.0.0', port=5000)
