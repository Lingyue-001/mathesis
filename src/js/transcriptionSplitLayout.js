const SPLIT_LAYOUT_STYLE_ID = "transcription-split-layout-style";

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function injectSplitLayoutStyle() {
  if (document.getElementById(SPLIT_LAYOUT_STYLE_ID)) return;

  const style = document.createElement("style");
  style.id = SPLIT_LAYOUT_STYLE_ID;
  style.textContent = `
    .transcription-layout.transcription-split-layout {
      position: relative;
      --transcription-main-size: 57%;
      --transcription-split-gap: 16px;
      --transcription-splitter-width: 18px;
      --transcription-split-content-pad: calc(var(--transcription-split-gap) / 2);
    }
    .transcription-layout.transcription-split-layout.is-split-active {
      grid-template-columns: minmax(0, var(--transcription-main-size)) minmax(0, 1fr);
    }
    .transcription-layout.transcription-split-layout.is-split-active .transcription-main {
      padding-right: var(--transcription-split-content-pad);
      box-sizing: border-box;
    }
    .transcription-layout.transcription-split-layout.is-split-active .transcription-viewer {
      border-left: none;
      padding-left: var(--transcription-split-content-pad);
      box-sizing: border-box;
    }
    .transcription-splitter-handle {
      position: absolute;
      top: 0;
      bottom: 0;
      left: calc(
        var(--transcription-main-size)
        + (var(--transcription-split-gap) / 2)
        - (var(--transcription-splitter-width) / 2)
      );
      width: var(--transcription-splitter-width);
      padding: 0;
      border: none;
      background: transparent;
      cursor: col-resize;
      z-index: 8;
      touch-action: none;
    }
    .transcription-splitter-handle::before {
      content: "";
      position: absolute;
      top: 0.5rem;
      bottom: 0.5rem;
      left: 50%;
      width: 1px;
      transform: translateX(-50%);
      background: linear-gradient(
        180deg,
        rgba(var(--editorial-mark-brown-rgb, 134, 88, 43), 0),
        rgba(var(--editorial-mark-brown-rgb, 134, 88, 43), 0.24) 14%,
        rgba(var(--editorial-mark-brown-rgb, 134, 88, 43), 0.38) 50%,
        rgba(var(--editorial-mark-brown-rgb, 134, 88, 43), 0.24) 86%,
        rgba(var(--editorial-mark-brown-rgb, 134, 88, 43), 0)
      );
      opacity: 0.62;
      transition: background 0.2s ease, opacity 0.2s ease;
    }
    .transcription-splitter-handle:hover::before,
    .transcription-splitter-handle:focus-visible::before,
    .transcription-layout.transcription-split-layout.is-split-dragging .transcription-splitter-handle::before {
      background: linear-gradient(
        180deg,
        rgba(var(--editorial-mark-brown-rgb, 134, 88, 43), 0),
        rgba(var(--editorial-mark-brown-rgb, 134, 88, 43), 0.44) 14%,
        rgba(var(--editorial-mark-brown-rgb, 134, 88, 43), 0.68) 50%,
        rgba(var(--editorial-mark-brown-rgb, 134, 88, 43), 0.44) 86%,
        rgba(var(--editorial-mark-brown-rgb, 134, 88, 43), 0)
      );
      opacity: 1;
    }
    .transcription-layout.transcription-split-layout:not(.is-split-active) .transcription-splitter-handle {
      display: none;
    }
    .transcription-layout.transcription-split-layout.is-split-dragging,
    .transcription-layout.transcription-split-layout.is-split-dragging * {
      cursor: col-resize !important;
      user-select: none !important;
    }
  `;
  document.head.appendChild(style);
}

function getGapPx(layout) {
  const styles = getComputedStyle(layout);
  const value = parseFloat(styles.columnGap || styles.gap || "16");
  return Number.isFinite(value) ? value : 16;
}

function getDesktopBounds(layout, options = {}) {
  const rect = layout.getBoundingClientRect();
  const gapPx = getGapPx(layout);
  const usableWidth = Math.max(0, rect.width - gapPx);
  const preferredMinMain = Number(options.minMainPx) || 480;
  const preferredMinSide = Number(options.minSidePx) || 340;

  let minMain = Math.min(preferredMinMain, Math.max(280, usableWidth * 0.38));
  let minSide = Math.min(preferredMinSide, Math.max(240, usableWidth * 0.3));
  if (minMain + minSide > usableWidth) {
    minMain = Math.max(240, usableWidth * 0.52);
    minSide = Math.max(220, usableWidth - minMain);
  }

  const maxMain = Math.max(minMain, usableWidth - minSide);
  return { rect, gapPx, usableWidth, minMain, maxMain };
}

