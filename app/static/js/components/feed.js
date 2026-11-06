import { escapeHtml, icon, money } from "../icons.js";

export function renderFeed({ cards, index, dragX, dragging, animating, error, loading }) {
  if (loading) {
    return `
      <section class="screen feed-screen">
        <div class="screen-heading feed-heading">
          <div>
            <p class="eyebrow">ЛЕНТА ЗАПРОСОВ</p>
            <h1>Кому поможем сегодня?</h1>
          </div>
        </div>
        <div class="loading-state"><h2>Загружаем карточки</h2><p>Ещё секунда</p></div>
      </section>`;
  }

  if (error) {
    return `
      <section class="screen feed-screen">
        <div class="screen-heading feed-heading">
          <div>
            <p class="eyebrow">ЛЕНТА ЗАПРОСОВ</p>
            <h1>Кому поможем сегодня?</h1>
          </div>
        </div>
        <div class="error-state">
          <h2>Не получилось загрузить ленту</h2>
          <p>${escapeHtml(error)}</p>
          <button class="primary-button" data-action="reload">Попробовать снова</button>
        </div>
      </section>`;
  }

  if (!cards.length) {
    return `
      <section class="screen feed-screen">
        <div class="screen-heading feed-heading">
          <div>
            <p class="eyebrow">ЛЕНТА ЗАПРОСОВ</p>
            <h1>Кому поможем сегодня?</h1>
          </div>
        </div>
        <div class="empty-state">
          <h2>Пока нет запросов</h2>
          <p>Создайте первую карточку или загляните позже</p>
          <button class="primary-button" data-nav="create">Создать карточку</button>
        </div>
      </section>`;
  }

  const current = cards[index % cards.length];
  const next = cards[(index + 1) % cards.length];
  const progress = (index % cards.length) + 1;
  const rotate = Math.max(-12, Math.min(12, dragX / 28));
  const stamp = dragX > 40 ? "ПОМОЧЬ" : dragX < -40 ? "ДАЛЬШЕ" : "";

  return `
    <section class="screen feed-screen">
      <div class="screen-heading feed-heading">
        <div>
          <p class="eyebrow">ЛЕНТА ЗАПРОСОВ</p>
          <h1>Кому поможем сегодня?</h1>
        </div>
        <div class="counter"><span>${progress}</span> / ${cards.length}</div>
      </div>
      <div class="deck-wrap">
        <div class="request-card card-behind second" style="background:${escapeHtml(next.color)}"></div>
        <div class="request-card card-behind first" style="background:${escapeHtml(next.color)}">
          <span class="card-id">${escapeHtml(next.id)}</span>
        </div>
        <div
          class="request-card active-card ${dragging ? "dragging" : ""} ${animating ? "animating" : ""}"
          style="background:${escapeHtml(current.color)};transform:translateX(${dragX}px) rotate(${rotate}deg)"
          data-card
        >
          ${stamp ? `<div class="swipe-stamp ${dragX > 0 ? "help" : "skip"}">${stamp}</div>` : ""}
          <div class="card-top">
            <span class="card-id">${escapeHtml(current.id)}</span>
            <span class="category">${escapeHtml(current.category)}</span>
          </div>
          <div class="card-content">
            <span class="amount-label">НУЖНА СУММА</span>
            <div class="amount">${money(current.amount)}</div>
            <div class="purpose-rule"></div>
            <p class="purpose">${escapeHtml(current.purpose)}</p>
          </div>
          <div class="card-author">
            <span class="author-avatar">${escapeHtml(current.initials)}</span>
            <div>
              <span>Автор запроса</span>
              <strong>${escapeHtml(current.author)}</strong>
            </div>
          </div>
        </div>
      </div>
      <div class="swipe-actions">
        <button class="round-action skip-action" data-swipe="left" aria-label="Пропустить">${icon("close", 30)}</button>
        <div class="swipe-hint"><span>Пропустить</span><span>Помочь</span></div>
        <button class="round-action help-action" data-swipe="right" aria-label="Помочь">${icon("heart", 29)}</button>
      </div>
      <p class="desktop-hint">Перетяните карточку или используйте кнопки</p>
    </section>`;
}
