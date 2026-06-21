export function filterObservationRecords(records, filters) {
  return records.filter((record) => {
    const observation = record.observation;
    const calendarMatches = Array.isArray(filters.calendarIds)
      ? filters.calendarIds.includes(observation.calendarId)
      : true;
    const periodMatches = filters.period === "all" || observation.period === filters.period;
    const siteType = getObservationSiteType(record);
    const siteTypeMatches = Array.isArray(filters.siteTypes)
      ? filters.siteTypes.includes(siteType)
      : true;
    const yearMatches = !Number.isFinite(filters.year)
      || observation.observationYear === filters.year;

    return calendarMatches && periodMatches && siteTypeMatches && yearMatches;
  });
}

export function getObservationSiteType(record) {
  const observation = record?.observation || record || {};
  const sourceTypes = Array.isArray(observation.sourceTypes) ? observation.sourceTypes : [];

  if (observation.status === "hypothetical" || sourceTypes.includes("hypothetical-inferred")) {
    return "hypothetical";
  }

  if (observation.status === "reference") {
    return "reference";
  }

  return "measured";
}
