import { api } from "./api.js";
import { escapeHtml, icon, money } from "./icons.js";
import { cardColor, renderCreate } from "./components/create.js";
import { renderFeed } from "./components/feed.js";
import { renderProfile } from "./components/profile.js";
import { renderStats } from "./components/stats.js";
import { renderDocsPanel, renderGate, renderLegalLinks, renderLegalReader } from "./components/legal.js";
import { LEGAL_VERSION } from "./legal.js";

const root = document.getElementById("root");
const SCREENS = ["feed", "profile", "stats", "create"];
const DEFAULT_MENU = [
  { id: "feed", label: "Карточки", icon: "cards" },
  { id: "profile", label: "Профиль", icon: "user" },
  { id: "stats", label: "Статистика", icon: "chart" },
  { id: "create", label: "Создать", icon: "plus" },
];

const CONSENT_KEY = "payder_consent";

// Принятие документов в этом браузере: действует, пока версия документов не изменилась.
function readConsent() {
  try {
    const saved = JSON.parse(window.localStorage.getItem(CONSENT_KEY) || "null");
    return saved && saved.version === LEGAL_VERSION ? saved : null;
  } catch {
    return null;
  }
}

function saveConsent() {
  state.consent = { version: LEGAL_VERSION, acceptedAt: new Date().toISOString() };
  try {
    window.localStorage.setItem(CONSENT_KEY, JSON.stringify(state.consent));
  } catch {
    /* без localStorage стартовый экран просто покажется снова */
  }
}

const state = {
  consent: readConsent(),
  gateOpen: false,
  gate: { terms: false, privacy: false },
  gateError: "",
  legalDoc: null,
  screen: screenFromHash(),
  authenticated: false,
  authMode: "login",
  authError: "",
  menu: DEFAULT_MENU,
  banks: ["Т-Банк", "Сбер", "Альфа-Банк", "ВТБ"],
  categories: ["Образование", "Техника", "Здоровье", "Доброе дело", "Творчество", "Другое"],
  colors: {},
  cards: [],
  index: 0,
  dragX: 0,
  pointerStart: null,
  animating: false,
  helped: null,
  toast: "",
  toastTimer: 0,
  profile: null,
  editing: false,
  stats: null,
  statsLoading: false,
  period: "month",
  form: { amount: "", purpose: "", category: "Образование" },
  previewId: makePreviewId(),
  loading: true,
  error: "",
  formError: "",
  submitting: false,
  deleting: false,
  deleteError: "",
  authNote: "",
};

// Настоящий id карточки выдаёт сервер (PD- и 10 случайных символов); это только вид для превью.
function makePreviewId() {
  const alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  const bytes = crypto.getRandomValues(new Uint8Array(10));
  return "PD-" + Array.from(bytes, (byte) => alphabet[byte % alphabet.length]).join("");
}

function screenFromHash() {
  const id = window.location.hash.replace("#", "");
  return SCREENS.includes(id) ? id : "feed";
}

function logo() {
  return `<div class="logo" aria-label="Payder"><span class="logo-mark">P</span><span>Payder</span></div>`;
}

function renderModal() {
  if (!state.helped) return "";
  const item = state.helped;
  return `
    <div class="modal-backdrop" data-close-modal>
      <div class="requisites-modal" data-modal-card>
        <button class="modal-close" data-close-modal aria-label="Закрыть">${icon("close", 20)}</button>
        <div class="success-icon">${icon("check", 27)}</div>
        <p class="eyebrow">ВЫ ВЫБРАЛИ ПОМОЧЬ</p>
        <h2>${escapeHtml(item.author)}</h2>
        <p class="modal-copy">Переведите любую комфортную сумму по реквизитам автора.</p>
        <div class="bank-row">
          <div class="bank-logo">${icon("wallet", 22)}</div>
          <div>
            <span>${escapeHtml(item.bank)}</span>
            <strong>${escapeHtml(item.requisites)}</strong>
          </div>
          <button data-copy="${escapeHtml(item.requisites)}" aria-label="Скопировать">${icon("copy", 20)}</button>
        </div>
        <button class="primary-button full" data-copy="${escapeHtml(item.requisites)}">Скопировать реквизиты</button>
        <button class="text-button" data-close-modal>Продолжить смотреть</button>
      </div>
    </div>`;
}

