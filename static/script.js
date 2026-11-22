const HISTORY_KEY = "tech_quiz_history";
const MAX_HISTORY = 5;

function initPage() {
  const firstInput = document.querySelector("input[name='keyword']");
  if (firstInput) {
    firstInput.focus();
  }

  initSearchHistory();
  initInstantQuizFeedback();

  document.querySelectorAll("form").forEach((form) => {
    form.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && e.target.tagName !== "TEXTAREA") {
        e.preventDefault();
        form.requestSubmit();
      }
    });

    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      const formData = new FormData(form);
      const keyword = String(formData.get("keyword") || "").trim();
      if (keyword) {
        saveSearchHistory(keyword);
      }

      const button = form.querySelector("button[type='submit']");
      if (button) {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.textContent = "処理中...";
      }

      showLoading("Geminiが解説記事とクイズを作成中…");

      try {
        const response = await fetch(form.action, {
          method: form.method || "POST",
          body: formData,
          headers: {
            "X-Requested-With": "fetch",
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP Error ${response.status}`);
        }

        const html = await response.text();
        const nextDocument = new DOMParser().parseFromString(html, "text/html");
        document.title = nextDocument.title;
        document.body.innerHTML = nextDocument.body.innerHTML;
        hideLoading();
        initPage();
      } catch (error) {
        hideLoading();
        showFormError(form, error.message);
        if (button) {
          button.disabled = false;
          button.textContent = button.dataset.originalText || "送信";
        }
      }
    });
  });
}

function showLoading(message) {
  hideLoading();
  const overlay = document.createElement("div");
  overlay.className = "loading-overlay";
  overlay.setAttribute("role", "status");
  overlay.setAttribute("aria-live", "polite");

  const card = document.createElement("div");
  card.className = "loading-card";

  const spinner = document.createElement("div");
  spinner.className = "loading-spinner";

  const text = document.createElement("p");
  text.className = "loading-message";
  text.textContent = message;

  card.append(spinner, text);
  overlay.appendChild(card);
  document.body.appendChild(overlay);
}

function hideLoading() {
  document.querySelectorAll(".loading-overlay").forEach((el) => el.remove());
}

function getSearchHistory() {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.filter((item) => typeof item === "string" && item.trim()) : [];
  } catch {
    return [];
  }
}

function saveSearchHistory(keyword) {
  const next = [keyword, ...getSearchHistory().filter((item) => item !== keyword)].slice(0, MAX_HISTORY);
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(next));
  } catch {
    // localStorage が使えない環境では無視
  }
}

function initSearchHistory() {
  const container = document.getElementById("search-history");
  const listEl = container?.querySelector(".history-list");
  const form = document.querySelector(".search-form");
  const input = document.querySelector("input[name='keyword']");
  if (!container || !listEl || !form || !input) {
    return;
  }

  const history = getSearchHistory();
  if (history.length === 0) {
    container.hidden = true;
    return;
  }

  listEl.innerHTML = "";
  history.forEach((term) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "history-chip";
    btn.textContent = term;
    btn.addEventListener("click", () => {
      input.value = term;
      form.requestSubmit();
    });
    listEl.appendChild(btn);
  });
  container.hidden = false;
}

function showFormError(form, message) {
  const currentAlert = document.querySelector(".alert");
  const alert = currentAlert || document.createElement("div");
  alert.className = "alert";
  alert.setAttribute("role", "alert");
  alert.textContent = `通信に失敗しました。エンドポイントを確認してください: ${message}`;

  if (!currentAlert) {
    form.insertAdjacentElement("beforebegin", alert);
  }
}

function initInstantQuizFeedback() {
  const questions = document.querySelectorAll(".question");
  if (questions.length === 0) {
    return;
  }

  let answeredCount = 0;
  let correctCount = 0;
  const totalCount = questions.length;
  const summaryEl = document.querySelector(".score-summary");
  const summaryTitleEl = document.querySelector(".score-summary-title");
  const summaryLeadEl = document.querySelector(".score-summary-lead");

  questions.forEach((questionEl) => {
    const answerIndex = Number(questionEl.dataset.answerIndex);
    const explanation = questionEl.dataset.explanation || "";
    const feedbackEl = questionEl.querySelector(".question-feedback");
    const markEl = questionEl.querySelector(".feedback-mark");
    const explanationEl = questionEl.querySelector(".feedback-explanation");
    const choices = questionEl.querySelectorAll(".choice");

    questionEl.querySelectorAll("input[type='radio']").forEach((radio) => {
      radio.addEventListener("change", () => {
        if (questionEl.classList.contains("is-answered")) {
          return;
        }
        questionEl.classList.add("is-answered");

        const currentAnswerIndex = Number(questionEl.dataset.answerIndex);
        const selectedIndex = Number(radio.value);
        const isCorrect = selectedIndex === currentAnswerIndex;
        answeredCount += 1;
        if (isCorrect) {
          correctCount += 1;
        }

        questionEl.querySelectorAll(".choice").forEach((choiceEl, idx) => {
          if (idx === currentAnswerIndex) {
            choiceEl.classList.add("is-correct");
          } else if (idx === selectedIndex && !isCorrect) {
            choiceEl.classList.add("is-incorrect");
          }
        });

        if (feedbackEl && markEl && explanationEl) {
          feedbackEl.classList.toggle("correct", isCorrect);
          feedbackEl.classList.toggle("incorrect", !isCorrect);
          markEl.textContent = isCorrect ? "正解！" : "不正解";
          explanationEl.textContent = explanation;
          feedbackEl.hidden = false;
        }

        if (answeredCount === totalCount && summaryEl && summaryTitleEl && summaryLeadEl) {
          summaryTitleEl.textContent = `${correctCount} / ${totalCount} 問正解`;
          if (correctCount === totalCount) {
            summaryLeadEl.textContent = "すばらしい理解度です。記事の内容をしっかり押さえられています。";
          } else if (correctCount > 0) {
            summaryLeadEl.textContent = "惜しいです。解説を読み直すと、さらに定着します。";
          } else {
            summaryLeadEl.textContent = "ここから覚えていけば大丈夫です。解説と正解理由を確認しましょう。";
          }
          summaryEl.hidden = false;
        }
      });
    });
  });

  const retryBtn = document.getElementById("retry-quiz-btn");
  if (retryBtn) {
    retryBtn.addEventListener("click", () => {
      answeredCount = 0;
      correctCount = 0;
      if (summaryEl) {
        summaryEl.hidden = true;
      }

      questions.forEach((questionEl) => {
        questionEl.classList.remove("is-answered");
        const feedbackEl = questionEl.querySelector(".question-feedback");
        if (feedbackEl) {
          feedbackEl.hidden = true;
          feedbackEl.classList.remove("correct", "incorrect");
        }

        const choicesContainer = questionEl.querySelector(".choices");
        if (!choicesContainer) {
          return;
        }

        const currentAnswerIndex = Number(questionEl.dataset.answerIndex);
        const choiceItems = Array.from(choicesContainer.querySelectorAll(".choice")).map((el, idx) => ({
          el,
          isCorrect: idx === currentAnswerIndex,
        }));

        for (let i = choiceItems.length - 1; i > 0; i -= 1) {
          const j = Math.floor(Math.random() * (i + 1));
          [choiceItems[i], choiceItems[j]] = [choiceItems[j], choiceItems[i]];
        }

        choiceItems.forEach((item, newIdx) => {
          item.el.classList.remove("is-correct", "is-incorrect");
          const radio = item.el.querySelector("input[type='radio']");
          if (radio) {
            radio.checked = false;
            radio.value = String(newIdx);
          }
          if (item.isCorrect) {
            questionEl.dataset.answerIndex = String(newIdx);
          }
          choicesContainer.appendChild(item.el);
        });
      });

      questions[0].scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initPage();
});
