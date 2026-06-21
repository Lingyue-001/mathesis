import { collectNodeDisplayRows, buildUnifiedEntryName } from "./nodeEntrySchema.js";

const DEFAULT_EXCLUDE_KEYS = new Set(["name_sa", "transliteration", "name_zh", "name_en"]);
const PANEL_STYLE_ID = "node-entry-popup-style";
const DEFAULT_NODE_HIT_SINGLE_CLICK_DELAY_MS = 300;

function escapeHtml(input) {
  return String(input || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function injectPopupStyle() {
  if (document.getElementById(PANEL_STYLE_ID)) return;
  const style = document.createElement("style");
  style.id = PANEL_STYLE_ID;
  style.textContent = `
    .node-entry-panel.side-left {
      --detail-panel-enter-x: -110%;
    }
    .node-entry-panel.side-right {
      --detail-panel-enter-x: 110%;
    }
    .node-entry-panel.is-dragging {
      transition: none;
      user-select: none;
    }
    .node-entry-panel.is-resizing {
      transition: none;
      user-select: none;
    }
    .node-entry-resize-handle {
      position: absolute;
      top: 0.65rem;
      bottom: 0.65rem;
      width: 12px;
      z-index: 4;
      cursor: ew-resize;
      border-radius: 6px;
      opacity: 0;
      transition: opacity 0.15s ease;
    }
    .node-entry-panel:hover .node-entry-resize-handle {
      opacity: 1;
    }
    .node-entry-panel.side-left .node-entry-resize-handle {
      right: -6px;
      background: linear-gradient(90deg, rgba(74, 62, 48, 0.05), rgba(74, 62, 48, 0.2));
    }
    .node-entry-panel.side-right .node-entry-resize-handle {
      left: -6px;
      background: linear-gradient(270deg, rgba(74, 62, 48, 0.05), rgba(74, 62, 48, 0.2));
    }
    .node-entry-badge {
      font-size: 0.82rem;
      color: #6a5742;
      margin: 0 0 0.5rem;
    }
    .node-entry-badge code {
      font-family: "SFMono-Regular", Menlo, Monaco, Consolas, "Liberation Mono", monospace;
      background: rgba(118, 90, 47, 0.1);
      padding: 0.08rem 0.26rem;
      border-radius: 4px;
      color: #5d431e;
      font-size: 0.82rem;
    }
  `;
  document.head.appendChild(style);
}

export function makePanelDraggable(panel) {
  const handle = panel.querySelector(".detail-panel-head");
  if (!(handle instanceof HTMLElement)) return;
  if (panel.dataset.dragBound === "1") return;
  panel.dataset.dragBound = "1";

  let dragging = false;
  let offsetX = 0;
  let offsetY = 0;

  const onMove = (event) => {
    if (!dragging) return;
    const rect = panel.getBoundingClientRect();
    const margin = 8;
    const nextX = clamp(event.clientX - offsetX, margin, window.innerWidth - rect.width - margin);
    const nextY = clamp(event.clientY - offsetY, margin, window.innerHeight - rect.height - margin);
    panel.style.left = `${nextX}px`;
    panel.style.top = `${nextY}px`;
    panel.style.right = "auto";
  };

  const stop = () => {
    if (!dragging) return;
    dragging = false;
    panel.classList.remove("is-dragging");
    window.removeEventListener("pointermove", onMove);
    window.removeEventListener("pointerup", stop);
  };

  handle.addEventListener("pointerdown", (event) => {
    if (event.button !== 0) return;
    if (event.target instanceof Element && event.target.closest(".detail-panel-close")) return;
    event.preventDefault();
    const rect = panel.getBoundingClientRect();
    dragging = true;
    offsetX = event.clientX - rect.left;
    offsetY = event.clientY - rect.top;
    panel.classList.add("is-dragging");
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", stop);
  });
}

function makePanelResizable(panel) {
  const handle = panel.querySelector(".node-entry-resize-handle");
  if (!(handle instanceof HTMLElement)) return;
  if (panel.dataset.resizeBound === "1") return;
  panel.dataset.resizeBound = "1";

  let resizing = false;
  let startX = 0;
  let startWidth = 0;

  const onMove = (event) => {
    if (!resizing) return;
    const side = panel.classList.contains("side-left") ? "left" : "right";
    const dx = event.clientX - startX;
    const nextWidth = side === "left" ? startWidth + dx : startWidth - dx;
    const clampedWidth = clamp(nextWidth, 260, Math.max(260, window.innerWidth * 0.46));
    panel.style.width = `${clampedWidth}px`;
  };

  const stop = () => {
    if (!resizing) return;
    resizing = false;
    panel.classList.remove("is-resizing");
    window.removeEventListener("pointermove", onMove);
    window.removeEventListener("pointerup", stop);
  };

  handle.addEventListener("pointerdown", (event) => {
    if (event.button !== 0) return;
    event.preventDefault();
    resizing = true;
    startX = event.clientX;
    startWidth = panel.getBoundingClientRect().width;
    panel.classList.add("is-resizing");
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", stop);
  });
}

export function openPanelWithEnterAnimation(panel) {
  if (!(panel instanceof HTMLElement)) return;
  if (panel.classList.contains("is-open")) return;
  requestAnimationFrame(() => {
    panel.classList.add("is-open");
  });
}

export function bindDetailPanelOutsideDismiss({ panel, ignoreSelector = "" } = {}) {
  if (!(panel instanceof HTMLElement)) return;
  if (panel.dataset.outsideDismissBound === "1") return;
  panel.dataset.outsideDismissBound = "1";

  document.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof Element)) return;
    if (!panel.classList.contains("is-open")) return;
    if (panel.contains(target)) return;
    if (ignoreSelector && target.closest?.(ignoreSelector)) return;
    panel.classList.remove("is-open");
  });
}

