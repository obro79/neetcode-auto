const DEFAULT_CONFIG = {
  apiBaseUrl: "http://localhost:8000",
  apiKey: "dev-api-key-change-me",
  autoSync: true,
};

chrome.runtime.onInstalled.addListener(async () => {
  const stored = await chrome.storage.local.get("config");
  if (!stored.config) {
    await chrome.storage.local.set({ config: DEFAULT_CONFIG });
  }
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.action === "getConfig") {
    chrome.storage.local.get("config").then(({ config }) => {
      sendResponse({ config: config || DEFAULT_CONFIG });
    });
    return true;
  }

  if (message.action === "saveConfig") {
    chrome.storage.local.set({ config: message.config }).then(() => {
      sendResponse({ success: true });
    });
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
  const { config } = await chrome.storage.local.get("config");
  const settings = config || DEFAULT_CONFIG;

  if (!settings.autoSync) {
    return { success: false, skipped: true, reason: "auto-sync disabled" };
  }

  const dedupeKey = `${payload.slug}:${payload.submissionId || payload.submittedAt}`;
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
      slug: payload.slug,
      source: payload.source,
      confidence: null,
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
      slug: payload.slug,
      source: payload.source,
      status: "synced",
      at: new Date().toISOString(),
      reviewStage: result.review_stage,
    },
  });

  return { success: true, result };
}
