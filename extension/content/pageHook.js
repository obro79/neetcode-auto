(function () {
  "use strict";

  const MESSAGE_TYPE = "NEETCODE_SRS_ACCEPTED";
  const DEBUG_TYPE = "NEETCODE_SRS_DEBUG";

  const SOURCE = window.location.hostname.includes("neetcode.io")
    ? "neetcode"
    : "leetcode";

  const SUBMISSION_GRAPHQL_OPS = [
    "submitsolution",
    "submit",
    "checksolution",
    "check",
    "submissiondetails",
    "syncuserprogress",
    "interpret",
    "judger",
  ];

  const recentAccepted = new Set();

  function requestUrl(input) {
    if (typeof input === "string") return input;
    if (input instanceof Request) return input.url;
    if (input?.url) return input.url;
    return String(input || "");
  }

  function isDebugEnabled() {
    return document.documentElement.getAttribute("data-neetcode-srs-debug") === "1";
  }

  function debugLog(message, detail) {
    if (!isDebugEnabled()) return;
    window.postMessage(
      {
        type: DEBUG_TYPE,
        message,
        detail,
        at: new Date().toISOString(),
      },
      "*"
    );
  }

  function parseRequestBody(body) {
    if (!body) return null;
    const text = typeof body === "string" ? body : "";
    if (!text) return null;
    try {
      return JSON.parse(text);
    } catch (_error) {
      return null;
    }
  }

  function isSubmissionGraphqlRequest(body) {
    const parsed = parseRequestBody(body);
    if (!parsed) return false;

    const op = String(parsed.operationName || "").toLowerCase();
    const query = String(parsed.query || "").toLowerCase();
    return SUBMISSION_GRAPHQL_OPS.some(
      (name) => op.includes(name) || query.includes(name)
    );
  }

  function isExcludedUrl(url) {
    const u = String(url || "").toLowerCase();
    return (
      u.includes("executecodefunctionhttp") ||
      u.includes("/test") ||
      u.includes("firebase") ||
      u.includes("googleapis.com") ||
      u.includes("analytics") ||
      u.includes("posthog") ||
      u.includes("sentry")
    );
  }

  function isNeetcodeSubmissionUrl(url) {
    const u = String(url || "").toLowerCase();
    if (isExcludedUrl(u)) return false;

    if (
      u.includes("submission") ||
      u.includes("submit") ||
      u.includes("cloudfunctions.net") ||
      u.includes("judge0") ||
      u.includes("/judge")
    ) {
      return true;
    }

    if (u.includes("/api/")) {
      return /\/api\/[^?#]*(code|run|submit|judge|submission|execute|grade|verdict)/i.test(
        u
      );
    }

    return false;
  }

  function isLeetcodeSubmissionUrl(url) {
    const u = String(url || "").toLowerCase();
    if (isExcludedUrl(u)) return false;
    return (
      u.includes("graphql") ||
      u.includes("/submit") ||
      u.includes("/submissions")
    );
  }

  function isSubmissionResultUrl(url) {
    if (SOURCE === "leetcode") {
      return isLeetcodeSubmissionUrl(url);
    }
    if (SOURCE === "neetcode") {
      return isNeetcodeSubmissionUrl(url);
    }
    return false;
  }

  function statusLooksAccepted(value) {
    if (value == null) return false;
    const normalized = String(value).trim().toLowerCase();
    return normalized === "accepted" || normalized === "ac";
  }

  function judge0StatusAccepted(status) {
    if (!status || typeof status !== "object") return false;
    if (status.id === 3) return true;
    return statusLooksAccepted(status.description);
  }

  function nodeLooksAccepted(node, depth = 0) {
    if (!node || typeof node !== "object" || depth > 6) return false;

    if (node.status_code === 10) return true;
    if (statusLooksAccepted(node.status)) return true;
    if (statusLooksAccepted(node.status_msg)) return true;
    if (judge0StatusAccepted(node.status)) return true;

    if (Array.isArray(node.submissions)) {
      return node.submissions.some((child) => nodeLooksAccepted(child, depth + 1));
    }

    const candidates = [
      node.submit,
      node.check,
      node.submissionDetails,
      node.submitSubmission,
      node.judger,
      node.data,
      node.result,
      node.verdict,
    ];

    return candidates.some((child) => nodeLooksAccepted(child, depth + 1));
  }

  function extractSubmissionId(payload) {
    if (!payload || typeof payload !== "object") return null;

    const paths = [
      payload?.token,
      payload?.data?.submit?.submission_id,
      payload?.data?.submitSubmission?.submissionId,
      payload?.data?.submissionDetails?.submissionId,
      payload?.submission_id,
      payload?.submissionId,
    ];

    for (const value of paths) {
      if (value != null && String(value).length > 0) {
        return String(value);
      }
    }
    return null;
  }

  function isAcceptedSubmission(bodyText) {
    if (!bodyText) return false;

    try {
      const payload = JSON.parse(bodyText);
      if (nodeLooksAccepted(payload)) return true;
    } catch (_error) {
      // Fall through to regex checks.
    }

    return (
      /"status"\s*:\s*"(Accepted|AC)"/i.test(bodyText) ||
      /"status_msg"\s*:\s*"Accepted"/i.test(bodyText) ||
      /"status_code"\s*:\s*10\b/.test(bodyText) ||
      /"description"\s*:\s*"Accepted"/i.test(bodyText) ||
      /"status"\s*:\s*\{\s*"id"\s*:\s*3\b/.test(bodyText)
    );
  }

  function shouldHandleAccepted(submissionId, url) {
    const key = submissionId || url || `${Date.now()}`;
    if (recentAccepted.has(key)) return false;
    recentAccepted.add(key);
    setTimeout(() => recentAccepted.delete(key), 15000);
    return true;
  }

  function emitAccepted(url, bodyText, source = "network") {
    let submissionId = null;
    try {
      submissionId = extractSubmissionId(JSON.parse(bodyText || "{}"));
    } catch (_error) {
      submissionId = null;
    }

    if (!shouldHandleAccepted(submissionId || source, url)) {
      debugLog("Skipped duplicate accepted event", { url, submissionId, source });
      return;
    }

    debugLog("Accepted submission detected", { url, submissionId, source });
    window.postMessage(
      {
        type: MESSAGE_TYPE,
        submissionId,
        source: SOURCE,
        url,
        detectSource: source,
      },
      "*"
    );
  }

  async function inspectSubmissionResponse(response, url, requestBody) {
    try {
      if (
        SOURCE === "leetcode" &&
        url.toLowerCase().includes("graphql") &&
        !isSubmissionGraphqlRequest(requestBody)
      ) {
        return;
      }

      const bodyText = await response.text();
      debugLog("Inspecting submission response", {
        url,
        accepted: isAcceptedSubmission(bodyText),
      });

      if (isAcceptedSubmission(bodyText)) {
        emitAccepted(url, bodyText, "network");
      }
    } catch (_error) {
      // Never throw back to the page.
    }
  }

  function startNeetcodeDomWatcher() {
    if (SOURCE !== "neetcode") return;

    let debounceTimer = null;

    function elementShowsAccepted(el) {
      if (!(el instanceof HTMLElement)) return false;
      if (!el.offsetParent && el !== document.body) return false;

      const text = (el.textContent || "").trim();
      if (!text) return false;
      if (text.length > 80) return false;

      return (
        text === "Accepted" ||
        /^Accepted\b/i.test(text) ||
        /^✓\s*Accepted/i.test(text) ||
        /^✔\s*Accepted/i.test(text)
      );
    }

    function scanForAcceptedVerdict() {
      const matches = document.querySelectorAll(
        '[class*="verdict"], [class*="result"], [class*="status"], [class*="submission"], [class*="output"], [class*="judge"], [data-testid*="result"], [data-testid*="verdict"]'
      );

      for (const el of matches) {
        if (elementShowsAccepted(el)) {
          emitAccepted("dom", null, "dom");
          return;
        }
      }

      const leaves = document.querySelectorAll("span, div, p, strong, h1, h2, h3, h4");
      for (const el of leaves) {
        if (el.children.length > 0) continue;
        if (elementShowsAccepted(el)) {
          emitAccepted("dom", null, "dom");
          return;
        }
      }
    }

    const observer = new MutationObserver(() => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(scanForAcceptedVerdict, 400);
    });

    observer.observe(document.documentElement, {
      childList: true,
      subtree: true,
      characterData: true,
    });
  }

  const originalFetch = window.fetch;
  window.fetch = async function (...args) {
    const url = requestUrl(args[0]);
    const requestBody = args[1]?.body;
    const shouldInspect =
      isSubmissionResultUrl(url) &&
      (SOURCE !== "leetcode" ||
        !url.toLowerCase().includes("graphql") ||
        isSubmissionGraphqlRequest(requestBody));

    if (shouldInspect) {
      debugLog("Hooked fetch", { url });
    }

    const res = await originalFetch.apply(this, args);

    if (shouldInspect) {
      void inspectSubmissionResponse(res.clone(), url, requestBody);
    }

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
    const requestBody = args[0];
    if (this._neetcodeIsSubmission) {
      debugLog("Hooked xhr", { url: this._neetcodeUrl });
      this.addEventListener("load", function () {
        void inspectSubmissionResponse(
          { text: async () => this.responseText },
          this._neetcodeUrl || "",
          requestBody
        );
      });
    }
    return originalSend.apply(this, args);
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", startNeetcodeDomWatcher, {
      once: true,
    });
  } else {
    startNeetcodeDomWatcher();
  }
})();
