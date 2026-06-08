(function () {
  const SOURCE = window.location.hostname.includes("neetcode.io")
    ? "neetcode"
    : "leetcode";

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

  async function handleAccepted(submissionId) {
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