export function bindTranscriptionSplitLayout(options = {}) {
  const layout = options.layout instanceof HTMLElement ? options.layout : null;
  const main = options.main instanceof HTMLElement ? options.main : null;
  const side = options.side instanceof HTMLElement ? options.side : null;
  if (!layout || !main || !side) {
    return { sync() {}, destroy() {} };
  }

  injectSplitLayoutStyle();

  const mobileQuery = options.mobileQuery || null;
  const initialMainRatio = Number(options.initialMainRatio) > 0 ? Number(options.initialMainRatio) : 0.57;
  layout.classList.add("transcription-split-layout");

  let currentRatio = null;
  let dragging = false;
  let handle = layout.querySelector(".transcription-splitter-handle");

  if (!(handle instanceof HTMLButtonElement)) {
    handle = document.createElement("button");
    handle.type = "button";
    handle.className = "transcription-splitter-handle hover-tooltip";
    handle.setAttribute("aria-label", "Resize transcription panels");
    layout.appendChild(handle);
  }
  handle.classList.add("hover-tooltip");
  handle.dataset.tooltip = "Drag to resize panels";

  function isDesktopActive() {
    if (mobileQuery?.matches) return false;
    return main.parentElement === layout && side.parentElement === layout;
  }

  function setMainWidth(mainWidthPx) {
    const bounds = getDesktopBounds(layout, options);
    if (bounds.usableWidth <= 0) return;
    const clamped = clamp(mainWidthPx, bounds.minMain, bounds.maxMain);
    currentRatio = clamped / bounds.usableWidth;
    layout.style.setProperty("--transcription-main-size", `${clamped}px`);
    layout.style.setProperty("--transcription-split-gap", `${bounds.gapPx}px`);
  }

  function inferInitialRatio() {
    const bounds = getDesktopBounds(layout, options);
    if (bounds.usableWidth <= 0) return initialMainRatio;
    const measured = main.getBoundingClientRect().width;
    if (measured > 0) {
      const clamped = clamp(measured, bounds.minMain, bounds.maxMain);
      return clamped / bounds.usableWidth;
    }
    return initialMainRatio;
  }

  function sync() {
    const active = isDesktopActive();
    layout.classList.toggle("is-split-active", active);
    handle.hidden = !active;
    if (!active) return;
    if (!(currentRatio > 0)) {
      currentRatio = inferInitialRatio();
    }
    const bounds = getDesktopBounds(layout, options);
    setMainWidth(bounds.usableWidth * currentRatio);
  }

  function stopDragging() {
    if (!dragging) return;
    dragging = false;
    layout.classList.remove("is-split-dragging");
    window.removeEventListener("pointermove", onPointerMove);
    window.removeEventListener("pointerup", stopDragging);
    window.removeEventListener("pointercancel", stopDragging);
  }

  function onPointerMove(event) {
    if (!dragging || !isDesktopActive()) return;
    const bounds = getDesktopBounds(layout, options);
    const rawMainWidth = event.clientX - bounds.rect.left - (bounds.gapPx / 2);
    setMainWidth(rawMainWidth);
  }

  handle.addEventListener("pointerdown", (event) => {
    if (event.button !== 0 || !isDesktopActive()) return;
    event.preventDefault();
    dragging = true;
    layout.classList.add("is-split-dragging");
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", stopDragging);
    window.addEventListener("pointercancel", stopDragging);
  });

  handle.addEventListener("keydown", (event) => {
    if (!isDesktopActive()) return;
    const bounds = getDesktopBounds(layout, options);
    const currentWidth = (currentRatio > 0 ? currentRatio : inferInitialRatio()) * bounds.usableWidth;
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      setMainWidth(currentWidth - 32);
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      setMainWidth(currentWidth + 32);
    } else if (event.key === "Home") {
      event.preventDefault();
      setMainWidth(bounds.minMain);
    } else if (event.key === "End") {
      event.preventDefault();
      setMainWidth(bounds.maxMain);
    }
  });

  const onResize = () => sync();
  window.addEventListener("resize", onResize);
  if (mobileQuery) {
    if (typeof mobileQuery.addEventListener === "function") {
      mobileQuery.addEventListener("change", sync);
    } else if (typeof mobileQuery.addListener === "function") {
      mobileQuery.addListener(sync);
    }
  }

  requestAnimationFrame(sync);

  return {
    sync,
    destroy() {
      stopDragging();
      window.removeEventListener("resize", onResize);
      if (mobileQuery) {
        if (typeof mobileQuery.removeEventListener === "function") {
          mobileQuery.removeEventListener("change", sync);
        } else if (typeof mobileQuery.removeListener === "function") {
          mobileQuery.removeListener(sync);
        }
      }
      handle.remove();
      layout.classList.remove("transcription-split-layout", "is-split-active", "is-split-dragging");
      layout.style.removeProperty("--transcription-main-size");
      layout.style.removeProperty("--transcription-split-gap");
    }
  };
}
