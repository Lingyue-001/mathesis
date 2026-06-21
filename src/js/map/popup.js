import { formatCoordinate, formatMeasurement } from "../formatters/measurement.js";
import {
  formatHistoricalName as formatHistoricalDisplayName,
  formatModernLocation
} from "../formatters/text.js";

export function createPopupHtml(record, placeName) {
  const { site, observation } = record;
  const historicalName = placeName?.nameTraditional || placeName?.name || "Unknown historical name";
  const historicalLabel = formatHistoricalName(placeName, historicalName);
  const modernLabel = formatModernName(site);

  return `
    <div>
      <strong class="entry-card-title map-detail-drag-handle">${escapeHtml(historicalLabel)}</strong>
      ${createEntryRow("Modern location", modernLabel)}
      ${createEntryRow("Modern latitude", formatCoordinate(site.lat, "lat"))}
      ${createEntryRow("Modern longitude", formatCoordinate(site.lng, "lng"))}
      ${createEntryRow("Polar altitude", formatMeasurement(observation.poleHeight))}
      ${createEntryRow("Summer solstice shadow", formatMeasurement(observation.summerShadow))}
      ${createEntryRow("Equinox shadow", formatMeasurement(observation.equinoxShadow))}
      ${createEntryRow("Winter solstice shadow", formatMeasurement(observation.winterShadow))}
      ${createEntryRow("Status", observation.status || "")}
      ${createEntryRow("Note", observation.note || site.note || "")}
      ${createEntryRow("Primary source", formatPrimarySource(observation.primarySource))}
    </div>
  `;
}

function createEntryRow(label, value) {
  return `<div class="entry-card-row"><strong>${escapeHtml(label)}:</strong> ${escapeHtml(value)}</div>`;
}

function formatHistoricalName(placeName, fallbackName) {
  const transliteration = placeName?.transliteration;
  const name = placeName?.nameTraditional || placeName?.name || fallbackName;
  return formatHistoricalDisplayName(name, transliteration);
}

function formatModernName(site) {
  return formatModernLocation(site.modernNameEn) || "Unknown modern name";
}

function formatPrimarySource(source) {
  const text = String(source || "");
  const parts = text.split(" / ");
  return parts.length > 1 ? parts[parts.length - 1] : text;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