function renderPrivacy() {
  return `
    <section class="panel privacy-panel" style="margin-top:16px">
      <p class="eyebrow">ВАШИ ДАННЫЕ</p>
      <p class="preview-note" style="text-align:left;margin:8px 0 14px">Можно скачать всё, что мы о вас храним, или удалить аккаунт вместе с карточками и историей. Удаление необратимо.</p>
      ${
        state.deleting
          ? `<form data-form="delete" class="auth-form">
              <label>Введите пароль для подтверждения
                <input name="password" type="password" autocomplete="current-password" maxlength="128" required>
              </label>
              ${state.deleteError ? `<p class="field-error">${escapeHtml(state.deleteError)}</p>` : ""}
              <button class="primary-button full" type="submit">Удалить аккаунт навсегда</button>
              <button class="text-button" type="button" data-action="delete-cancel">Отмена</button>
            </form>`
          : `<button class="secondary-button" type="button" data-action="export-data">Скачать мои данные</button>
             <button class="text-button" type="button" data-action="delete-start">Удалить аккаунт</button>`
      }
    </section>`;
}

function renderAuth() {
  root.innerHTML = `
    <main class="auth-shell"><section class="auth-panel">
      <div class="logo"><span class="logo-mark">P</span><span>Payder</span></div>
      <p class="eyebrow">СООБЩЕСТВО ВЗАИМОПОМОЩИ</p>
      <h1>${state.authMode === "login" ? "С возвращением" : "Создать аккаунт"}</h1>
      <p class="auth-description">${state.authMode === "login" ? "Войдите, чтобы смотреть карточки и делиться своими запросами." : "Зарегистрируйтесь, чтобы публиковать карточки и видеть запросы других участников."}</p>
      ${state.authNote ? `<p class="auth-description">${escapeHtml(state.authNote)}</p>` : ""}
      <form data-form="auth" class="auth-form">
        ${state.authMode === "register" ? `<label>Ваше имя<input name="name" autocomplete="name" minlength="2" maxlength="120" required placeholder="Имя Фамилия"></label>` : ""}
        <label>Логин<input name="username" autocomplete="username" minlength="3" maxlength="64" required placeholder="Например, alex2026"></label>
        <label>Пароль<input name="password" type="password" autocomplete="${state.authMode === "login" ? "current-password" : "new-password"}" minlength="8" maxlength="128" required placeholder="Не менее 8 символов"></label>
        ${state.authError ? `<p class="field-error">${escapeHtml(state.authError)}</p>` : ""}
        <button class="primary-button full" type="submit">${state.authMode === "login" ? "Войти" : "Зарегистрироваться"}</button>
      </form>
      <button class="text-button auth-switch" data-action="toggle-auth">${state.authMode === "login" ? "Нет аккаунта? Зарегистрироваться" : "Уже есть аккаунт? Войти"}</button>
      ${renderLegalLinks()}
    </section></main>
    ${state.legalDoc ? renderLegalReader(state.legalDoc) : ""}`;
}

function renderGateScreen() {
  root.innerHTML = renderGate({
    gate: state.gate,
    legalDoc: state.legalDoc,
    error: state.gateError,
    account: state.authenticated,
  });
}

// Перерисовывает текущий экран (стартовый, вход или основное приложение).
function rerender() {
  if (state.gateOpen) renderGateScreen();
  else if (!state.authenticated) renderAuth();
  else render();
}

// Куда попадает человек, не вошедший в аккаунт: на стартовый экран или сразу к входу.
function showEntry() {
  state.gateOpen = !state.consent;
  if (state.gateOpen) {
    state.gate = { terms: false, privacy: false };
    state.gateError = "";
  }
  rerender();
}

