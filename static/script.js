function initPage() {
  const firstInput = document.querySelector("input[name='keyword']");
  if (firstInput) {
    firstInput.focus();
  }

  document.querySelectorAll("form").forEach((form) => {
    form.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && e.target.tagName !== "TEXTAREA") {
        e.preventDefault();
        form.requestSubmit();
      }
    });

    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      const button = form.querySelector("button[type='submit']");
      if (button) {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.textContent = "処理中...";
      }

      try {
        const response = await fetch(form.action, {
          method: form.method || "POST",
          body: new FormData(form),
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
        initPage();
      } catch (error) {
        showFormError(form, error.message);
        if (button) {
          button.disabled = false;
          button.textContent = button.dataset.originalText || "送信";
        }
      }
    });
  });
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

document.addEventListener("DOMContentLoaded", () => {
  initPage();
});
