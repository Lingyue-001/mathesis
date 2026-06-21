import { buildObservationRecords, findPlaceName, loadMapData } from "./data.js";
import { createDetailDock } from "./details.js";
import { filterObservationRecords, getObservationSiteType } from "./filters.js";
import { createMap, renderObservationMarkers } from "./leaflet-view.js";
import { createPopupHtml } from "./popup.js";
import {
  closeSplitDetail,
  openSplitDetail,
  swapSplitDetailSide
} from "../ui/splitDetail.js";
import {
  formatCalendarName,
  formatHistoricalName as formatHistoricalDisplayName,
  formatModernLocation,
  formatYearRangeCE
} from "../formatters/text.js";

const baseUrl = document.documentElement.dataset.baseurl || "/";
const state = {
  calendarIds: ["dayanli"],
  siteTypes: ["measured", "reference", "hypothetical"],
  period: "Tang",
  year: null,
  selectedSummaryObservationId: null
};
let summaryContext = null;

document.addEventListener("DOMContentLoaded", async () => {
  const status = document.getElementById("map-status");

  try {
    const data = await loadMapData(baseUrl);
    const records = buildObservationRecords(data);
    const view = createMap("map");
    const detailDock = createDetailDock("map-detail-dock");

    populateCalendarFilters(data.calendars);
    populateSiteTypeFilters(records);
    populatePeriodFilter(data);
    bindControls(() => render(data, records, view, detailDock));
    render(data, records, view, detailDock);
  } catch (error) {
    console.error(error);
    if (status) status.textContent = "Map data failed to load.";
  }
});

function render(data, records, view, detailDock) {
  const filteredRecords = filterObservationRecords(records, state);
  const placeNameByObservationId = new Map();

  filteredRecords.forEach((record) => {
    const placeName = findPlaceName(data.placeNames, record.site.siteId, state.year, state.period);
    placeNameByObservationId.set(record.observation.observationId, placeName);
  });

  renderObservationMarkers(view, filteredRecords, placeNameByObservationId, {
    onRecordSelect: (record, placeName) => detailDock.open(record, placeName)
  });
  updateStatus(filteredRecords, placeNameByObservationId);
}

function populateCalendarFilters(calendars) {
  const container = document.getElementById("calendar-filter-list");
  if (!container) return;

  container.innerHTML = calendars.map((calendar) => {
    const checked = state.calendarIds.includes(calendar.calendarId) ? "checked" : "";
    const color = calendar.color || "#955539";
    const uncertainColor = calendar.uncertainColor || "#cfa08e";
    return `
      <label class="map-check">
        <input type="checkbox" value="${calendar.calendarId}" ${checked} />
        <span class="map-swatch" style="--swatch-certain: ${color}; --swatch-uncertain: ${uncertainColor};"></span>
        <span>${escapeHtml(formatCalendarLabel(calendar))}</span>
      </label>
    `;
  }).join("");
}

function populateSiteTypeFilters(records) {
  const container = document.getElementById("site-type-filter-list");
  if (!container) return;

  const availableTypes = Array.from(new Set(records.map(getObservationSiteType)));
  const orderedTypes = ["measured", "reference", "hypothetical"]
    .filter((type) => availableTypes.includes(type));

  container.innerHTML = orderedTypes.map((type) => {
    const checked = state.siteTypes.includes(type) ? "checked" : "";
    return `
      <label class="map-check">
        <input type="checkbox" value="${type}" ${checked} />
        <span class="map-swatch map-swatch-${type}" aria-hidden="true"></span>
        <span>${escapeHtml(formatSiteTypeLabel(type))}</span>
      </label>
    `;
  }).join("");
}

function populatePeriodFilter(data) {
  const select = document.getElementById("period-filter");
  if (!select) return;

  const periods = Array.from(new Set([
    ...data.calendars.map((calendar) => calendar.period),
    ...data.observations.map((observation) => observation.period)
  ].filter(Boolean)));

  select.innerHTML = periods
    .map((period) => `<option value="${period}">${formatPeriodLabel(period)}</option>`)
    .join("");
  select.value = state.period;
}

