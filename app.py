# 1. Flaskという「Webアプリを作るための便利道具」をこのファイルにインポート（取り込み）しています
from flask import Flask,render_template,request
# 2. Flaskアプリの本体を作成し、「app」という名前の変数（入れ物）に入れています
app = Flask(__name__)


# 3. 「ホームページ（一番最初の画面）」にアクセスされたときの処理を定義しています
@app.route("/",methods=["GET","POST"])
def hello():

    keyword = ""
    title = ""
    article = ""
    #クイズ用の変数 
    quiz_question = ""
    quiz_choices = []
    quiz_answer = ""
    result_message = ""#結果を画面に表示する変数

    # 4. ボタン（POST)が押されたらデータを受け取って画面に表示する処理をします
    if request.method == "POST":

        keyword = request.form.get("keyword")
        print(f"★受け取ったキーワード:({keyword})")
  

         #ボタンが押されたら画面に表示するための固定データをセットする
         #キーワードがnoneの場合は、記事とデータをセット
        if keyword:
            title = f"{keyword}とは？初心者向けに解説"
            article = f"ここでは{keyword}について初心者向けに解説します。"
           #クイズを出す
            quiz_question = f"{keyword}に関するクイズです。正しい答えを選んでください。"
            quiz_choices = ["選択肢1", "選択肢2", "選択肢3", "選択肢4"]
            quiz_answer = "選択肢1"  # 正解の選択肢を設定

            #ユーザーの選択を取得
            user_choice = request.form.get("user_choice")

            #ユーザーの選択がある場合、正解かどうかを判定
            if user_choice:
                if user_choice == quiz_answer:
                    result_message = "正解です！"
                else:
                    result_message = f"不正解です。正解は「{quiz_answer}」です。"

    #HTMLファイルに変数を渡して表示する
    return render_template("index.html", keyword=keyword, title=title, article=article, quiz_question=quiz_question, quiz_choices=quiz_choices, quiz_answer=quiz_answer, result_message=result_message)

# 5. このファイルが直接実行されたときに、Webサーバーを起動するおまじないです
if __name__ == "__main__":
    # 6. デバッグモード（エラーがあったら教えてくれる親切モード）でサーバーを動かします
    app.run(debug=True)