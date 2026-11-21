export default async function handler(req, res) {
  const lat = Number(req.query.lat),
    lon = Number(req.query.lon);
  if (!Number.isFinite(lat) || !Number.isFinite(lon) || lat < 49 || lat > 55 || lon < 14 || lon > 25)
    return res.status(400).json({ error: "Invalid coordinates" });
  try {
    const end = new Date(),
      start = new Date(end.getTime() - 60 * 86400000);
    const response = await fetch("https://stac.dataspace.copernicus.eu/v1/search", {
      method: "POST",
      headers: { "content-type": "application/json" },
      signal: AbortSignal.timeout(12000),
      body: JSON.stringify({
        collections: ["sentinel-2-l2a"],
        intersects: { type: "Point", coordinates: [lon, lat] },
        datetime: `${start.toISOString()}/${end.toISOString()}`,
        query: { "eo:cloud_cover": { lt: 30 } },
        sortby: [{ field: "properties.datetime", direction: "desc" }],
        limit: 1,
      }),
    });
    if (!response.ok || !response.headers.get("content-type")?.includes("json")) throw Error();
    const data = await response.json();
    if (!Array.isArray(data.features)) throw Error();
    const f = data.features[0];
    const scene =
      f &&
      typeof f.id === "string" &&
      typeof f.properties?.datetime === "string" &&
      Number.isFinite(f.properties?.["eo:cloud_cover"])
        ? {
            id: f.id,
            date: f.properties.datetime,
            cloudPercent: f.properties["eo:cloud_cover"],
            url: `https://browser.dataspace.copernicus.eu/?zoom=12&lat=${lat}&lng=${lon}`,
          }
        : null;
    res.setHeader("Cache-Control", "public, s-maxage=3600, stale-while-revalidate=86400");
    return res.status(200).json({ scene });
  } catch {
    return res.status(502).json({ error: "Satellite catalogue unavailable" });
  }
}