function bindControls(onChange) {
  const calendarFilterList = document.getElementById("calendar-filter-list");
  const siteTypeFilterList = document.getElementById("site-type-filter-list");
  const periodSelect = document.getElementById("period-filter");

  calendarFilterList?.addEventListener("change", () => {
    state.calendarIds = getCheckedValues(calendarFilterList);
    onChange();
  });

  siteTypeFilterList?.addEventListener("change", () => {
    state.siteTypes = getCheckedValues(siteTypeFilterList);
    onChange();
  });

  periodSelect?.addEventListener("change", () => {
    state.period = periodSelect.value;
    onChange();
  });
}

function getCheckedValues(container) {
  return Array.from(container.querySelectorAll("input[type='checkbox']"))
    .filter((item) => item.checked)
    .map((item) => item.value);
}

function updateStatus(records, placeNameByObservationId) {
  const resultList = document.getElementById("map-results");
  if (!resultList) return;
  summaryContext = { records, placeNameByObservationId };

  if (!records.some((record) => record.observation.observationId === state.selectedSummaryObservationId)) {
    state.selectedSummaryObservationId = null;
  }

  resultList.innerHTML = Array.from(groupRecords(records).entries()).map(([groupKey, groupRecords]) => {
    const first = groupRecords[0];
    const selectedRecord = groupRecords.find((record) =>
      record.observation.observationId === state.selectedSummaryObservationId
    );
    const heading = formatCalendarLabel(first.calendar);
    const countLabel = `${groupRecords.length} record${groupRecords.length === 1 ? "" : "s"}`;
    const calendarYears = formatCalendarYears(first.calendar);
    const periodLabel = formatCalendarPeriod(first.calendar, first.observation);
    const meta = [
      calendarYears,
      periodLabel
    ].filter(Boolean).join(" · ");
    const rows = groupRecords.map((record) => {
      const placeName = placeNameByObservationId.get(record.observation.observationId);
      const historicalName = formatHistoricalName(placeName);
      const modernName = formatModernName(record.site);
      const isSelected = record.observation.observationId === state.selectedSummaryObservationId;
      return `
        <tr class="${isSelected ? "is-selected" : ""}" data-observation-id="${escapeHtml(record.observation.observationId)}">
          <td>
            <button class="records-row-button" type="button" data-observation-id="${escapeHtml(record.observation.observationId)}">
              ${escapeHtml(historicalName)}
            </button>
          </td>
          <td>${escapeHtml(modernName)}</td>
        </tr>
      `;
    }).join("");
    const selectedPlaceName = selectedRecord
      ? placeNameByObservationId.get(selectedRecord.observation.observationId)
      : null;
    const detailHtml = selectedRecord ? renderSummaryDetail(selectedRecord, selectedPlaceName) : "";

    return `
      <li class="map-results-group ${selectedRecord ? "has-detail" : ""}">
        <strong>${escapeHtml(heading)}</strong>
        <span>${escapeHtml(meta)}</span>
        <div class="split-detail map-results-content ${selectedRecord ? "has-detail" : ""}" data-group-key="${escapeHtml(groupKey)}">
          <div class="split-detail-main map-results-main">
            <table class="records-table">
              <thead>
                <tr>
                  <th scope="col">Historical name</th>
                  <th scope="col">Modern location</th>
                </tr>
              </thead>
              <tbody>${rows}</tbody>
            </table>
            <div class="map-results-count">${escapeHtml(countLabel)}</div>
          </div>
          ${detailHtml}
        </div>
      </li>
    `;
  }).join("");

  bindSummaryInteractions(resultList);

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      resultList.querySelectorAll(".split-detail.has-detail").forEach((layout) => {
        layout.classList.add("is-open");
      });
    });
  });
}

function bindSummaryInteractions(resultList) {
  if (resultList.dataset.summaryInteractionsBound === "1") return;
  resultList.dataset.summaryInteractionsBound = "1";

  resultList.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof Element)) return;

    const closeButton = target.closest("[data-summary-detail-close]");
    if (closeButton) {
      closeSummarySelection(resultList);
      return;
    }

    const rowButton = target.closest(".records-row-button");
    if (!(rowButton instanceof HTMLElement)) return;
    const observationId = rowButton.dataset.observationId;
    if (observationId) selectSummaryRecord(resultList, observationId);
  });
}

