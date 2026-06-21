export function formatBilingualLabel(primary, secondary) {
  const left = String(primary || "").trim();
  const right = String(secondary || "").trim();
  return [left, right].filter(Boolean).join(" ");
}

export function formatHistoricalName(originalScript, romanization) {
  const original = String(originalScript || "").trim();
  const roman = String(romanization || "").trim();
  return original && roman ? `${original} / ${roman}` : (original || roman);
}

export function formatCalendarName(romanization, originalScript) {
  return formatBilingualLabel(romanization, originalScript);
}

export function formatModernLocation(englishName) {
  return String(englishName || "").trim();
}

export function formatYearRangeCE(startYear, endYear) {
  if (!Number.isFinite(startYear) && !Number.isFinite(endYear)) return "";
  if (!Number.isFinite(endYear) || startYear === endYear) return formatYearCE(startYear);
  if ((startYear < 0 && endYear >= 0) || (startYear >= 0 && endYear < 0)) {
    return `${formatYearCE(startYear)}-${formatYearCE(endYear)}`;
  }
  return `${formatYearNumber(startYear)}-${formatYearNumber(endYear)} ${eraLabel(startYear, endYear)}`;
}

function formatYearCE(year) {
  if (!Number.isFinite(year)) return "";
  return `${formatYearNumber(year)} ${year < 0 ? "BCE" : "CE"}`;
}

function formatYearNumber(year) {
  return String(Math.abs(year));
}

function eraLabel(startYear, endYear) {
  return startYear < 0 || endYear < 0 ? "BCE" : "CE";
}
