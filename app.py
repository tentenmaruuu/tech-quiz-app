import json
import os
import random
import re
import secrets
import urllib.error
import urllib.parse
import urllib.request

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for
import google.generativeai as genai

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))

GEMINI_API_KEY_ENV = "GEMINI_API_KEY"
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
MODEL_ALIASES = {
    "gemini-3.6": "gemini-3.6-flash",
}


def build_fallback_content(keyword):
    title = f"{keyword}とは？初心者向けに解説"
    article = (
        f"{keyword}は、ITやプログラミングを理解するときに重要になる技術用語です。"
        "まずは「何のために使うのか」「どんな場面で登場するのか」を押さえると、"
        "細かい仕組みも理解しやすくなります。"
    )
    quiz_specs = [
        (
            f"{keyword}を学ぶとき、最初に意識するとよいことはどれですか？",
            f"{keyword}が何のために使われる技術なのか",
            "目的と利用場面を先に押さえると、細かな仕組みを理解しやすくなります。",
        ),
        (
            f"{keyword}の理解を深めるために有効な進め方はどれですか？",
            f"{keyword}が使われる具体例を確認する",
            "具体例と結びつけることで、用語の意味を実務やコード上の動きとして捉えられます。",
        ),
        (
            f"{keyword}を説明するときに重要な観点はどれですか？",
            f"{keyword}によって解決したい課題",
            "技術用語は、解決したい課題とセットで理解すると記憶に残りやすくなります。",
        ),
    ]
    distractors = [
        "すべての専門用語を丸暗記すること",
        "エラーや警告を読み飛ばすこと",
        "公式ドキュメントを一切見ないこと",
        "動作確認をせずに推測だけで進めること",
        "関連する概念をすべて同じ意味として扱うこと",
        "用語の目的より先に設定値だけを覚えること",
    ]
    questions = [
        build_question(question_text, correct_choice, explanation, distractors)
        for question_text, correct_choice, explanation in quiz_specs
    ]
    return {"title": title, "article": article, "questions": questions}


def build_question(question_text, correct_choice, explanation, distractors):
    choices = [correct_choice, *random.sample(distractors, 3)]
    random.shuffle(choices)
    return {
        "question": question_text,
        "choices": choices,
        "answer_index": choices.index(correct_choice),
        "explanation": explanation,
    }


def extract_json(text):
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.DOTALL)
    if fenced:
        cleaned = fenced.group(1).strip()
    else:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


def generate_with_gemini(keyword):
    api_key = os.environ.get(GEMINI_API_KEY_ENV)
    if not api_key:
        fallback = build_fallback_content(keyword)
        fallback["notice"] = (
            "GEMINI_API_KEY が未設定のため、サンプル内容を表示しています。"
        )
        return fallback

    prompt = f"""
技術用語「{keyword}」について、日本語の初心者向け学習コンテンツを作ってください。
必ず次のJSON形式だけで返してください。Markdownや説明文は不要です。

{{
  "title": "記事タイトル",
  "article": "500文字程度の解説本文。段落は\\nで区切る。",
  "questions": [
    {{
      "question": "4択クイズの問題文",
      "choices": ["選択肢A", "選択肢B", "選択肢C", "選択肢D"],
      "answer_index": 0,
      "explanation": "正解の理由"
    }}
  ]
}}

クイズは3問作成してください。answer_indexは0から3の整数にしてください。
各問題は、技術用語「{keyword}」の内容に直接関係する正解1つと不正解3つにしてください。
不正解の選択肢も自然な日本語にしつつ、正解と同じ意味にならないようにしてください。
"""
    model_path = urllib.parse.quote(normalize_model_name(GEMINI_MODEL), safe="")
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model_path}:generateContent?key={urllib.parse.quote(api_key)}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"response_mime_type": "application/json"},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=40) as response:
            body = json.loads(response.read().decode("utf-8"))
        text = body["candidates"][0]["content"]["parts"][0]["text"]
        content = normalize_content(extract_json(text))
        validate_content(content)
        return content
    except (
        KeyError,
        ValueError,
        json.JSONDecodeError,
        urllib.error.HTTPError,
        urllib.error.URLError,
    ) as exc:
        fallback = build_fallback_content(keyword)
        fallback["notice"] = f"AI生成に失敗したため、代替問題を表示しています: {format_gemini_error(exc)}"
        return fallback


