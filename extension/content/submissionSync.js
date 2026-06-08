(function () {
  const SOURCE = window.location.hostname.includes("neetcode.io")
    ? "neetcode"
    : "leetcode";

  const EXECUTION_ENDPOINTS = /executecodefunctionhttp|runcodefunctionhttp/i;

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

  function handleAccepted(submissionId) {
    const slug = slugFromUrl();
    if (!slug) return;

    chrome.runtime.sendMessage(
      {
        action: "syncCompletion",
        payload: {
          slug,
          source: SOURCE,
          submissionId: submissionId || `${Date.now()}`,
          submittedAt: new Date().toISOString(),
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

  function requestUrl(input) {
    if (typeof input === "string") return input;
    if (input instanceof Request) return input.url;
    return String(input?.url || input || "");
  }

  function isExecutionEndpoint(url) {
    return EXECUTION_ENDPOINTS.test(String(url));
  }

  function isNeetCodeSubmissionUrl(url) {
    const lower = String(url).toLowerCase();
    if (!lower.includes("neetcode.io") && !lower.includes("/api/")) {
      return false;
    }
    return /submit|submission/i.test(lower);
  }

  function isLeetCodeGraphqlSubmissionBody(body) {
    if (body == null) return false;
    const normalized = String(body).toLowerCase();
    return (
      normalized.includes("submit") ||
      (normalized.includes("check") && normalized.includes("submission"))
    );
  }

  function shouldInspectFetch(url, body) {
    if (isExecutionEndpoint(url)) return false;
    if (isNeetCodeSubmissionUrl(url)) return true;
    if (/leetcode\.com/i.test(url) && /graphql/i.test(url)) {
      return isLeetCodeGraphqlSubmissionBody(body);
    }
    return false;
  }

  function shouldInspectXhr(url, body) {
    if (isExecutionEndpoint(url)) return false;
    if (isNeetCodeSubmissionUrl(url)) return true;
    if (/leetcode\.com/i.test(url) && /graphql/i.test(url)) {
      return isLeetCodeGraphqlSubmissionBody(body);
    }
    return false;
  }

  function inspectResponseText(url, bodyText) {
    if (!isAcceptedSubmission(bodyText)) return;

    if (/leetcode\.com/i.test(url) && /graphql/i.test(url)) {
      const lower = bodyText.toLowerCase();
      if (!lower.includes("submit") && !lower.includes("check")) return;
    }

    handleAccepted(url);
  }

  const originalFetch = window.fetch.bind(window);
  window.fetch = function (input, init) {
    const url = requestUrl(input);
    const body =
      init?.body != null && typeof init.body === "string" ? init.body : null;

    if (!shouldInspectFetch(url, body)) {
      return originalFetch(input, init);
    }

    return originalFetch(input, init).then(
      (response) => {
        try {
          const clone = response.clone();
          return clone.text().then((bodyText) => {
            inspectResponseText(url, bodyText);
            return response;
          });
        } catch (_error) {
          return response;
        }
      },
      (error) => Promise.reject(error)
    );
  };

  const originalOpen = XMLHttpRequest.prototype.open;
  const originalSend = XMLHttpRequest.prototype.send;

  XMLHttpRequest.prototype.open = function (method, url, ...rest) {
    this._neetcodeUrl = String(url || "");
    return originalOpen.call(this, method, url, ...rest);
  };

  XMLHttpRequest.prototype.send = function (...args) {
    const url = this._neetcodeUrl || "";
    const body = args[0];

    if (shouldInspectXhr(url, body)) {
      this.addEventListener("load", function () {
        try {
          inspectResponseText(url, this.responseText);
        } catch (_error) {
          // Ignore parse failures.
        }
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
