import type { DailySet, DashboardConfig, ProblemWithProgress, StatsSummary } from "./types";

const CONFIG_KEY = "neetcode-dashboard-config";

export function loadConfig(): DashboardConfig | null {
  const raw = localStorage.getItem(CONFIG_KEY);
  if (!raw) {
    return null;
  }
  try {
    const parsed = JSON.parse(raw) as DashboardConfig;
    if (!parsed.apiBaseUrl || !parsed.apiKey) {
      return null;
    }
    return {
      apiBaseUrl: parsed.apiBaseUrl.trim().replace(/\/$/, ""),
      apiKey: parsed.apiKey.trim(),
    };
  } catch {
    return null;
  }
}

export function saveConfig(config: DashboardConfig): void {
  localStorage.setItem(
    CONFIG_KEY,
    JSON.stringify({
      apiBaseUrl: config.apiBaseUrl.trim().replace(/\/$/, ""),
      apiKey: config.apiKey.trim(),
    }),
  );
}

export function clearConfig(): void {
  localStorage.removeItem(CONFIG_KEY);
}

async function apiFetch<T>(config: DashboardConfig, path: string): Promise<T> {
  const response = await fetch(`${config.apiBaseUrl}${path}`, {
    headers: {
      "X-API-Key": config.apiKey,
    },
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return (await response.json()) as T;
}

export async function verifyAuth(config: DashboardConfig): Promise<{ ok: boolean; app_name: string }> {
  return apiFetch(config, "/auth/verify");
}

export async function fetchStatsSummary(config: DashboardConfig): Promise<StatsSummary> {
  return apiFetch(config, "/stats/summary");
}

export async function fetchDueReviews(config: DashboardConfig): Promise<ProblemWithProgress[]> {
  return apiFetch(config, "/reviews/due?limit=50");
}

export async function fetchTodaySet(config: DashboardConfig): Promise<DailySet> {
  return apiFetch(config, "/daily-sets/today");
}