function setLegalDoc(id) {
  state.legalDoc = id;
  document.body.style.overflow = id ? "hidden" : "";
  rerender();
}

async function acceptGate() {
  if (!(state.gate.terms && state.gate.privacy)) return;
  state.gateError = "";
  if (state.authenticated) {
    try {
      state.profile = await api.acceptDocuments(LEGAL_VERSION);
    } catch (error) {
      state.gateError = error.message;
      renderGateScreen();
      return;
    }
    saveConsent();
    state.gateOpen = false;
    await loadFeed();
    if (state.screen === "stats") await loadStats();
    return;
  }
  saveConsent();
  state.gateOpen = false;
  renderAuth();
}

function render() {
  if (state.gateOpen) { renderGateScreen(); return; }
  if (!state.authenticated) { renderAuth(); return; }
  const initials = state.profile?.initials || "АМ";
  const firstName = (state.profile?.name || "Алексей").split(" ")[0];
  const username = state.profile?.username || "alexmoroz";
  let screenHtml = "";
  if (state.screen === "feed") {
    screenHtml = renderFeed({
      cards: state.cards,
      index: state.index,
      dragX: state.dragX,
      dragging: state.pointerStart !== null,
      animating: state.animating,
      error: state.error,
      loading: state.loading,
    });
  } else if (state.screen === "profile") {
    screenHtml = renderProfile({
      profile: state.profile,
      editing: state.editing,
      banks: state.banks,
      error: state.formError,
      extra: renderDocsPanel() + renderPrivacy(),
    });
  } else if (state.screen === "stats") {
    screenHtml = renderStats({
      stats: state.stats,
      period: state.period,
      loading: state.statsLoading,
      error: state.error,
    });
  } else {
    screenHtml = renderCreate({
      form: state.form,
      previewId: state.previewId,
      categories: state.categories,
      colors: state.colors,
      profile: state.profile,
      error: state.formError,
      submitting: state.submitting,
    });
  }

  root.innerHTML = `
    <div class="app-shell">
      <aside class="sidebar">
        ${logo()}
        <nav class="side-nav" aria-label="Основная навигация">
          ${state.menu
            .map(
              (item) => `
            <button class="nav-item ${state.screen === item.id ? "active" : ""}" data-nav="${item.id}">
              <span class="nav-icon">${icon(item.icon)}</span>
              <span>${item.label}</span>
            </button>`
            )
            .join("")}
        </nav>
        <button class="sidebar-card" data-nav="profile" type="button">
          <div class="mini-avatar">${escapeHtml(initials)}</div>
          <div>
            <strong>${escapeHtml(firstName)}</strong>
            <span>@${escapeHtml(username)}</span>
          </div>
          ${icon("arrow", 18)}
        </button>
        <button class="text-button sidebar-logout" data-action="logout">Выйти из аккаунта</button>
      </aside>
      <main class="main">
        <header class="mobile-header">
          ${logo()}
          <button class="mobile-avatar" data-nav="profile">${escapeHtml(initials)}</button><button class="text-button mobile-logout" data-action="logout">Выйти</button>
        </header>
        ${screenHtml}
      </main>
      <nav class="bottom-nav" aria-label="Мобильная навигация">
        ${state.menu
          .map(
            (item) => `
          <button class="${state.screen === item.id ? "active" : ""}" data-nav="${item.id}" aria-label="${item.label}">
            ${icon(item.icon, 21)}
            <span>${item.label}</span>
          </button>`
          )
          .join("")}
      </nav>
      ${renderModal()}
      ${state.legalDoc ? renderLegalReader(state.legalDoc) : ""}
      ${state.toast ? `<div class="toast">${icon("check", 18)}${escapeHtml(state.toast)}</div>` : ""}
    </div>`;

  bindCardGestures();
}

function go(screen) {
  if (!SCREENS.includes(screen)) return;
  state.screen = screen;
  state.formError = "";
  if (window.location.hash.replace("#", "") !== screen) {
    window.location.hash = screen;
  }
  render();
  if (screen === "stats") {
    loadStats();
  }
}

