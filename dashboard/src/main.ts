import {
  clearConfig,
  fetchDueReviews,
  fetchStatsSummary,
  fetchTodaySet,
  loadConfig,
  saveConfig,
  verifyAuth,
} from "./api";
import type { DailySet, DailySetItem, DashboardConfig, ProblemWithProgress, StatsSummary } from "./types";
import "./style.css";

const appRoot = document.querySelector<HTMLDivElement>("#app");
if (!appRoot) {
  throw new Error("Missing #app root");
}
const app: HTMLDivElement = appRoot;

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function formatDate(value: string | null): string {
  if (!value) {
    return "—";
  }
  return value;
}

function renderLogin(): void {
  const existing = loadConfig();
  app.innerHTML = `
    <div class="login-card">
      <h1>NeetCode Dashboard</h1>
      <p>Connect to your NeetCode SRS API using the same base URL and API key as the browser extension.</p>
      <form id="login-form">
        <div class="field">
          <label for="apiBaseUrl">API base URL</label>
          <input id="apiBaseUrl" name="apiBaseUrl" placeholder="https://your-api.example.com" value="${escapeHtml(existing?.apiBaseUrl ?? "")}" required />
        </div>
        <div class="field">
          <label for="apiKey">API key</label>
          <input id="apiKey" name="apiKey" type="password" placeholder="X-API-Key" value="${escapeHtml(existing?.apiKey ?? "")}" required />
        </div>
        <button class="primary" type="submit">Connect</button>
      </form>
      <div id="status" class="status"></div>
    </div>
  `;

  const form = document.querySelector<HTMLFormElement>("#login-form");
  const status = document.querySelector<HTMLDivElement>("#status");
  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!status) {
      return;
    }
    status.textContent = "Verifying…";
    status.className = "status";

    const formData = new FormData(form);
    const config: DashboardConfig = {
      apiBaseUrl: String(formData.get("apiBaseUrl") ?? ""),
      apiKey: String(formData.get("apiKey") ?? ""),
    };

    try {
      const verified = await verifyAuth(config);
      saveConfig(config);
      status.textContent = `Connected to ${verified.app_name}`;
      status.className = "status ok";
      await renderDashboard(config);
    } catch (error) {
      status.textContent = error instanceof Error ? error.message : "Connection failed";
      status.className = "status error";
    }
  });
}

function statCard(label: string, value: number | string): string {
  return `
    <div class="stat-card">
      <div class="label">${escapeHtml(label)}</div>
      <div class="value">${escapeHtml(String(value))}</div>
    </div>
  `;
}

