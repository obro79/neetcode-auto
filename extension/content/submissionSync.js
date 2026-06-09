(function () {
  const SOURCE = window.location.hostname.includes("neetcode.io")
    ? "neetcode"
    : "leetcode";

  const CONFIDENCE_OPTIONS = [
    { value: "struggling", label: "Struggling" },
    { value: "getting_there", label: "Getting There" },
    { value: "solid", label: "Solid" },
    { value: null, label: "Skip" },
  ];

  function slugFromUrl() {
    const match = window.location.pathname.match(/\/problems\/([^/]+)/);
    return match ? match[1] : null;
  }

  function notify(message, isError = false) {
    const existing = document.getElementById("neetcode-srs-toast");
    if (existing) existing.remove();

    const toast = document.createElement("div");
    toast.id = "neetcode-srs-toast";
    toast.textContent = message;
    Object.assign(toast.style, {
      position: "fixed",
      bottom: "20px",
      right: "20px",
      zIndex: "99999",
      padding: "12px 16px",
      borderRadius: "8px",
      color: "#fff",
      background: isError ? "#b42318" : "#027a48",
      fontFamily: "system-ui, sans-serif",
      fontSize: "14px",
      boxShadow: "0 8px 24px rgba(0,0,0,0.2)",
    });
    document.documentElement.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
  }

  function removeConfidencePicker() {
    const existing = document.getElementById("neetcode-srs-confidence");
    if (existing) existing.remove();
  }

  function showConfidencePicker(slug, submissionId) {
    removeConfidencePicker();

    const panel = document.createElement("div");
    panel.id = "neetcode-srs-confidence";
    Object.assign(panel.style, {
      position: "fixed",
      bottom: "72px",
      right: "20px",
      zIndex: "99999",
      padding: "12px",
      borderRadius: "10px",
      background: "#101828",
      color: "#fff",
      fontFamily: "system-ui, sans-serif",
      fontSize: "13px",
      boxShadow: "0 8px 24px rgba(0,0,0,0.25)",
      minWidth: "220px",
    });

    const title = document.createElement("p");
    title.textContent = "How did it go?";
    title.style.margin = "0 0 8px";
    panel.appendChild(title);

    const buttonRow = document.createElement("div");
    buttonRow.style.display = "flex";
    buttonRow.style.flexWrap = "wrap";
    buttonRow.style.gap = "6px";

    CONFIDENCE_OPTIONS.forEach((option) => {
      const button = document.createElement("button");
      button.textContent = option.label;
      Object.assign(button.style, {
        border: "1px solid #344054",
        background: option.value ? "#1d2939" : "#475467",
        color: "#fff",
        borderRadius: "6px",
        padding: "6px 8px",
        cursor: "pointer",
        fontSize: "12px",
      });
      button.addEventListener("click", () => {
        removeConfidencePicker();
        if (option.value === null) {
          notify("Skipped SRS sync");
          return;
        }
        postCompletion(slug, submissionId, option.value);
      });
      buttonRow.appendChild(button);
    });

    panel.appendChild(buttonRow);
    document.documentElement.appendChild(panel);
  }

  function postCompletion(slug, submissionId, confidence) {
    chrome.runtime.sendMessage(
      {
        action: "syncCompletion",
        payload: {
          slug,
          source: SOURCE,
          submissionId: submissionId || `${Date.now()}`,
          submittedAt: new Date().toISOString(),
          confidence,
        },
      },
      (response) => {
        if (chrome.runtime.lastError) {
          notify(`SRS sync failed: ${chrome.runtime.lastError.message}`, true);
          return;
        }
        if (response?.skipped) return;
        if (response?.success) {
          notify(`Synced ${slug} to NeetCode SRS`);
        } else {
          notify(response?.error || "SRS sync failed", true);
        }
      }
    );
  }

  function handleAccepted(submissionId) {
    const rawSlug = slugFromUrl();
    if (!rawSlug) return;

    chrome.runtime.sendMessage(
      { action: "resolveSlug", slug: rawSlug },
      (response) => {
        if (chrome.runtime.lastError) {
          showConfidencePicker(rawSlug, submissionId);
          return;
        }
        const slug = response?.slug || rawSlug;
        showConfidencePicker(slug, submissionId);
      }
    );
  }

  function applyDebugMode() {
    chrome.storage.local.get("config", ({ config }) => {
      if (config?.debugMode) {
        document.documentElement.setAttribute("data-neetcode-srs-debug", "1");
      } else {
        document.documentElement.removeAttribute("data-neetcode-srs-debug");
      }
    });
  }

  applyDebugMode();
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area === "local" && changes.config) {
      applyDebugMode();
    }
  });

  window.addEventListener("message", (event) => {
    if (event.source !== window) return;

    if (event.data?.type === "NEETCODE_SRS_ACCEPTED") {
      handleAccepted(event.data.submissionId || event.data.url || "accepted");
      return;
    }

    if (event.data?.type === "NEETCODE_SRS_DEBUG") {
      console.debug("[NeetCode SRS]", event.data.message, event.data.detail || "");
      return;
    }

    if (event.data?.type === "NEETCODE_SRS_MANUAL_SYNC") {
      handleAccepted("manual");
    }
  });
})();