function showToast(message) {
  state.toast = message;
  render();
  window.clearTimeout(state.toastTimer);
  state.toastTimer = window.setTimeout(() => {
    state.toast = "";
    render();
  }, 2200);
}

async function copyText(value) {
  try {
    await navigator.clipboard.writeText(value);
    showToast("Реквизиты скопированы");
  } catch {
    showToast(`Реквизиты: ${value}`);
  }
}

async function swipe(direction) {
  if (state.animating || !state.cards.length || state.screen !== "feed") return;
  const current = state.cards[state.index % state.cards.length];
  state.animating = true;
  state.dragX = direction === "left" ? -700 : 700;
  render();
  window.setTimeout(async () => {
    if (direction === "right") {
      try {
        state.helped = await api.helpCard(current.id);
      } catch (error) {
        showToast(error.message);
      }
    }
    state.index += 1;
    state.dragX = 0;
    state.animating = false;
    render();
    trackCurrentView();
  }, 260);
}

function bindCardGestures() {
  const card = root.querySelector("[data-card]");
  if (!card) return;
  const applyDrag = () => {
    const rotate = Math.max(-12, Math.min(12, state.dragX / 28));
    card.style.transform = `translateX(${state.dragX}px) rotate(${rotate}deg)`;
    card.classList.toggle("dragging", state.pointerStart !== null);
    let stamp = card.querySelector(".swipe-stamp");
    const label = state.dragX > 40 ? "ПОМОЧЬ" : state.dragX < -40 ? "ДАЛЬШЕ" : "";
    if (label) {
      if (!stamp) {
        stamp = document.createElement("div");
        card.prepend(stamp);
      }
      stamp.className = `swipe-stamp ${state.dragX > 0 ? "help" : "skip"}`;
      stamp.textContent = label;
    } else if (stamp) {
      stamp.remove();
    }
  };
  card.addEventListener("pointerdown", (event) => {
    if (state.animating) return;
    card.setPointerCapture(event.pointerId);
    state.pointerStart = event.clientX;
    applyDrag();
  });
  card.addEventListener("pointermove", (event) => {
    if (state.pointerStart === null || state.animating) return;
    state.dragX = event.clientX - state.pointerStart;
    applyDrag();
  });
  const end = () => {
    if (state.pointerStart === null) return;
    if (Math.abs(state.dragX) > 95) {
      swipe(state.dragX > 0 ? "right" : "left");
    } else {
      state.dragX = 0;
      applyDrag();
    }
    state.pointerStart = null;
  };
  card.addEventListener("pointerup", end);
  card.addEventListener("pointercancel", end);
}

async function trackCurrentView() {
  if (!state.cards.length) return;
  const current = state.cards[state.index % state.cards.length];
  try {
    await api.viewCard(current.id);
  } catch {
    /* viewing is best-effort */
  }
}

function paintCreatePreview() {
  const amount = Number(String(state.form.amount || "").replace(/\D/g, "")) || 0;
  const purpose = state.form.purpose || "";
  const category = state.form.category;
  const previewCard = root.querySelector("[data-preview-card]");
  const amountNode = root.querySelector("[data-preview-amount]");
  const purposeNode = root.querySelector("[data-preview-purpose]");
  const categoryNode = root.querySelector("[data-preview-category]");
  const charCount = root.querySelector("[data-char-count]");
  const submit = root.querySelector("[data-submit-create]");
  if (previewCard) previewCard.style.background = cardColor(category, state.colors);
  if (categoryNode) categoryNode.textContent = category;
  if (amountNode) {
    amountNode.textContent = amount ? money(amount) : "0 ₽";
    amountNode.classList.toggle("placeholder-text", !amount);
  }
  if (purposeNode) {
    purposeNode.textContent = purpose || "Здесь появится описание вашей цели";
    purposeNode.classList.toggle("placeholder-text", !purpose);
  }
  if (charCount) charCount.textContent = `${purpose.length} / 160`;
  if (submit) submit.disabled = !(amount > 0 && purpose.trim().length >= 10) || state.submitting;
}

