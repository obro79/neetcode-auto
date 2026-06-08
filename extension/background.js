const DEFAULT_CONFIG = {
  apiBaseUrl: "https://neetcode-auto-production.up.railway.app",
  apiKey: "",
  autoSync: true,
  debugMode: false,
};

const DEFAULT_PUBLIC_CONFIG = {
  slug_aliases: {},
  sync_only_daily_set: false,
};

chrome.runtime.onInstalled.addListener(async () => {
  const stored = await chrome.storage.local.get("config");
  if (!stored.config) {
    await chrome.storage.local.set({ config: DEFAULT_CONFIG });
  }
  await refreshPublicConfig();
});

chrome.runtime.onStartup.addListener(() => {
  void refreshPublicConfig();
});

async function refreshPublicConfig() {
  const { config } = await chrome.storage.local.get("config");
  const settings = config || DEFAULT_CONFIG;
  if (!settings.apiBaseUrl) return;

  try {
    const response = await fetch(`${settings.apiBaseUrl}/config/public`);
    if (!response.ok) return;
    const publicConfig = await response.json();
    await chrome.storage.local.set({ publicConfig });
  } catch (_error) {
    // Keep cached config on network failure.
  }
}

function resolveSlug(slug, publicConfig) {
  const aliases = publicConfig?.slug_aliases || {};
  return aliases[slug] || slug;
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.action === "getConfig") {
    chrome.storage.local.get(["config", "publicConfig"]).then(({ config, publicConfig }) => {
      sendResponse({
        config: config || DEFAULT_CONFIG,
        publicConfig: publicConfig || DEFAULT_PUBLIC_CONFIG,
      });
    });
    return true;
  }

  if (message.action === "resolveSlug") {
    chrome.storage.local.get("publicConfig").then(({ publicConfig }) => {
      sendResponse({
        slug: resolveSlug(message.slug, publicConfig || DEFAULT_PUBLIC_CONFIG),
      });
    });
    return true;
  }

  if (message.action === "saveConfig") {
    chrome.storage.local
      .set({ config: message.config })
      .then(() => refreshPublicConfig())
      .then(() => sendResponse({ success: true }));
    return true;
  }

  if (message.action === "recordSync") {
    chrome.storage.local.set({
      lastSync: {
        slug: message.slug,
        source: message.source,
        status: message.status,
        at: new Date().toISOString(),
      },
    });
    sendResponse({ success: true });
    return true;
  }

  if (message.action === "syncCompletion") {
    syncCompletion(message.payload)
      .then((result) => sendResponse(result))
      .catch((error) => sendResponse({ success: false, error: error.message }));
    return true;
  }
});

async function syncCompletion(payload) {
  const { config, publicConfig } = await chrome.storage.local.get([
    "config",
    "publicConfig",
  ]);
  const settings = config || DEFAULT_CONFIG;
  const pub = publicConfig || DEFAULT_PUBLIC_CONFIG;

  if (!settings.autoSync) {
    return { success: false, skipped: true, reason: "auto-sync disabled" };
  }

  const resolvedSlug = resolveSlug(payload.slug, pub);
  const dedupeKey = `${resolvedSlug}:${payload.submissionId || payload.submittedAt}`;
  const { syncedKeys = {} } = await chrome.storage.local.get("syncedKeys");
  if (syncedKeys[dedupeKey]) {
    return { success: true, skipped: true, reason: "already synced" };
  }

  const response = await fetch(`${settings.apiBaseUrl}/completions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": settings.apiKey,
    },
    body: JSON.stringify({
      slug: resolvedSlug,
      source: payload.source,
      confidence: payload.confidence ?? null,
    }),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`API error ${response.status}: ${detail}`);
  }

  const result = await response.json();
  syncedKeys[dedupeKey] = true;
  await chrome.storage.local.set({ syncedKeys });

  await chrome.storage.local.set({
    lastSync: {
      slug: resolvedSlug,
      source: payload.source,
      status: "synced",
      at: new Date().toISOString(),
      reviewStage: result.review_stage,
      confidence: payload.confidence,
    },
  });

  return { success: true, result };
}
