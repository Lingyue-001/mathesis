import { mapConfig } from "./config.js";
import {
  formatHistoricalName,
  formatModernLocation
} from "../formatters/text.js";
import { getObservationSiteType } from "./filters.js";

export function createMap(containerId) {
  const map = L.map(containerId, {
    scrollWheelZoom: mapConfig.interaction.scrollWheelZoom,
    touchZoom: mapConfig.interaction.touchZoom,
    doubleClickZoom: mapConfig.interaction.doubleClickZoom,
    zoomSnap: mapConfig.interaction.trackpadPinchStep || 0.25
  }).setView(mapConfig.initialView.center, mapConfig.initialView.zoom);

  enableTrackpadPinchZoom(map);

  L.tileLayer(mapConfig.baseLayer.tileUrl, {
    attribution: mapConfig.baseLayer.attribution,
    maxZoom: mapConfig.baseLayer.maxZoom
  }).addTo(map);

  const markerLayer = L.layerGroup().addTo(map);
  const lineLayer = L.layerGroup().addTo(map);

  return { map, markerLayer, lineLayer, markersByObservationId: new Map() };
}

function enableTrackpadPinchZoom(map) {
  if (!mapConfig.interaction.trackpadPinchZoom) return;

  const container = map.getContainer();
  const zoomStep = mapConfig.interaction.trackpadPinchStep || 0.25;
  const threshold = mapConfig.interaction.trackpadPinchThreshold || 12;
  let accumulatedDelta = 0;

  const onWheel = (event) => {
    if (!event.ctrlKey) return;

    event.preventDefault();
    event.stopPropagation();

    accumulatedDelta += normalizeWheelDelta(event);
    if (Math.abs(accumulatedDelta) < threshold) return;

    const direction = accumulatedDelta < 0 ? 1 : -1;
    accumulatedDelta = 0;
    const nextZoom = clamp(
      map.getZoom() + direction * zoomStep,
      map.getMinZoom(),
      map.getMaxZoom()
    );

    map.setZoomAround(map.mouseEventToContainerPoint(event), nextZoom, {
      animate: false
    });
  };

  container.addEventListener("wheel", onWheel, { passive: false, capture: true });
  map.on("unload", () => {
    container.removeEventListener("wheel", onWheel, { capture: true });
  });
}

function normalizeWheelDelta(event) {
  if (event.deltaMode === WheelEvent.DOM_DELTA_LINE) return event.deltaY * 16;
  if (event.deltaMode === WheelEvent.DOM_DELTA_PAGE) return event.deltaY * window.innerHeight;
  return event.deltaY;
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

export function renderObservationMarkers(view, records, placeNameByObservationId, options = {}) {
  view.lineLayer.clearLayers();

  renderObservationLines(view, records);
  removeFilteredMarkers(view, records);

  records.forEach((record) => {
    const { site, observation } = record;
    if (view.markersByObservationId.has(observation.observationId)) return;

    const placeName = placeNameByObservationId.get(observation.observationId);
    const label = formatMarkerLabel(placeName, site);

    const marker = createObservationMarker(record, label).addTo(view.markerLayer);
    view.markersByObservationId.set(observation.observationId, marker);
    animateMarker(marker, "map-marker-enter");

    marker.on("click", (event) => {
      event.originalEvent?.stopPropagation?.();
      options.onRecordSelect?.(record, placeName);
    });

  });

  const bounds = L.latLngBounds(records.map((record) => [record.site.lat, record.site.lng]));
  if (bounds.isValid()) {
    view.map.fitBounds(bounds.pad(0.35), { maxZoom: 7 });
  }
}

function removeFilteredMarkers(view, records) {
  const nextIds = new Set(records.map((record) => record.observation.observationId));

  view.markersByObservationId.forEach((marker, observationId) => {
    if (nextIds.has(observationId)) return;

    view.markersByObservationId.delete(observationId);
    animateMarker(marker, "map-marker-exit");
    window.setTimeout(() => {
      view.markerLayer.removeLayer(marker);
    }, 260);
  });
}

function formatMarkerLabel(placeName, site) {
  const historicalName = placeName?.nameTraditional || placeName?.name;
  const historicalLabel = formatHistoricalName(historicalName, placeName?.transliteration);
  const modernName = formatModernLocation(site.modernNameEn);
  return historicalLabel || modernName || "Observation site";
}

function renderObservationLines(view, records) {
  if (!mapConfig.observationLines.enabled) return;

  const recordsByCalendar = new Map();
  records.forEach((record) => {
    const bucket = recordsByCalendar.get(record.observation.calendarId) || [];
    bucket.push(record);
    recordsByCalendar.set(record.observation.calendarId, bucket);
  });

  recordsByCalendar.forEach((calendarRecords) => {
    if (calendarRecords.length < 2) return;

    const sorted = [...calendarRecords].sort((a, b) => {
      const aOrder = Number.isFinite(a.observation.sequence) ? a.observation.sequence : a.observation.observationYear;
      const bOrder = Number.isFinite(b.observation.sequence) ? b.observation.sequence : b.observation.observationYear;
      return aOrder - bOrder;
    });

    L.polyline(
      sorted.map((record) => [record.site.lat, record.site.lng]),
      {
        color: sorted[0].calendar.color || "#6d817b",
        opacity: mapConfig.observationLines.opacity,
        weight: mapConfig.observationLines.weight,
        dashArray: "4 6"
      }
    ).addTo(view.lineLayer);
  });
}

function createObservationMarker(record, label) {
  const { site } = record;
  if (getObservationSiteType(record) === "reference") {
    return L.marker([site.lat, site.lng], {
      title: label,
      icon: L.divIcon({
        className: "map-reference-star",
        html: "<span class=\"map-reference-star-shape\" aria-hidden=\"true\"></span>",
        iconSize: [26, 26],
        iconAnchor: [13, 13]
      })
    });
  }

  return L.circleMarker([site.lat, site.lng], {
    title: label,
    ...getCircleMarkerStyle(record)
  });
}

function animateMarker(marker, className) {
  requestAnimationFrame(() => {
    const element = marker.getElement?.();
    if (!element) return;
    element.classList.remove("map-marker-enter", "map-marker-exit");
    void element.getBoundingClientRect();
    element.classList.add(className);
    if (className === "map-marker-enter") {
      window.setTimeout(() => {
        element.classList.remove("map-marker-enter");
      }, 320);
    }
  });
}

function getCircleMarkerStyle(record) {
  const isUncertain = getObservationSiteType(record) === "hypothetical";
  const color = isUncertain
    ? (record.calendar.uncertainColor || "#cfa08e")
    : (record.calendar.color || "#955539");

  return {
    radius: isUncertain ? 8 : 9,
    stroke: false,
    weight: 0,
    fillColor: color,
    fillOpacity: isUncertain ? 0.72 : 0.78,
    className: "map-observation-circle"
  };
}
