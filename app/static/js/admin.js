import { money } from "./icons.js";

const root = document.getElementById("admin-root");
let token = sessionStorage.getItem("payder-admin") || "";

function errorText(payload) {
  const detail = payload?.detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg || item).join(", ");
  return detail || "Ошибка";
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Admin-Token": token,
      ...(options.headers || {}),
    },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(errorText(payload));
  return payload;
}

function loginView(error = "") {
  root.innerHTML = `
    <form class="panel admin-login" id="login">
      <p class="eyebrow">АДМИН-ПАНЕЛЬ</p>
      <h1 style="font-size:28px;margin:8px 0 18px">Payder</h1>
      <p class="preview-note" style="text-align:left;margin:0 0 16px">Пароль задаётся в файле .env как ADMIN_PASSWORD</p>
      <label>Пароль
        <input name="password" type="password" required autocomplete="current-password">
      </label>
      ${error ? `<p class="field-error">${error}</p>` : ""}
      <button class="primary-button full">Войти</button>
    </form>`;
}

function table(title, headers, rowsHtml, emptyText) {
  return `
    <h2 style="margin:28px 0 12px;font-size:22px">${title}</h2>
    <table class="admin-table">
      <thead><tr>${headers.map((item) => `<th>${item}</th>`).join("")}</tr></thead>
      <tbody>${rowsHtml || `<tr><td class="admin-empty" colspan="${headers.length}">${emptyText}</td></tr>`}</tbody>
    </table>`;
}

async function dashboard() {
  const [cards, users, helps] = await Promise.all([
    request("/api/admin/cards"),
    request("/api/admin/users"),
    request("/api/admin/helps"),
  ]);
  root.innerHTML = `
    <p class="eyebrow">АДМИН-ПАНЕЛЬ</p>
    <div class="admin-toolbar screen-heading">
      <h1>Модерация Payder</h1>
      <button class="secondary-button" id="logout">Выйти</button>
    </div>
    ${table(
      "Карточки",
      ["ID", "Сумма", "Категория", "Автор", "Статус", ""],
      cards
        .map(
          (card) => `<tr>
            <td>${card.public_id}</td>
            <td>${money(card.amount)}</td>
            <td>${card.category}</td>
            <td>${card.author}</td>
            <td><span class="${card.is_active ? "badge-on" : "badge-off"}">${card.is_active ? "активна" : "скрыта"}</span></td>
            <td><button class="secondary-button" data-toggle="${card.id}">${card.is_active ? "Скрыть" : "Показать"}</button></td>
          </tr>`
        )
        .join(""),
      "Карточек пока нет"
    )}
    ${table(
      "Пользователи",
      ["ID", "Имя", "Логин", "Банк"],
      users.map((user) => `<tr><td>${user.id}</td><td>${user.name}</td><td>@${user.username}</td><td>${user.bank}</td></tr>`).join(""),
      "Пользователей нет"
    )}
    ${table(
      "Помощь",
      ["ID", "Карточка", "Кто помог", "Сумма"],
      helps.map((item) => `<tr><td>${item.id}</td><td>${item.card}</td><td>${item.helper}</td><td>${money(item.amount)}</td></tr>`).join(""),
      "Записей о помощи нет"
    )}`;
}

root.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (event.target.id !== "login") return;
  const password = new FormData(event.target).get("password");
  try {
    const result = await request("/api/admin/login", {
      method: "POST",
      body: JSON.stringify({ password }),
      headers: { "Content-Type": "application/json" },
    });
    token = result.token;
    sessionStorage.setItem("payder-admin", token);
    await dashboard();
  } catch (error) {
    loginView(error.message);
  }
});

root.addEventListener("click", async (event) => {
  if (event.target.id === "logout") {
    token = "";
    sessionStorage.removeItem("payder-admin");
    loginView();
    return;
  }
  const toggle = event.target.closest("[data-toggle]");
  if (toggle) {
    await request(`/api/admin/cards/${toggle.dataset.toggle}/toggle`, { method: "POST" });
    await dashboard();
  }
});

if (token) {
  dashboard().catch(() => loginView());
} else {
  loginView();
}
