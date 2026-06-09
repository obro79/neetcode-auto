# NeetCode SRS Chrome extension

Syncs accepted LeetCode / NeetCode submissions to the NeetCode Auto API.

## Load unpacked (development)

1. Open Chrome and go to `chrome://extensions`.
2. Enable **Developer mode** (top right).
3. Click **Load unpacked**.
4. Select this folder: `neetcode-auto/extension` (the directory that contains `manifest.json`).
5. Pin the extension from the puzzle icon if you want quick access.

## Configure

1. Click the extension icon to open the popup.
2. **API base URL** defaults to production: `https://neetcode-auto-production.up.railway.app`.
3. Paste your production **API key** (from Railway `API_KEY` — never commit this value).
4. Click **Save settings**.
5. Enable **Auto-sync accepted submissions**.

The extension fetches `GET /config/public` for LeetCode→catalog slug aliases.

## After Accepted

When a submission is accepted, a small panel asks how it went:

- **Struggling** / **Getting There** / **Solid** — syncs with confidence to `/completions`
- **Skip** — no sync

The extension uses a MAIN-world page hook (`pageHook.js`) to intercept submit responses:

- **LeetCode** — GraphQL submit/check responses
- **NeetCode** — Judge0-style responses (`status.id === 3`) plus `/api` and Firebase function calls, with a DOM fallback when the verdict panel shows **Accepted**

After updating the extension, click **Reload** on `chrome://extensions` and refresh any open problem tabs.

If the picker still does not appear, enable **Debug mode** in the popup, submit again, and check the page console for `[NeetCode SRS]` logs.

## Manual sync

On a LeetCode or NeetCode problem tab, open the popup and click **Mark current problem done** (same confidence picker flow via content script on next accepted solve, or immediate sync from popup).

## Permissions

The extension requests access to `leetcode.com`, `neetcode.io`, and your configured API host only (`manifest.json`).
