const openEndedYear = 9999;

export async function loadMapData(baseUrl) {
  const [sites, placeNames, calendars, observations, sources] = await Promise.all([
    fetchJson(baseUrl, "map-data/sites.json"),
    fetchJson(baseUrl, "map-data/placeNames.json"),
    fetchJson(baseUrl, "map-data/calendars.json"),
    fetchJson(baseUrl, "map-data/observations.json"),
    fetchJson(baseUrl, "map-data/sources.json")
  ]);

  return {
    sites: withoutSchemaNotes(sites),
    placeNames: withoutSchemaNotes(placeNames),
    calendars: withoutSchemaNotes(calendars),
    observations: withoutSchemaNotes(observations),
    sources: withoutSchemaNotes(sources)
  };
}

export function buildObservationRecords(data) {
  const siteById = new Map(data.sites.map((site) => [site.siteId, site]));
  const calendarById = new Map(data.calendars.map((calendar) => [calendar.calendarId, calendar]));
  const sourceById = new Map(data.sources.map((source) => [source.sourceId, source]));

  return data.observations
    .map((observation) => {
      const compiledFromIds = Array.isArray(observation.compiledFromIds)
        ? observation.compiledFromIds
        : observation.compiledFromId ? [observation.compiledFromId] : [];
      return {
        observation,
        site: siteById.get(observation.siteId),
        calendar: calendarById.get(observation.calendarId),
        compiledFrom: compiledFromIds.map(id => sourceById.get(id)).filter(Boolean)
      };
    })
    .filter((record) => record.site && record.calendar);
}

export function findPlaceName(placeNames, siteId, year, period) {
  const namesForSite = placeNames.filter((item) => item.siteId === siteId);

  if (Number.isFinite(year)) {
    const byYear = namesForSite.find((item) => isYearInRange(year, item.startYear, item.endYear));
    if (byYear) return byYear;
  }

  if (period) {
    const byPeriod = namesForSite.find((item) => item.period === period);
    if (byPeriod) return byPeriod;
  }

  return namesForSite.find((item) => item.nameType === "modern") || namesForSite[0] || null;
}

export function isYearInRange(year, startYear, endYear) {
  const start = Number.isFinite(startYear) ? startYear : -openEndedYear;
  const end = Number.isFinite(endYear) ? endYear : openEndedYear;
  return year >= start && year <= end;
}

async function fetchJson(baseUrl, path) {
  const url = withBase(baseUrl, path);
  const response = await fetch(url, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    throw new Error(`Failed to load ${url}: ${response.status}`);
  }
  return response.json();
}

function withBase(baseUrl, path) {
  return `${baseUrl.replace(/\/?$/, "/")}${path.replace(/^\/+/, "")}`;
}

function withoutSchemaNotes(items) {
  return Array.isArray(items)
    ? items.filter((item) => !item?._schemaNote)
    : [];
}
