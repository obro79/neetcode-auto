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

  function isAcceptedSubmission(payload) {
    const text = typeof payload === "string" ? payload : JSON.stringify(payload);
    if (!text.includes("Accepted")) return false;

    try {
      const data = typeof payload === "string" ? JSON.parse(payload) : payload;
      const status =
        data?.data?.submit?.status ||
        data?.data?.check?.status ||
        data?.status ||
        data?.state;
      if (status) {
        return String(status).toLowerCase() === "accepted";
      }
    } catch (_error) {
      // Fall through to substring check.
    }

    return text.toLowerCase().includes('"accepted"') || text.includes("Accepted");
  }

  function requestUrl(input) {
    if (typeof input === "string") return input;
    if (input instanceof Request) return input.url;
    if (input?.url) return input.url;
    return String(input || "");
  }

  function isSubmissionResultUrl(url) {
    const u = String(url || "").toLowerCase();

    if (
      u.includes("executecodefunctionhttp") ||
      u.includes("/execute") ||
      u.includes("/run") ||
      u.includes("/test")
    ) {
      return false;
    }

    if (SOURCE === "leetcode" && u.includes("graphql")) {
      return true;
    }

    if (SOURCE === "neetcode") {
      return u.includes("submit") || u.includes("submissions");
    }

    return false;
  }

  async function inspectSubmissionResponse(response, url) {
    try {
      const bodyText = await response.text();
      if (isAcceptedSubmission(bodyText)) {
        handleAccepted(url);
      }
    } catch (_error) {
      // Ignore parse failures; never throw to caller.
    }
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

  async function handleAccepted(submissionId) {
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

  const originalFetch = window.fetch;
  window.fetch = async function (...args) {
    const url = requestUrl(args[0]);
    if (!isSubmissionResultUrl(url)) {
      return originalFetch.apply(this, args);
    }

    const res = await originalFetch.apply(this, args);
    void inspectSubmissionResponse(res.clone(), url);
    return res;
  };

  const originalOpen = XMLHttpRequest.prototype.open;
  const originalSend = XMLHttpRequest.prototype.send;

  XMLHttpRequest.prototype.open = function (method, url, ...rest) {
    this._neetcodeUrl = url;
    this._neetcodeIsSubmission = isSubmissionResultUrl(url);
    return originalOpen.call(this, method, url, ...rest);
  };

  XMLHttpRequest.prototype.send = function (...args) {
    if (this._neetcodeIsSubmission) {
      this.addEventListener("load", function () {
        void inspectSubmissionResponse(
          { text: async () => this.responseText },
          this._neetcodeUrl || ""
        );
      });
    }
    return originalSend.apply(this, args);
  };

  window.addEventListener("message", (event) => {
    if (event.source !== window) return;
    if (event.data?.type === "NEETCODE_SRS_MANUAL_SYNC") {
      handleAccepted("manual");
    }
  });
})();
