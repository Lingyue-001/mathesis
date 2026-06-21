const TRANSITION_FALLBACK_MS = 360;

export function openSplitDetail(layout) {
  if (!(layout instanceof HTMLElement)) return;
  const side = layout.querySelector(".split-detail-side");
  side?.classList.add("is-entering");
  layout.classList.add("has-detail");

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      layout.classList.add("is-open");
      side?.classList.remove("is-entering");
    });
  });
}

export function swapSplitDetailSide(layout, nextHtml) {
  if (!(layout instanceof HTMLElement)) return;
  const currentSide = layout.querySelector(".split-detail-side");

  if (!layout.classList.contains("is-open") || !currentSide) {
    replaceSplitDetailSide(layout, nextHtml);
    openSplitDetail(layout);
    return;
  }

  currentSide.classList.add("is-exiting");
  afterTransition(currentSide, () => {
    replaceSplitDetailSide(layout, nextHtml, { enter: true });
  });
}

export function closeSplitDetail(layout) {
  if (!(layout instanceof HTMLElement)) return;
  const side = layout.querySelector(".split-detail-side");
  side?.classList.add("is-exiting");
  layout.classList.remove("is-open");

  afterTransition(side || layout, () => {
    side?.remove();
    layout.classList.remove("has-detail");
  });
}

function replaceSplitDetailSide(layout, nextHtml, options = {}) {
  const currentSide = layout.querySelector(".split-detail-side");
  currentSide?.remove();

  const nextSide = createElementFromHtml(nextHtml);
  if (!(nextSide instanceof HTMLElement)) return;
  if (options.enter) nextSide.classList.add("is-entering");
  layout.appendChild(nextSide);

  if (options.enter) {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        nextSide.classList.remove("is-entering");
      });
    });
  }
}

function createElementFromHtml(html) {
  const template = document.createElement("template");
  template.innerHTML = String(html || "").trim();
  return template.content.firstElementChild;
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
  window.setTimeout(finish, TRANSITION_FALLBACK_MS);
}
