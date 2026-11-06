import { escapeHtml, icon, money } from "../icons.js";

const FALLBACK_COLORS = {
  Образование: "#BFDBFE",
  Техника: "#D9F99D",
  Здоровье: "#FDE68A",
  "Доброе дело": "#FBCFE8",
  Творчество: "#FED7AA",
  Другое: "#E7E5E4",
};

export function cardColor(category, colors = {}) {
  return colors[category] || FALLBACK_COLORS[category] || "#D9F99D";
}

export function shortName(name) {
  const parts = String(name || "").split(" ").filter(Boolean);
  if (parts.length < 2) return name || "Алексей М.";
  return `${parts[0]} ${parts[1][0]}.`;
}

export function renderCreate({ form, previewId, categories, colors, profile, error, submitting }) {
  const amount = Number(String(form.amount || "").replace(/\D/g, "")) || 0;
  const purpose = form.purpose || "";
  const category = form.category || categories[0];
  const canSubmit = amount > 0 && purpose.trim().length >= 10 && !submitting;
  const color = cardColor(category, colors);

  return `
    <section class="screen content-screen">
      <div class="screen-heading">
        <div>
          <p class="eyebrow">НОВЫЙ ЗАПРОС</p>
          <h1>Создать карточку</h1>
        </div>
      </div>
      <div class="create-grid">
        <form class="panel create-form" data-form="create">
          <div class="step">
            <span>1</span>
            <div>
              <strong>Расскажите о запросе</strong>
              <small>Коротко и понятно — так больше шансов получить помощь</small>
            </div>
          </div>
          <label>Какая сумма вам нужна?
            <div class="amount-input">
              <input inputmode="numeric" name="amount" placeholder="10 000" value="${escapeHtml(form.amount || "")}" required>
              <span>₽</span>
            </div>
          </label>
          <label>На что нужны деньги?
            <textarea name="purpose" placeholder="Например: на оплату курса по дизайну..." minlength="10" maxlength="160" required>${escapeHtml(purpose)}</textarea>
            <small class="char-count" data-char-count>${purpose.length} / 160</small>
          </label>
          <label>Категория
            <select name="category">
              ${categories.map((item) => `<option ${item === category ? "selected" : ""}>${escapeHtml(item)}</option>`).join("")}
            </select>
          </label>
          <div class="notice">
            ${icon("wallet", 21)}
            <p>
              <strong>Ваши реквизиты защищены</strong>
              <span>Их увидят только пользователи, которые свайпнут карточку вправо.</span>
            </p>
          </div>
          ${error ? `<p class="field-error">${escapeHtml(error)}</p>` : ""}
          <button class="primary-button full" data-submit-create ${canSubmit ? "" : "disabled"}>${submitting ? "Публикуем..." : "Опубликовать карточку"}</button>
        </form>
        <div class="preview-column">
          <p class="eyebrow">ПРЕДПРОСМОТР</p>
          <div class="request-card preview-card" data-preview-card style="background:${color}">
            <div class="card-top">
              <span class="card-id">${escapeHtml(previewId)}</span>
              <span class="category" data-preview-category>${escapeHtml(category)}</span>
            </div>
            <div class="card-content">
              <span class="amount-label">НУЖНА СУММА</span>
              <div class="amount ${amount ? "" : "placeholder-text"}" data-preview-amount>${amount ? money(amount) : "0 ₽"}</div>
              <div class="purpose-rule"></div>
              <p class="purpose ${purpose ? "" : "placeholder-text"}" data-preview-purpose>${escapeHtml(purpose) || "Здесь появится описание вашей цели"}</p>
            </div>
            <div class="card-author">
              <span class="author-avatar">${escapeHtml(profile?.initials || "АМ")}</span>
              <div>
                <span>Автор запроса</span>
                <strong>${escapeHtml(shortName(profile?.name || "Алексей М."))}</strong>
              </div>
            </div>
          </div>
          <p class="preview-note">Так вашу карточку увидят другие пользователи</p>
        </div>
      </div>
    </section>`;
}
