import { DOCS, LEGAL_VERSION } from "../legal.js";
import { escapeHtml, icon } from "../icons.js";

const ORDER = ["privacy", "terms"];

function renderBlocks(section, sectionIndex) {
  let n = 0;
  return section.blocks
    .map((block) => {
      if (typeof block === "string") {
        n += 1;
        return `<p class="legal-clause"><span class="legal-num">${sectionIndex + 1}.${n}</span><span>${escapeHtml(block)}</span></p>`;
      }
      const list = block.list
        ? `<ul class="legal-list">${block.list.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`
        : "";
      if (block.lead) return `<p class="legal-lead">${escapeHtml(block.lead)}</p>`;
      if (block.note) return `<p class="legal-lead legal-note">${escapeHtml(block.note)}</p>`;
      if (block.label) return `<p class="legal-label">${escapeHtml(block.label)}</p>${list}`;
      return list;
    })
    .join("");
}

function renderDocBody(doc) {
  return doc.sections
    .map(
      (section, index) => `
      <section class="legal-section">
        <h3><span class="legal-sec-num">${index + 1}</span>${escapeHtml(section.title)}</h3>
        ${renderBlocks(section, index)}
      </section>`
    )
    .join("");
}

// Окно чтения документа поверх любого экрана.
export function renderLegalReader(docId) {
  const doc = DOCS[docId];
  if (!doc) return "";
  return `
    <div class="legal-overlay" data-legal-backdrop>
      <div class="legal-sheet" role="dialog" aria-modal="true" aria-label="${escapeHtml(doc.title)}">
        <header class="legal-head">
          <button class="legal-back" type="button" data-action="legal-close" aria-label="Назад">${icon("back", 20)}</button>
          <div>
            <p class="eyebrow">${escapeHtml(doc.kicker)}</p>
            <h2>${escapeHtml(doc.title)}</h2>
            <span class="legal-version">Версия ${LEGAL_VERSION}</span>
          </div>
        </header>
        <div class="legal-scroll" data-legal-scroll>${renderDocBody(doc)}</div>
        <footer class="legal-foot">
          <button class="primary-button full" type="button" data-action="legal-close">Понятно</button>
        </footer>
      </div>
    </div>`;
}

function docRows() {
  return ORDER.map((id) => {
    const doc = DOCS[id];
    return `
      <button class="gate-doc" type="button" data-legal="${id}">
        <span class="gate-doc-icon">${icon(doc.icon, 20)}</span>
        <span class="gate-doc-title">${escapeHtml(doc.short)}</span>
        <span class="gate-doc-arrow">${icon("arrow", 18)}</span>
      </button>`;
  }).join("");
}

// Стартовый экран: документы + обязательные отметки.
export function renderGate({ gate, legalDoc, error, account }) {
  const ready = gate.terms && gate.privacy;
  return `
    <main class="auth-shell">
      <section class="auth-panel gate-panel">
        <div class="gate-head">
          <div class="logo"><span class="logo-mark">P</span><span>Payder</span></div>
          <p class="eyebrow">ДОБРО ПОЖАЛОВАТЬ</p>
        </div>
        <h1>${account ? "Документы обновились" : "Перед началом работы"}</h1>
        <p class="auth-description">${account ? "Чтобы продолжить, ознакомьтесь с актуальными документами сервиса." : "Ознакомьтесь с документами сервиса."}</p>
        <div class="gate-docs">${docRows()}</div>
        <p class="gate-note">В тестовой версии документы являются предварительными и требуют заполнения и проверки перед публичным запуском.</p>
        <div class="gate-checks">
          <label class="gate-check">
            <input type="checkbox" data-gate="terms" ${gate.terms ? "checked" : ""}>
            <span class="gate-box">${icon("check", 14)}</span>
            <span>Я ознакомился с Пользовательским соглашением.</span>
          </label>
          <label class="gate-check">
            <input type="checkbox" data-gate="privacy" ${gate.privacy ? "checked" : ""}>
            <span class="gate-box">${icon("check", 14)}</span>
            <span>Я ознакомился с Политикой обработки персональных данных.</span>
          </label>
        </div>
        ${error ? `<p class="field-error">${escapeHtml(error)}</p>` : ""}
        <button class="primary-button full gate-continue" type="button" data-action="gate-continue" ${ready ? "" : "disabled"}>Продолжить</button>
        <p class="gate-hint" data-gate-hint ${ready ? "hidden" : ""}>Кнопка активируется после необходимых отметок.</p>
        ${account ? `<button class="text-button auth-switch" type="button" data-action="logout">Выйти из аккаунта</button>` : ""}
      </section>
    </main>
    ${legalDoc ? renderLegalReader(legalDoc) : ""}`;
}

// Блок «Документы» на экране профиля.
export function renderDocsPanel() {
  return `
    <section class="panel privacy-panel" style="margin-top:16px">
      <p class="eyebrow">ДОКУМЕНТЫ</p>
      <div class="gate-docs docs-panel-list">${docRows()}</div>
    </section>`;
}

// Ссылки под формой входа/регистрации.
export function renderLegalLinks() {
  return `
    <div class="legal-links">
      <button class="text-button" type="button" data-legal="terms">Пользовательское соглашение</button>
      <button class="text-button" type="button" data-legal="privacy">Политика обработки данных</button>
    </div>`;
}
