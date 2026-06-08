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
5. Optionally enable **Auto-sync accepted submissions**.

## Manual sync

On a LeetCode or NeetCode problem tab, open the popup and click **Mark current problem done**.

## Permissions

The extension requests access to `leetcode.com`, `neetcode.io`, and your configured API host only (`manifest.json`).