function ensurePopupPanel(options) {
  injectPopupStyle();
  const {
    panelId = "nodeEntryPanel",
    panelTitle = "Node Details",
    emptyText = "Click a highlighted matched node to view details.",
    panelPosition = null
  } = options || {};

  let panel = document.getElementById(panelId);
  if (panel) return panel;

  panel = document.createElement("aside");
  panel.id = panelId;
  panel.className = "detail-panel node-entry-panel";
  const side = panelPosition && typeof panelPosition === "object" && Object.prototype.hasOwnProperty.call(panelPosition, "left")
    ? "side-left"
    : "side-right";
  panel.classList.add(side);
  panel.innerHTML = `
    <div class="detail-panel-head">
      <div class="detail-panel-title">${escapeHtml(panelTitle)}</div>
      <button class="detail-panel-close" type="button" aria-label="Close">&times;</button>
    </div>
    <div class="detail-panel-body">
      <p class="detail-panel-empty">${escapeHtml(emptyText)}</p>
    </div>
    <div class="node-entry-resize-handle" aria-hidden="true"></div>
  `;
  document.body.appendChild(panel);
  if (panelPosition && typeof panelPosition === "object") {
    if (Object.prototype.hasOwnProperty.call(panelPosition, "left")) {
      panel.style.left = panelPosition.left;
      panel.style.right = "auto";
    }
    if (Object.prototype.hasOwnProperty.call(panelPosition, "right")) {
      panel.style.right = panelPosition.right;
    }
    if (Object.prototype.hasOwnProperty.call(panelPosition, "top")) {
      panel.style.top = panelPosition.top;
    }
    if (Object.prototype.hasOwnProperty.call(panelPosition, "bottom")) {
      panel.style.bottom = panelPosition.bottom;
    }
  }
  panel.querySelector(".detail-panel-close")?.addEventListener("click", () => {
    panel.classList.remove("is-open");
  });
  makePanelDraggable(panel);
  makePanelResizable(panel);
  return panel;
}

function renderPanelContent(panel, node, clickedForm, options = {}) {
  const body = panel.querySelector(".detail-panel-body");
  if (!body) return;
  const properties = node?.properties || {};
  const rows = collectNodeDisplayRows(properties, {
    excludeKeys: options.excludeKeys || DEFAULT_EXCLUDE_KEYS,
    valueFilter: options.valueFilter || null
  });
  const rowsHtml = rows
    .map((row) => `<div class="entry-card-row"><strong>${escapeHtml(row.label)}:</strong> ${row.isReference ? `<em>${escapeHtml(row.value)}</em>` : escapeHtml(row.value)}</div>`)
    .join("");

  body.innerHTML = `
    <div class="node-entry-badge">Matched form: <code>${escapeHtml(clickedForm || "(unknown)")}</code></div>
    <div class="entry-card">
      <h3 class="entry-card-title">${escapeHtml(buildUnifiedEntryName(properties))}</h3>
      ${rowsHtml || "<p><em>No fields available.</em></p>"}
    </div>
  `;
}

