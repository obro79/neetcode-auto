(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const n of document.querySelectorAll('link[rel="modulepreload"]'))o(n);new MutationObserver(n=>{for(const a of n)if(a.type==="childList")for(const l of a.addedNodes)l.tagName==="LINK"&&l.rel==="modulepreload"&&o(l)}).observe(document,{childList:!0,subtree:!0});function r(n){const a={};return n.integrity&&(a.integrity=n.integrity),n.referrerPolicy&&(a.referrerPolicy=n.referrerPolicy),n.crossOrigin==="use-credentials"?a.credentials="include":n.crossOrigin==="anonymous"?a.credentials="omit":a.credentials="same-origin",a}function o(n){if(n.ep)return;n.ep=!0;const a=r(n);fetch(n.href,a)}})();const p="neetcode-dashboard-config";function v(){const e=localStorage.getItem(p);if(!e)return null;try{const t=JSON.parse(e);return!t.apiBaseUrl||!t.apiKey?null:{apiBaseUrl:t.apiBaseUrl.trim().replace(/\/$/,""),apiKey:t.apiKey.trim()}}catch{return null}}function b(e){localStorage.setItem(p,JSON.stringify({apiBaseUrl:e.apiBaseUrl.trim().replace(/\/$/,""),apiKey:e.apiKey.trim()}))}function $(){localStorage.removeItem(p)}async function c(e,t){const r=await fetch(`${e.apiBaseUrl}${t}`,{headers:{"X-API-Key":e.apiKey}});if(!r.ok){const o=await r.text();throw new Error(o||`Request failed (${r.status})`)}return await r.json()}async function w(e){return c(e,"/auth/verify")}async function S(e){return c(e,"/stats/summary")}async function _(e){return c(e,"/reviews/due?limit=50")}async function N(e){return c(e,"/daily-sets/today")}const g=document.querySelector("#app");if(!g)throw new Error("Missing #app root");const d=g;function s(e){return e.replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;")}function U(e){return e||"—"}function f(){const e=v();d.innerHTML=`
    <div class="login-card">
      <h1>NeetCode Dashboard</h1>
      <p>Connect to your NeetCode SRS API using the same base URL and API key as the browser extension.</p>
      <form id="login-form">
        <div class="field">
          <label for="apiBaseUrl">API base URL</label>
          <input id="apiBaseUrl" name="apiBaseUrl" placeholder="https://your-api.example.com" value="${s((e==null?void 0:e.apiBaseUrl)??"")}" required />
        </div>
        <div class="field">
          <label for="apiKey">API key</label>
          <input id="apiKey" name="apiKey" type="password" placeholder="X-API-Key" value="${s((e==null?void 0:e.apiKey)??"")}" required />
        </div>
        <button class="primary" type="submit">Connect</button>
      </form>
      <div id="status" class="status"></div>
    </div>
  `;const t=document.querySelector("#login-form"),r=document.querySelector("#status");t==null||t.addEventListener("submit",async o=>{if(o.preventDefault(),!r)return;r.textContent="Verifying…",r.className="status";const n=new FormData(t),a={apiBaseUrl:String(n.get("apiBaseUrl")??""),apiKey:String(n.get("apiKey")??"")};try{const l=await w(a);b(a),r.textContent=`Connected to ${l.app_name}`,r.className="status ok",await y(a)}catch(l){r.textContent=l instanceof Error?l.message:"Connection failed",r.className="status error"}})}function i(e,t){return`
    <div class="stat-card">
      <div class="label">${s(e)}</div>
      <div class="value">${s(String(t))}</div>
    </div>
  `}function C(e){return e.length===0?'<p class="empty">No reviews due right now.</p>':`
    <table>
      <thead>
        <tr>
          <th>Problem</th>
          <th>Pattern</th>
          <th>Due</th>
          <th>Confidence</th>
          <th>Stage</th>
        </tr>
      </thead>
      <tbody>${e.map(r=>{var o,n,a;return`
      <tr>
        <td><a href="${s(r.neetcode_url)}" target="_blank" rel="noreferrer">${s(r.title)}</a></td>
        <td>${s(r.pattern)}</td>
        <td>${U(((o=r.progress)==null?void 0:o.next_review)??null)}</td>
        <td>${s(((n=r.progress)==null?void 0:n.confidence)??"unset")}</td>
        <td><span class="badge due">${s(((a=r.progress)==null?void 0:a.review_stage)??"new")}</span></td>
      </tr>
    `}).join("")}</tbody>
    </table>
  `}function u(e){return e.length===0?'<p class="empty">None</p>':`
    <ul>
      ${e.map(t=>`
        <li>
          <a href="${s(t.neetcode_url)}" target="_blank" rel="noreferrer">${s(t.title)}</a>
          <span class="badge ${t.completed?"done":""}">${s(t.slot)}</span>
        </li>
      `).join("")}
    </ul>
  `}function L(e){return e.by_pattern.length===0?'<p class="empty">No pattern data yet.</p>':e.by_pattern.map(t=>{const r=t.total===0?0:Math.round(t.solved/t.total*100);return`
        <div class="pattern-row">
          <div>
            <div>${s(t.pattern)}</div>
            <div class="meta">${t.solved} / ${t.total} solved</div>
            <div class="progress-bar"><span style="width: ${r}%"></span></div>
          </div>
          <div>${r}%</div>
        </div>
      `}).join("")}function P(e,t,r,o){var n,a;d.innerHTML=`
    <header class="page-header">
      <div>
        <h1>NeetCode Dashboard</h1>
        <p>${s(e.apiBaseUrl)}</p>
      </div>
      <div class="toolbar">
        <button id="refresh-btn" type="button">Refresh</button>
        <button id="logout-btn" type="button">Disconnect</button>
      </div>
    </header>

    <section class="grid stats-grid">
      ${i("Total",t.total)}
      ${i("Solved",t.solved)}
      ${i("Unsolved",t.unsolved)}
      ${i("Due today",t.due_today)}
      ${i("Overdue",t.due_overdue)}
      ${i("Mastered",t.mastered)}
    </section>

    <section class="layout layout-two" style="margin-top: 1.25rem;">
      <div class="panel">
        <h2>Due for Review</h2>
        ${C(r)}
      </div>
      <div class="panel">
        <h2>Today's Set (${s(o.set_date)})</h2>
        <p><strong>Focus:</strong> ${s(o.focus_pattern??"None")}</p>
        <h3>Review</h3>
        ${u(o.review)}
        <h3>Focused New</h3>
        ${u(o.focused_new)}
        <h3>Random New</h3>
        ${u(o.random_new)}
      </div>
    </section>

    <section class="layout layout-two" style="margin-top: 1.25rem;">
      <div class="panel">
        <h2>Confidence</h2>
        <div class="confidence-grid">
          ${i("Struggling",t.by_confidence.struggling)}
          ${i("Getting there",t.by_confidence.getting_there)}
          ${i("Solid",t.by_confidence.solid)}
          ${i("Unset",t.by_confidence.unset)}
        </div>
      </div>
      <div class="panel">
        <h2>Review Stage</h2>
        <div class="stage-grid">
          ${Object.entries(t.by_review_stage).map(([l,m])=>i(l,m)).join("")}
        </div>
      </div>
    </section>

    <section class="panel" style="margin-top: 1.25rem;">
      <h2>Progress by Pattern</h2>
      ${L(t)}
    </section>
  `,(n=document.querySelector("#refresh-btn"))==null||n.addEventListener("click",()=>{y(e)}),(a=document.querySelector("#logout-btn"))==null||a.addEventListener("click",()=>{$(),f()})}async function y(e){var t;d.innerHTML='<p class="empty">Loading dashboard…</p>';try{const[r,o,n]=await Promise.all([S(e),_(e),N(e)]);P(e,r,o,n)}catch(r){d.innerHTML=`
      <div class="panel">
        <h2>Failed to load dashboard</h2>
        <p class="status error">${s(r instanceof Error?r.message:"Unknown error")}</p>
        <button id="retry-login" type="button">Back to login</button>
      </div>
    `,(t=document.querySelector("#retry-login"))==null||t.addEventListener("click",f)}}const h=v();h?y(h):f();
