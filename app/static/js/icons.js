const PATHS = {
  cards: `<rect x="4" y="5" width="15" height="15" rx="3"></rect><path d="M8 2h9a4 4 0 0 1 4 4v10"></path>`,
  user: `<circle cx="12" cy="8" r="4"></circle><path d="M4.5 21a7.5 7.5 0 0 1 15 0"></path>`,
  chart: `<path d="M4 19V9M10 19V5M16 19v-7M22 19V3"></path><path d="M2 19h21"></path>`,
  plus: `<path d="M12 5v14M5 12h14"></path>`,
  close: `<path d="m6 6 12 12M18 6 6 18"></path>`,
  heart: `<path d="M20.8 4.7a5.5 5.5 0 0 0-7.8 0L12 5.8l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8l1.1 1.1L12 21l7.8-7.4 1.1-1.1a5.5 5.5 0 0 0-.1-7.8Z"></path>`,
  copy: `<rect x="8" y="8" width="12" height="12" rx="2"></rect><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"></path>`,
  edit: `<path d="M12 20h9"></path><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4Z"></path>`,
  arrow: `<path d="m9 18 6-6-6-6"></path>`,
  check: `<path d="m5 12 4 4L19 6"></path>`,
  back: `<path d="m15 18-6-6 6-6"></path>`,
  doc: `<path d="M7 3h7l5 5v11a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"></path><path d="M14 3v5h5M9 13h6M9 17h4"></path>`,
  "check-doc": `<path d="M7 3h7l5 5v11a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"></path><path d="M14 3v5h5"></path><path d="m9 14 2.2 2.2L15.5 12"></path>`,
  wallet: `<path d="M4 6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v14H6a2 2 0 0 1-2-2Z"></path><path d="M4 8h16M15 13h5"></path>`,
};

export function icon(name, size = 22) {
  return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${PATHS[name] || ""}</svg>`;
}

export function money(value) {
  return new Intl.NumberFormat("ru-RU").format(value) + " ₽";
}

export function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