function renderDueTable(items: ProblemWithProgress[]): string {
  if (items.length === 0) {
    return '<p class="empty">No reviews due right now.</p>';
  }
  const rows = items
    .map(
      (item) => `
      <tr>
        <td><a href="${escapeHtml(item.neetcode_url)}" target="_blank" rel="noreferrer">${escapeHtml(item.title)}</a></td>
        <td>${escapeHtml(item.pattern)}</td>
        <td>${formatDate(item.progress?.next_review ?? null)}</td>
        <td>${escapeHtml(item.progress?.confidence ?? "unset")}</td>
        <td><span class="badge due">${escapeHtml(item.progress?.review_stage ?? "new")}</span></td>
      </tr>
    `,
    )
    .join("");
  return `
    <table>
      <thead>
        <tr>
          <th>Problem</th>
          <th>Pattern</th>
          <th>Due</th>
          <th>Confidence</th>
          <th>Stage</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function renderDailyItems(items: DailySetItem[]): string {
  if (items.length === 0) {
    return '<p class="empty">None</p>';
  }
  return `
    <ul>
      ${items
        .map(
          (item) => `
        <li>
          <a href="${escapeHtml(item.neetcode_url)}" target="_blank" rel="noreferrer">${escapeHtml(item.title)}</a>
          <span class="badge ${item.completed ? "done" : ""}">${escapeHtml(item.slot)}</span>
        </li>
      `,
        )
        .join("")}
    </ul>
  `;
}

function renderPatternProgress(stats: StatsSummary): string {
  if (stats.by_pattern.length === 0) {
    return '<p class="empty">No pattern data yet.</p>';
  }
  return stats.by_pattern
    .map((row) => {
      const pct = row.total === 0 ? 0 : Math.round((row.solved / row.total) * 100);
      return `
        <div class="pattern-row">
          <div>
            <div>${escapeHtml(row.pattern)}</div>
            <div class="meta">${row.solved} / ${row.total} solved</div>
            <div class="progress-bar"><span style="width: ${pct}%"></span></div>
          </div>
          <div>${pct}%</div>
        </div>
      `;
    })
    .join("");
}

function renderDashboardShell(
  config: DashboardConfig,
  stats: StatsSummary,
  due: ProblemWithProgress[],
  daily: DailySet,
): void {
  app.innerHTML = `
    <header class="page-header">
      <div>
        <h1>NeetCode Dashboard</h1>
        <p>${escapeHtml(config.apiBaseUrl)}</p>
      </div>
      <div class="toolbar">
        <button id="refresh-btn" type="button">Refresh</button>
        <button id="logout-btn" type="button">Disconnect</button>
      </div>
    </header>

    <section class="grid stats-grid">
      ${statCard("Total", stats.total)}
      ${statCard("Solved", stats.solved)}
      ${statCard("Unsolved", stats.unsolved)}
      ${statCard("Due today", stats.due_today)}
      ${statCard("Overdue", stats.due_overdue)}
      ${statCard("Mastered", stats.mastered)}
    </section>

    <section class="layout layout-two" style="margin-top: 1.25rem;">
      <div class="panel">
        <h2>Due for Review</h2>
        ${renderDueTable(due)}
      </div>
      <div class="panel">
        <h2>Today's Set (${escapeHtml(daily.set_date)})</h2>
        <p><strong>Focus:</strong> ${escapeHtml(daily.focus_pattern ?? "None")}</p>
        <h3>Review</h3>
        ${renderDailyItems(daily.review)}
        <h3>Focused New</h3>
        ${renderDailyItems(daily.focused_new)}
        <h3>Random New</h3>
        ${renderDailyItems(daily.random_new)}
      </div>
    </section>

    <section class="layout layout-two" style="margin-top: 1.25rem;">
      <div class="panel">
        <h2>Confidence</h2>
        <div class="confidence-grid">
          ${statCard("Struggling", stats.by_confidence.struggling)}
          ${statCard("Getting there", stats.by_confidence.getting_there)}
          ${statCard("Solid", stats.by_confidence.solid)}
          ${statCard("Unset", stats.by_confidence.unset)}
        </div>
      </div>
      <div class="panel">
        <h2>Review Stage</h2>
        <div class="stage-grid">
          ${Object.entries(stats.by_review_stage)
            .map(([stage, count]) => statCard(stage, count))
            .join("")}
        </div>
      </div>
    </section>

    <section class="panel" style="margin-top: 1.25rem;">
      <h2>Progress by Pattern</h2>
      ${renderPatternProgress(stats)}
    </section>
  `;

  document.querySelector("#refresh-btn")?.addEventListener("click", () => {
    void renderDashboard(config);
  });
  document.querySelector("#logout-btn")?.addEventListener("click", () => {
    clearConfig();
    renderLogin();
  });
}

async function renderDashboard(config: DashboardConfig): Promise<void> {
  app.innerHTML = '<p class="empty">Loading dashboard…</p>';
  try {
    const [stats, due, daily] = await Promise.all([
      fetchStatsSummary(config),
      fetchDueReviews(config),
      fetchTodaySet(config),
    ]);
    renderDashboardShell(config, stats, due, daily);
  } catch (error) {
    app.innerHTML = `
      <div class="panel">
        <h2>Failed to load dashboard</h2>
        <p class="status error">${escapeHtml(error instanceof Error ? error.message : "Unknown error")}</p>
        <button id="retry-login" type="button">Back to login</button>
      </div>
    `;
    document.querySelector("#retry-login")?.addEventListener("click", renderLogin);
  }
}

const saved = loadConfig();
if (saved) {
  void renderDashboard(saved);
} else {
  renderLogin();
}
