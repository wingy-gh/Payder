import { escapeHtml, icon, money } from "../icons.js";

export function renderStats({ stats, period = "month", loading = false, error = "" }) {
  if (loading && !stats) {
    return `<section class="screen content-screen"><div class="loading-state"><h2>Считаем статистику</h2></div></section>`;
  }

  if (error && !stats) {
    return `
      <section class="screen content-screen">
        <div class="error-state">
          <h2>Не получилось загрузить статистику</h2>
          <p>${escapeHtml(error)}</p>
          <button class="primary-button" data-nav="stats">Повторить</button>
        </div>
      </section>`;
  }

  if (!stats) {
    return `<section class="screen content-screen"><div class="loading-state"><h2>Считаем статистику</h2></div></section>`;
  }

  const max = Math.max(...stats.chart.map((item) => item.value), 1);

  return `
    <section class="screen content-screen">
      <div class="screen-heading">
        <div>
          <p class="eyebrow">ВАША АКТИВНОСТЬ</p>
          <h1>Статистика</h1>
        </div>
        <select class="period-select" data-period aria-label="Период">
          <option value="month" ${period === "month" ? "selected" : ""}>За месяц</option>
          <option value="week" ${period === "week" ? "selected" : ""}>За неделю</option>
          <option value="year" ${period === "year" ? "selected" : ""}>За год</option>
        </select>
      </div>
      <div class="metrics-grid">
        <div class="metric-card accent">
          <span>Собрано на ваши карточки</span>
          <strong>${money(stats.collected)}</strong>
          <small>${escapeHtml(stats.collected_delta || "За выбранный период")}</small>
        </div>
        <div class="metric-card">
          <span>Вы помогли</span>
          <strong>${stats.helped_people} людям</strong>
          <small>на общую сумму ${money(stats.helped_amount)}</small>
        </div>
        <div class="metric-card">
          <span>Активные карточки</span>
          <strong>${stats.active_cards}</strong>
          <small>из ${stats.card_limit} доступных</small>
        </div>
      </div>
      <div class="stats-grid">
        <div class="panel chart-panel">
          <div class="panel-heading">
            <div>
              <h3>Просмотры карточек</h3>
              <p>За последние 7 дней</p>
            </div>
            <strong>${stats.views_total}</strong>
          </div>
          <div class="chart">
            ${stats.chart
              .map(
                (item) => `
              <div class="bar-column">
                <div class="bar-track">
                  <div class="bar" style="height:${(item.value / max) * 100}%"><span>${item.value}</span></div>
                </div>
                <small>${escapeHtml(item.day)}</small>
              </div>`
              )
              .join("")}
          </div>
        </div>
        <div class="panel recent-panel">
          <div class="panel-heading">
            <div>
              <h3>Последние события</h3>
              <p>Недавняя активность</p>
            </div>
          </div>
          ${
            stats.activities.length
              ? stats.activities
                  .map(
                    (item) => `
            <div class="activity-row">
              <div class="activity-icon ${item.kind === "out" ? "out" : ""}">
                ${icon(item.kind === "view" ? "cards" : "arrow", 18)}
              </div>
              <div>
                <strong>${escapeHtml(item.title)}</strong>
                <span>${escapeHtml(item.happened_at)}</span>
              </div>
              <b>${escapeHtml(item.amount_label)}</b>
            </div>`
                  )
                  .join("")
              : `<p class="preview-note">Событий пока нет</p>`
          }
        </div>
      </div>
    </section>`;
}