function selectSummaryRecord(resultList, observationId) {
  if (!summaryContext) return;
  if (state.selectedSummaryObservationId === observationId) return;

  const previousObservationId = state.selectedSummaryObservationId;
  state.selectedSummaryObservationId = observationId;
  updateSelectedSummaryRows(resultList, observationId);

  const record = summaryContext.records.find((item) => item.observation.observationId === observationId);
  if (!record) return;

  const layout = findSummaryLayout(resultList, record);
  if (!layout) return;

  resultList.querySelectorAll(".split-detail.is-open").forEach((openLayout) => {
    if (openLayout !== layout) closeSplitDetail(openLayout);
  });

  const placeName = summaryContext.placeNameByObservationId.get(record.observation.observationId);
  const detailHtml = renderSummaryDetail(record, placeName);

  if (previousObservationId && layout.classList.contains("is-open")) {
    swapSplitDetailSide(layout, detailHtml);
  } else {
    const existingSide = layout.querySelector(".split-detail-side");
    existingSide?.remove();
    layout.insertAdjacentHTML("beforeend", detailHtml);
    openSplitDetail(layout);
  }
}

function closeSummarySelection(resultList) {
  if (!state.selectedSummaryObservationId) return;
  state.selectedSummaryObservationId = null;
  updateSelectedSummaryRows(resultList, null);

  resultList.querySelectorAll(".split-detail.is-open").forEach((layout) => {
    closeSplitDetail(layout);
  });
}

function updateSelectedSummaryRows(resultList, observationId) {
  resultList.querySelectorAll("[data-observation-id]").forEach((element) => {
    if (element instanceof HTMLTableRowElement) {
      element.classList.toggle("is-selected", element.dataset.observationId === observationId);
    }
  });
}

function findSummaryLayout(resultList, record) {
  const key = `${record.observation.calendarId}:${record.observation.period}`;
  return Array.from(resultList.querySelectorAll(".map-results-content"))
    .find((layout) => layout.dataset.groupKey === key) || null;
}

function renderSummaryDetail(record, placeName) {
  return `
    <aside class="split-detail-side map-results-detail" aria-live="polite">
      <div class="entry-card">
        <button class="detail-panel-close" type="button" data-summary-detail-close aria-label="Close selected record">&times;</button>
        ${createPopupHtml(record, placeName)}
      </div>
    </aside>
  `;
}

function groupRecords(records) {
  const groups = new Map();
  records.forEach((record) => {
    const key = `${record.observation.calendarId}:${record.observation.period}`;
    const bucket = groups.get(key) || [];
    bucket.push(record);
    groups.set(key, bucket);
  });
  return groups;
}

function formatCalendarLabel(calendar) {
  return formatCalendarName(calendar.nameEn, calendar.name);
}

function formatPeriodLabel(period) {
  const labels = {
    Tang: `Tang dynasty (${formatYearRangeCE(618, 907)})`,
    Han: `Han dynasty (${formatYearRangeCE(-206, 220)})`,
    Modern: "Modern"
  };
  return labels[period] || period;
}

function formatCalendarPeriod(calendar, observation) {
  return calendar.periodLabel || formatPeriodLabel(calendar.period || observation.period);
}

function formatCalendarYears(calendar) {
  const parts = [];
  if (Number.isFinite(calendar.promulgatedYear)) {
    parts.push(`Promulgated ${formatYearRange(calendar.promulgatedYear, calendar.promulgatedYear)}`);
  }
  const inUseRange = formatYearRange(calendar.inUseStartYear, calendar.inUseEndYear);
  if (inUseRange) parts.push(`in use ${inUseRange}`);
  if (!parts.length && Number.isFinite(calendar.observationYear)) {
    parts.push(`Observations ${formatYearRange(calendar.observationYear, calendar.observationYear)}`);
  }
  return parts.join("; ");
}

function formatSiteTypeLabel(type) {
  const labels = {
    measured: "Measured",
    reference: "Reference",
    hypothetical: "Hypothetical"
  };
  return labels[type] || type;
}

function formatYearRange(startYear, endYear) {
  return formatYearRangeCE(startYear, endYear);
}

function formatHistoricalName(placeName) {
  const name = placeName?.nameTraditional || placeName?.name || "Unknown";
  return formatHistoricalDisplayName(name, placeName?.transliteration);
}

function formatModernName(site) {
  return formatModernLocation(site.modernNameEn) || "Unknown";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