root.addEventListener("click", async (event) => {
  const legalOpen = event.target.closest("[data-legal]");
  if (legalOpen) {
    setLegalDoc(legalOpen.dataset.legal);
    return;
  }
  if (event.target.closest("[data-action='legal-close']") || event.target.matches("[data-legal-backdrop]")) {
    setLegalDoc(null);
    return;
  }
  if (event.target.closest("[data-action='gate-continue']")) {
    await acceptGate();
    return;
  }

  const nav = event.target.closest("[data-nav]");
  if (nav) {
    go(nav.dataset.nav);
    return;
  }

  const swipeBtn = event.target.closest("[data-swipe]");
  if (swipeBtn) {
    swipe(swipeBtn.dataset.swipe);
    return;
  }

  if (event.target.closest("[data-close-modal]")) {
    if (event.target.closest("[data-modal-card]") && !event.target.closest("[data-close-modal]")) {
      return;
    }
    if (event.target.classList.contains("requisites-modal")) return;
    state.helped = null;
    render();
    return;
  }

  const copyBtn = event.target.closest("[data-copy]");
  if (copyBtn) {
    copyText(copyBtn.dataset.copy);
    return;
  }

  const action = event.target.closest("[data-action]");
  if (action?.dataset.action === "edit") {
    state.editing = true;
    render();
  }
  if (action?.dataset.action === "cancel") {
    state.editing = false;
    state.formError = "";
    render();
  }
  if (action?.dataset.action === "reload") await loadFeed();
  if (action?.dataset.action === "toggle-auth") {
    state.authMode = state.authMode === "login" ? "register" : "login";
    state.authError = "";
    renderAuth();
  }
  if (action?.dataset.action === "delete-start") {
    state.deleting = true;
    state.deleteError = "";
    render();
  }
  if (action?.dataset.action === "delete-cancel") {
    state.deleting = false;
    state.deleteError = "";
    render();
  }
  if (action?.dataset.action === "export-data") {
    try {
      const data = await api.exportData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "payder-data.json";
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      showToast(error.message);
    }
  }
  if (action?.dataset.action === "logout") {
    await api.logout();
    state.authenticated = false;
    state.profile = null;
    state.cards = [];
    state.authMode = "login";
    showEntry();
  }
});

root.addEventListener("mousedown", (event) => {
  if (event.target.classList.contains("modal-backdrop")) {
    state.helped = null;
    render();
  }
});

root.addEventListener("change", async (event) => {
  if (event.target.matches("[data-gate]")) {
    state.gate[event.target.dataset.gate] = event.target.checked;
    const ready = state.gate.terms && state.gate.privacy;
    const button = root.querySelector("[data-action='gate-continue']");
    const hint = root.querySelector("[data-gate-hint]");
    if (button) button.disabled = !ready;
    if (hint) hint.hidden = ready;
    return;
  }
  if (event.target.matches("[data-period]")) {
    state.period = event.target.value;
    await loadStats();
    return;
  }
  if (event.target.closest("[data-form='create']") && event.target.name === "category") {
    state.form.category = event.target.value;
    paintCreatePreview();
  }
});

