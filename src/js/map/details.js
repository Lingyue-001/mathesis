import { createPopupHtml } from "./popup.js";
import { makePanelDraggable } from "../nodeEntryPopup.js";

const transitionFallbackMs = 360;
const slots = ["left", "right"];

export function createDetailDock(containerId) {
  const container = document.getElementById(containerId);
  const state = {
    left: createSlotState("left"),
    right: createSlotState("right")
  };

  function open(record, placeName) {
    if (!container) return;

    const observationId = record.observation.observationId;
    const existingSlotName = slots.find((name) => state[name].observationId === observationId);
    if (existingSlotName) {
      openPanel(state[existingSlotName]);
      return;
    }

    const slotName = getTargetSlotName();
    const slot = state[slotName];
    const nextHtml = createDetailContentHtml(record, placeName);
    ensurePanel(slot);
    if (!slot.panel) return;

    container.hidden = false;
    slot.observationId = observationId;

    if (!slot.panel.classList.contains("is-open") || !slot.hasContent) {
      renderInitialContent(slot, nextHtml);
      openPanel(slot);
      return;
    }

    swapContent(slot, nextHtml);
  }

  function close(observationId) {
    const slotName = slots.find((name) => state[name].observationId === observationId);
    if (!slotName) return;
    closeSlot(state[slotName]);
  }

  function getTargetSlotName() {
    if (!state.left.observationId) return "left";
    if (!state.right.observationId) return "right";
    return getRightmostOpenSlotName() || "right";
  }

  function getRightmostOpenSlotName() {
    const openSlots = slots
      .map((name) => state[name])
      .filter((slot) => slot.observationId && slot.panel instanceof HTMLElement);

    if (!openSlots.length) return null;

    return openSlots
      .map((slot) => ({
        name: slot.name,
        centerX: getPanelCenterX(slot.panel)
      }))
      .sort((a, b) => b.centerX - a.centerX)[0].name;
  }

  function ensurePanel(slot) {
    if (slot.panel) return;

    const sideClass = slot.name === "left" ? "side-left" : "side-right";
    const panel = document.createElement("aside");
    panel.className = `detail-panel map-detail-panel ${sideClass}`;
    panel.dataset.mapDetailPanel = slot.name;
    panel.innerHTML = `
      <div class="detail-panel-head">
        <div class="detail-panel-title">Observation Details</div>
        <button class="detail-panel-close" type="button" aria-label="Close detail">&times;</button>
      </div>
      <div class="detail-panel-body"></div>
    `;

    container.appendChild(panel);
    panel.querySelector(".detail-panel-close")?.addEventListener("click", () => closeSlot(slot));
    makePanelDraggable(panel);
    bindOutsideMapDismiss(panel);
    slot.panel = panel;
  }

  function renderInitialContent(slot, nextHtml) {
    const body = getBody(slot);
    if (!body) return;

    body.innerHTML = nextHtml;
    slot.hasContent = true;

    const content = body.querySelector(".map-detail-content");
    content?.classList.add("is-entering");
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        content?.classList.remove("is-entering");
      });
    });
  }

  function swapContent(slot, nextHtml) {
    const body = getBody(slot);
    if (!body) return;

    const currentContent = body.querySelector(".map-detail-content");
    if (!(currentContent instanceof HTMLElement)) {
      renderInitialContent(slot, nextHtml);
      return;
    }

    currentContent.classList.add("is-exiting");
    afterTransition(currentContent, () => {
      if (!slot.observationId) return;

      body.innerHTML = nextHtml;
      slot.hasContent = true;

      const nextContent = body.querySelector(".map-detail-content");
      nextContent?.classList.add("is-entering");
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          nextContent?.classList.remove("is-entering");
        });
      });
    });
  }

  function openPanel(slot) {
    if (!(slot.panel instanceof HTMLElement)) return;

    resetPanelPosition(slot);
    setPanelMotionDirection(slot.panel, getPanelDirection(slot.panel, slot.name));
    slot.panel.classList.remove("is-open");
    void slot.panel.getBoundingClientRect();
    slot.panel.classList.add("is-open");
  }

  function closeSlot(slot) {
    if (!(slot.panel instanceof HTMLElement)) return;

    setPanelMotionDirection(slot.panel, slot.pendingCloseDirection || getPanelDirection(slot.panel, slot.name));
    slot.pendingCloseDirection = null;
    slot.panel.classList.remove("is-open");
    slot.observationId = null;

    afterTransition(slot.panel, () => {
      if (slot.observationId) return;

      const body = getBody(slot);
      if (body) body.innerHTML = "";
      slot.hasContent = false;
      resetPanelPosition(slot);
      updateContainerHidden();
    });
  }

  function updateContainerHidden() {
    if (!container) return;
    container.hidden = !slots.some((name) => state[name].observationId);
  }

  function bindOutsideMapDismiss(panel) {
    if (panel.dataset.mapOutsideDismissBound === "1") return;
    panel.dataset.mapOutsideDismissBound = "1";

    document.addEventListener("click", (event) => {
      const target = event.target;
      if (!(target instanceof Element)) return;
      if (!slots.some((name) => state[name].panel?.classList.contains("is-open"))) return;
      if (target.closest(".map-detail-panel")) return;
      if (target.closest(".map-stage")) return;

      setCloseDirectionsByRelativePosition();
      slots.forEach((name) => closeSlot(state[name]));
    });
  }

  function setCloseDirectionsByRelativePosition() {
    const openSlots = slots
      .map((name) => state[name])
      .filter((slot) => slot.panel instanceof HTMLElement && slot.panel.classList.contains("is-open"))
      .map((slot) => ({
        slot,
        centerX: getPanelCenterX(slot.panel)
      }));

    if (openSlots.length === 1) {
      const [item] = openSlots;
      item.slot.pendingCloseDirection = item.centerX < window.innerWidth / 2 ? "left" : "right";
      return;
    }

    openSlots
      .sort((a, b) => a.centerX - b.centerX)
      .forEach((item, index) => {
        item.slot.pendingCloseDirection = index === 0 ? "left" : "right";
      });
  }

  function getBody(slot) {
    const body = slot.panel?.querySelector(".detail-panel-body");
    return body instanceof HTMLElement ? body : null;
  }

  if (container) container.hidden = true;

  return { open, close };
}

