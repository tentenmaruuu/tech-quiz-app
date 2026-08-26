# 1. Flaskという「Webアプリを作るための便利道具」をこのファイルにインポート（取り込み）しています
from flask import Flask,render_template

# 2. Flaskアプリの本体を作成し、「app」という名前の変数（入れ物）に入れています
app = Flask(__name__)


# 3. 「ホームページ（一番最初の画面）」にアクセスされたときの処理を定義しています
@app.route("/")
def hello():
    # 4. ブラウザに「Hello, Tech Quiz App!」という文字を返して表示させます
    return render_template("index.html")



# 5. このファイルが直接実行されたときに、Webサーバーを起動するおまじないです
if __name__ == "__main__":
    # 6. デバッグモード（エラーがあったら教えてくれる親切モード）でサーバーを動かします
    app.run(debug=True)