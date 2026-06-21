export const mapConfig = {
  initialView: {
    center: [34.45, 113.05],
    zoom: 6
  },
  interaction: {
    scrollWheelZoom: false,
    touchZoom: true,
    doubleClickZoom: true,
    trackpadPinchZoom: true,
    trackpadPinchStep: 0.25,
    trackpadPinchThreshold: 12
  },
  baseLayer: {
    tileUrl: "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    attribution: "&copy; OpenStreetMap contributors, &copy; CARTO",
    maxZoom: 18
  },
  observationLines: {
    enabled: true,
    opacity: 0.32,
    weight: 1.6
  }
};
