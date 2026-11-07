async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (response.status === 204) {
    return null;
  }

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload.detail;
    const message = Array.isArray(detail)
      ? detail.map((item) => item.msg || item).join(", ")
      : detail || "Не удалось выполнить запрос";
    throw new Error(message);
  }
  return payload;
}

export const api = {
  menu: () => request("/api/menu"),
  register: (body) => request("/api/auth/register", { method: "POST", body: JSON.stringify(body) }),
  login: (body) => request("/api/auth/login", { method: "POST", body: JSON.stringify(body) }),
  logout: () => request("/api/auth/logout", { method: "POST" }),
  cards: () => request("/api/cards"),
  createCard: (body) => request("/api/cards", { method: "POST", body: JSON.stringify(body) }),
  viewCard: (id) => request(`/api/cards/${id}/view`, { method: "POST" }),
  helpCard: (id) => request(`/api/cards/${id}/help`, { method: "POST" }),
  profile: () => request("/api/profile"),
  saveProfile: (body) => request("/api/profile", { method: "PUT", body: JSON.stringify(body) }),
  stats: (period = "month") => request(`/api/stats?period=${encodeURIComponent(period)}`),
};
