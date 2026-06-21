const unitLabels = {
  chi: "尺",
  du: "度",
  decimalDegree: "°",
  li: "里",
  bu: "步",
  yojana: "由旬",
  angula: "指"
};

export function formatMeasurement(measurement, options = {}) {
  if (measurement === null || measurement === undefined || measurement === "") return "Unknown";

  if (typeof measurement !== "object") {
    return String(measurement);
  }

  const main = formatMeasurementValue(measurement, options);
  const variants = Array.isArray(measurement.variants)
    ? measurement.variants.map((variant) => {
      const label = variant.label ? `${variant.label} ` : "";
      return `${label}${formatMeasurementValue(variant, options)}`;
    })
    : [];

  return [main, ...variants].filter(Boolean).join("; ");
}

export function formatCoordinate(value, axis) {
  if (!Number.isFinite(value)) return "Unknown";

  const direction = axis === "lat"
    ? (value >= 0 ? "N" : "S")
    : (value >= 0 ? "E" : "W");

  return `${formatNumber(Math.abs(value))}${unitLabels.decimalDegree} ${direction}`;
}

function formatMeasurementValue(measurement, options = {}) {
  const unit = options.unitLabel || unitLabels[measurement.unit] || measurement.unit || "";
  const value = formatNumber(measurement.value);
  return unit ? `${value} ${unit}` : value;
}

function formatNumber(value) {
  if (!Number.isFinite(value)) return String(value ?? "Unknown");
  return Number.isInteger(value) ? String(value) : String(value);
}