function createSlotState(name) {
  return {
    name,
    panel: null,
    observationId: null,
    hasContent: false,
    pendingCloseDirection: null
  };
}

function resetPanelPosition(slot) {
  if (!(slot.panel instanceof HTMLElement)) return;
  slot.panel.style.top = "";
  slot.panel.style.left = "";
  slot.panel.style.right = "";
}

function getPanelDirection(panel, fallbackSide = "right") {
  if (!(panel instanceof HTMLElement)) return fallbackSide === "left" ? "left" : "right";
  return getPanelCenterX(panel) < window.innerWidth / 2 ? "left" : "right";
}

function getPanelCenterX(panel) {
  const rect = panel.getBoundingClientRect();
  return rect.left + rect.width / 2;
}

function setPanelMotionDirection(panel, direction) {
  if (!(panel instanceof HTMLElement)) return;
  panel.style.setProperty("--detail-panel-enter-x", direction === "left" ? "-110%" : "110%");
}

function createDetailContentHtml(record, placeName) {
  return `
    <div class="map-detail-content" data-observation-id="${record.observation.observationId}">
      <div class="entry-card">
        ${createPopupHtml(record, placeName)}
      </div>
    </div>
  `;
}

function afterTransition(element, callback) {
  if (!(element instanceof HTMLElement)) {
    callback();
    return;
  }

  let done = false;
  const finish = () => {
    if (done) return;
    done = true;
    element.removeEventListener("transitionend", finish);
    callback();
  };

  element.addEventListener("transitionend", finish, { once: true });
  window.setTimeout(finish, transitionFallbackMs);
}
