import { escapeHtml, icon } from "../icons.js";

export function renderProfile({ profile, editing, banks, error, extra = "" }) {
  if (!profile) {
    return `<section class="screen content-screen"><div class="loading-state"><h2>Загружаем профиль</h2></div></section>`;
  }

  return `
    <section class="screen content-screen">
      <div class="screen-heading">
        <div>
          <p class="eyebrow">ЛИЧНЫЙ КАБИНЕТ</p>
          <h1>Ваш профиль</h1>
        </div>
        ${editing ? "" : `<button class="secondary-button" data-action="edit">${icon("edit", 18)} Редактировать</button>`}
      </div>
      <div class="profile-grid">
        <div class="panel profile-summary">
          <div class="large-avatar">${escapeHtml(profile.initials)}</div>
          <h2>${escapeHtml(profile.name)}</h2>
          <p>@${escapeHtml(profile.username)}</p>
          <span class="verified-badge">${icon("check", 14)} Профиль подтверждён</span>
          <div class="profile-mini-stats">
            <div><strong>${profile.helped}</strong><span>помогли</span></div>
            <div><strong>${profile.cards}</strong><span>карточки</span></div>
          </div>
        </div>
        <form class="panel details-panel" data-form="profile">
          <div class="panel-heading">
            <div>
              <h3>Личные данные</h3>
              <p>Эти данные видны только вам</p>
            </div>
          </div>
          <label>Имя и фамилия
            <input name="name" value="${escapeHtml(profile.name)}" ${editing ? "" : "disabled"} required minlength="2">
          </label>
          <label>Номер телефона
            <input name="phone" value="${escapeHtml(profile.phone)}" ${editing ? "" : "disabled"} required minlength="5">
          </label>
          <div class="section-divider"></div>
          <div class="panel-heading compact">
            <div>
              <h3>Реквизиты для переводов</h3>
              <p>Покажем их только тем, кто выберет вашу карточку</p>
            </div>
          </div>
          <div class="field-row">
            <label>Банк
              <select name="bank" ${editing ? "" : "disabled"}>
                ${banks.map((bank) => `<option ${bank === profile.bank ? "selected" : ""}>${escapeHtml(bank)}</option>`).join("")}
              </select>
            </label>
            <label>Телефон или карта
              <input name="requisites" value="${escapeHtml(profile.requisites)}" ${editing ? "" : "disabled"} required minlength="5">
            </label>
          </div>
          ${error ? `<p class="field-error">${escapeHtml(error)}</p>` : ""}
          ${
            editing
              ? `<div class="form-actions">
                  <button type="button" class="text-button" data-action="cancel">Отмена</button>
                  <button class="primary-button">Сохранить изменения</button>
                </div>`
              : ""
          }
        </form>
      </div>
      ${extra}
    </section>`;
}