export function bindNodeHitPopup(options = {}) {
  const {
    root,
    hitSelector = ".tei-node-hit",
    resolveNode,
    getMatchedText = ({ hit }) => (hit?.textContent || "").trim(),
    panelId = "nodeEntryPanel",
    panelTitle = "Node Details",
    emptyText = "Click a highlighted matched node to view details.",
    panelPosition = null,
    excludeKeys = DEFAULT_EXCLUDE_KEYS,
    valueFilter = null,
    stopPropagation = false,
    deferSingleClickMs = DEFAULT_NODE_HIT_SINGLE_CLICK_DELAY_MS
  } = options;

  if (!(root instanceof Element)) return;
  if (typeof resolveNode !== "function") return;

  const bindKey = `nodePopupBound_${panelId}`;
  if (root.dataset[bindKey] === "1") return;
  root.dataset[bindKey] = "1";

  const activate = async (hit, event) => {
    const term = getMatchedText({ hit, event });
    try {
      const node = await resolveNode({ hit, term, event });
      if (!node) return;
      const panel = ensurePopupPanel({ panelId, panelTitle, emptyText, panelPosition });
      renderPanelContent(panel, node, term, { excludeKeys, valueFilter });
      openPanelWithEnterAnimation(panel);
    } catch (err) {
      console.warn("[Node popup] failed:", err);
    }
  };

  let pendingClickTimer = null;
  root.addEventListener("click", (event) => {
    const hit = event.target?.closest?.(hitSelector);
    if (!hit || !root.contains(hit)) return;
    if (stopPropagation) event.stopPropagation();

    if (deferSingleClickMs > 0) {
      // Browsers fire click before dblclick; treat multi-click as a signal to cancel
      // the pending single-click action instead of scheduling it again.
      if ((event.detail || 0) > 1) {
        if (pendingClickTimer) {
          window.clearTimeout(pendingClickTimer);
          pendingClickTimer = null;
        }
        return;
      }
      if (pendingClickTimer) {
        window.clearTimeout(pendingClickTimer);
      }
      pendingClickTimer = window.setTimeout(() => {
        pendingClickTimer = null;
        activate(hit, event);
      }, deferSingleClickMs);
      return;
    }

    activate(hit, event);
  });

  if (deferSingleClickMs > 0) {
    root.addEventListener("dblclick", (event) => {
      const hit = event.target?.closest?.(hitSelector);
      if (!hit || !root.contains(hit)) return;
      if (pendingClickTimer) {
        window.clearTimeout(pendingClickTimer);
        pendingClickTimer = null;
      }
    });
  }

  document.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof Element)) return;
    const panel = document.getElementById(panelId);
    if (!(panel instanceof HTMLElement) || !panel.classList.contains("is-open")) return;
    if (panel.contains(target)) return;
    const hit = target.closest?.(hitSelector);
    if (hit && root.contains(hit)) return;
    panel.classList.remove("is-open");
  });
}

export function resolveNodeByTerm(nodes, term, options = {}) {
  const list = Array.isArray(nodes) ? nodes : [];
  const fields = Array.isArray(options.fields) && options.fields.length
    ? options.fields
    : ["name", "name_zh", "name_zh_simple", "name_en", "name_sa", "transliteration", "original_text_tr", "original_text_zh"];
  const normalizer = typeof options.normalizer === "function"
    ? options.normalizer
    : (value) => String(value || "").trim().toLowerCase().replace(/\s+/g, " ");

  const target = normalizer(term);
  if (!target) return null;

  let best = null;
  let bestScore = -1;

  for (const node of list) {
    const p = node?.properties || {};
    let score = 0;
    for (const key of fields) {
      const value = normalizer(p[key]);
      if (!value) continue;
      if (value === target) score += 10;
      else if (value.includes(target)) score += 4;
      else if (target.includes(value) && value.length >= 2) score += 2;
    }
    if (score > bestScore) {
      bestScore = score;
      best = node;
    }
  }

  return bestScore > 0 ? best : null;
}
