const apiBaseUrlInput = document.getElementById("apiBaseUrl");
const apiKeyInput = document.getElementById("apiKey");
const autoSyncInput = document.getElementById("autoSync");
const saveBtn = document.getElementById("saveBtn");
const manualBtn = document.getElementById("manualBtn");
const statusEl = document.getElementById("status");
const lastSyncEl = document.getElementById("lastSync");

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.style.color = isError ? "#ff8f8f" : "#8dffb0";
}

async function loadConfig() {
  const { config, lastSync } = await chrome.storage.local.get([
    "config",
    "lastSync",
  ]);
  if (config) {
    apiBaseUrlInput.value = config.apiBaseUrl || "";
    apiKeyInput.value = config.apiKey || "";
    autoSyncInput.checked = Boolean(config.autoSync);
  }
  if (lastSync) {
    lastSyncEl.textContent = `Last sync: ${lastSync.slug} (${lastSync.status}) at ${lastSync.at}`;
  }
}

saveBtn.addEventListener("click", async () => {
  const config = {
    apiBaseUrl: apiBaseUrlInput.value.trim().replace(/\/$/, ""),
    apiKey: apiKeyInput.value.trim(),
    autoSync: autoSyncInput.checked,
  };
  await chrome.storage.local.set({ config });
  setStatus("Settings saved");
});

manualBtn.addEventListener("click", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) {
    setStatus("No active tab", true);
    return;
  }

  const slugMatch = tab.url?.match(/\/problems\/([^/?#]+)/);
  if (!slugMatch) {
    setStatus("Open a LeetCode or NeetCode problem page", true);
    return;
  }

  const slug = slugMatch[1];
  const source = tab.url.includes("neetcode.io") ? "neetcode" : "leetcode";

  chrome.runtime.sendMessage(
    {
      action: "syncCompletion",
      payload: {
        slug,
        source,
        submissionId: `manual-${Date.now()}`,
      },
    },
    (response) => {
      if (chrome.runtime.lastError) {
        setStatus(chrome.runtime.lastError.message, true);
        return;
      }
      if (response?.success) {
        setStatus(`Marked ${slug} done`);
        loadConfig();
      } else {
        setStatus(response?.error || "Sync failed", true);
      }
    }
  );
});

loadConfig();
