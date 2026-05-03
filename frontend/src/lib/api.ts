const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...opts.headers },
    ...opts,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `HTTP ${res.status}`);
  }
  return res.json();
}

// ── Jobs ─────────────────────────────────────────────────────────────────────

export const jobsApi = {
  trigger: (source = "bookmarks", limit = 30) =>
    request<any>(`/api/jobs/run-pipeline?source=${source}&limit=${limit}`, { method: "POST" }),

  listJobs: () => request<any[]>(`/api/jobs/status`),

  getJob: (id: string) => request<any>(`/api/jobs/status/${id}`),

  getSummary: () => request<any>(`/api/jobs/analytics/summary`),
};

// ── Scripts ───────────────────────────────────────────────────────────────────

export const scriptsApi = {
  list: (params?: { status?: string; limit?: number; offset?: number }) => {
    const qs = new URLSearchParams();
    if (params?.status) qs.set("status", params.status);
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.offset) qs.set("offset", String(params.offset));
    return request<any[]>(`/api/scripts?${qs.toString()}`);
  },

  get: (id: string) => request<any>(`/api/scripts/${id}`),

  update: (id: string, data: Partial<{ hook: string; body: string; cta: string; status: string; user_feedback: string }>) =>
    request<any>(`/api/scripts/${id}`, { method: "PATCH", body: JSON.stringify(data) }),

  delete: (id: string) =>
    request<{ ok: boolean }>(`/api/scripts/${id}`, { method: "DELETE" }),

  generateManual: (content: string, nicheConfigId?: string) =>
    request<any[]>(`/api/scripts/generate/manual`, {
      method: "POST",
      body: JSON.stringify({ content, niche_config_id: nicheConfigId }),
    }),

  logPerformance: (id: string, data: any) =>
    request<any>(`/api/scripts/${id}/performance`, { method: "POST", body: JSON.stringify(data) }),
};

// ── Tweets ────────────────────────────────────────────────────────────────────

export const tweetsApi = {
  list: (params?: { status?: string }) => {
    const qs = new URLSearchParams();
    if (params?.status) qs.set("status", params.status);
    return request<any[]>(`/api/tweets?${qs.toString()}`);
  },
};

// ── Niche Settings ─────────────────────────────────────────────────────────────

export const nicheApi = {
  list: () => request<any[]>(`/api/settings/niche`),
  create: (data: any) => request<any>(`/api/settings/niche`, { method: "POST", body: JSON.stringify(data) }),
  update: (id: string, data: any) => request<any>(`/api/settings/niche/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  delete: (id: string) => request<{ ok: boolean }>(`/api/settings/niche/${id}`, { method: "DELETE" }),
};