def format_gemini_error(exc):
    if isinstance(exc, urllib.error.HTTPError):
        detail = exc.read().decode("utf-8", errors="replace")
        try:
            message = json.loads(detail)["error"]["message"]
        except (KeyError, json.JSONDecodeError):
            message = detail[:200]
        return f"HTTP {exc.code} {message}"
    return str(exc)


def normalize_model_name(model_name):
    normalized = model_name.removeprefix("models/").strip()
    return MODEL_ALIASES.get(normalized, normalized)


def normalize_content(content):
    normalized_questions = []
    for question in content.get("questions", []):
        choices = question.get("choices") or question.get("options")
        answer_index = question.get("answer_index")

        if answer_index is None and "correct_answer_index" in question:
            answer_index = question["correct_answer_index"]

        if isinstance(answer_index, str) and answer_index.isdigit():
            answer_index = int(answer_index)

        if answer_index is None:
            correct_answer = question.get("answer") or question.get("correct_answer")
            if isinstance(correct_answer, str) and isinstance(choices, list):
                answer_index = next(
                    (
                        index
                        for index, choice in enumerate(choices)
                        if str(choice).strip() == correct_answer.strip()
                    ),
                    None,
                )

        normalized_questions.append(
            {
                "question": str(question.get("question", "")).strip(),
                "choices": (
                    [str(choice).strip() for choice in choices]
                    if isinstance(choices, list)
                    else choices
                ),
                "answer_index": answer_index,
                "explanation": str(question.get("explanation", "")).strip(),
            }
        )

    return {
        "title": str(content.get("title", "")).strip(),
        "article": str(content.get("article", "")).strip(),
        "questions": normalized_questions,
    }


def validate_content(content):
    if not isinstance(content.get("title"), str) or not content["title"].strip():
        raise ValueError("title is missing")
    if not isinstance(content.get("article"), str) or not content["article"].strip():
        raise ValueError("article is missing")
    questions = content.get("questions")
    if not isinstance(questions, list) or not questions:
        raise ValueError("questions are missing")
    for question in questions:
        choices = question.get("choices")
        answer_index = question.get("answer_index")
        if not isinstance(question.get("question"), str):
            raise ValueError("question text is invalid")
        if not isinstance(choices, list) or len(choices) != 4:
            raise ValueError("choices must contain four items")
        if any(not isinstance(choice, str) or not choice.strip() for choice in choices):
            raise ValueError("choice text is invalid")
        if len({choice.strip() for choice in choices}) != 4:
            raise ValueError("choices must be unique")
        if not isinstance(answer_index, int) or answer_index not in range(4):
            raise ValueError("answer_index must be 0-3")


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/article")
def article():
    keyword = request.form.get("keyword", "").strip()
    if not keyword:
        flash("技術用語を入力してください。")
        return redirect(url_for("index"))

    content = generate_with_gemini(keyword)
    session["keyword"] = keyword
    session["content"] = content
    return render_template("article.html", keyword=keyword, content=content)


@app.post("/result")
def result():
    content = session.get("content")
    if not content:
        flash("先に技術用語を入力して記事を作成してください。")
        return redirect(url_for("index"))

    questions = content["questions"]
    results = []
    score = 0
    for index, question in enumerate(questions):
        selected_raw = request.form.get(f"q{index}")
        selected_index = int(selected_raw) if selected_raw and selected_raw.isdigit() else None
        correct_index = question["answer_index"]
        is_correct = selected_index == correct_index
        score += int(is_correct)
        results.append(
            {
                "question": question["question"],
                "choices": question["choices"],
                "selected_index": selected_index,
                "correct_index": correct_index,
                "is_correct": is_correct,
                "explanation": question.get("explanation", ""),
            }
        )

    return render_template(
        "result.html",
        keyword=session.get("keyword", ""),
        score=score,
        total=len(questions),
        results=results,
    )


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