root.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;
  if (form.dataset.form === "auth") {
    const payload = Object.fromEntries(new FormData(form).entries());
    try {
      state.authError = "";
      state.authNote = "";
      if (state.authMode === "register") await api.register({ ...payload, consent_version: state.consent?.version });
      else await api.login(payload);
      state.profile = await api.profile();
      const menu = await api.menu();
      state.menu = menu.items?.length ? menu.items : DEFAULT_MENU;
      state.banks = menu.banks || state.banks;
      state.categories = menu.categories || state.categories;
      state.colors = menu.colors || {};
      state.authenticated = true;
      state.form.category = state.categories[0];
      if (!state.profile.legal_accepted) {
        state.gate = { terms: false, privacy: false };
        state.gateOpen = true;
        render();
        return;
      }
      await loadFeed();
    } catch (error) { state.authError = error.message; renderAuth(); }
    return;
  }
  if (form.dataset.form === "delete") {
    const password = new FormData(form).get("password");
    try {
      await api.deleteAccount(password);
      state.authenticated = false;
      state.profile = null;
      state.cards = [];
      state.stats = null;
      state.helped = null;
      state.deleting = false;
      state.deleteError = "";
      state.authMode = "login";
      state.authError = "";
      state.authNote = "Аккаунт удалён вместе со всеми данными.";
      showEntry();
    } catch (error) {
      state.deleteError = error.message;
      render();
    }
    return;
  }
  if (form.dataset.form === "profile") {
    const payload = Object.fromEntries(new FormData(form).entries());
    try {
      state.submitting = true;
      state.profile = await api.saveProfile(payload);
      state.editing = false;
      state.formError = "";
      showToast("Профиль сохранён");
    } catch (error) {
      state.formError = error.message;
      render();
    } finally {
      state.submitting = false;
    }
  }
  if (form.dataset.form === "create") {
    const data = Object.fromEntries(new FormData(form).entries());
    const amount = Number(String(data.amount).replace(/\D/g, "")) || 0;
    try {
      state.submitting = true;
      render();
      await api.createCard({
        amount,
        purpose: data.purpose,
        category: data.category,
      });
      state.form = { amount: "", purpose: "", category: data.category };
      state.previewId = makePreviewId();
      state.formError = "";
      await loadFeed();
      state.profile = await api.profile();
      state.submitting = false;
      go("feed");
      showToast("Карточка опубликована");
    } catch (error) {
      state.submitting = false;
      state.formError = error.message;
      render();
    }
  }
});

root.addEventListener("input", (event) => {
  const form = event.target.closest("[data-form='create']");
  if (!form) return;
  const data = Object.fromEntries(new FormData(form).entries());
  state.form = {
    amount: data.amount,
    purpose: String(data.purpose || "").slice(0, 160),
    category: data.category,
  };
  if (event.target.name === "purpose" && event.target.value.length > 160) {
    event.target.value = state.form.purpose;
  }
  paintCreatePreview();
});

window.addEventListener("hashchange", () => {
  const next = screenFromHash();
  if (next === state.screen) return;
  state.screen = next;
  state.formError = "";
  render();
  if (next === "stats") loadStats();
});

window.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && state.legalDoc) {
    setLegalDoc(null);
    return;
  }
  if (state.gateOpen || state.legalDoc) return;
  if (state.screen !== "feed" || state.helped) return;
  const tag = document.activeElement?.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
  if (event.key === "ArrowLeft") swipe("left");
  if (event.key === "ArrowRight") swipe("right");
});

async function loadFeed() {
  state.loading = true;
  state.error = "";
  render();
  try {
    state.cards = await api.cards();
    state.index = 0;
  } catch (error) {
    state.error = error.message;
  } finally {
    state.loading = false;
    render();
    trackCurrentView();
  }
}

async function loadStats() {
  state.statsLoading = true;
  render();
  try {
    state.stats = await api.stats(state.period);
    state.error = "";
  } catch (error) {
    if (!state.stats) state.error = error.message;
    else showToast(error.message);
  } finally {
    state.statsLoading = false;
    render();
  }
}

async function boot() {
  try {
    const menu = await api.menu();
    state.menu = menu.items?.length ? menu.items : DEFAULT_MENU;
    state.banks = menu.banks || state.banks;
    state.categories = menu.categories || state.categories;
    state.colors = menu.colors || {};
    state.profile = await api.profile();
    state.authenticated = true;
    state.form.category = state.categories[0];
    if (!state.profile.legal_accepted) {
      state.loading = false;
      state.gateOpen = true;
      render();
      return;
    }
    await loadFeed();
    if (state.screen === "stats") await loadStats();
  } catch {
    state.loading = false;
    state.authenticated = false;
    showEntry();
  }
}

boot();