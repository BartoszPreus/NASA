const CRS = "urn:ogc:def:crs:OGC:1.3:CRS84";
const ENDPOINT = "https://geoportal-w2.arimr.gov.pl/geoserver/gsa_public/uprawy_2026/wfs";
const CAP = 500;

export default async function handler(req, res) {
  const b = String(req.query.bbox || "")
    .split(",")
    .map(Number);
  if (
    b.length !== 4 ||
    b.some((x) => !Number.isFinite(x)) ||
    b[0] < 14 ||
    b[2] > 25 ||
    b[1] < 49 ||
    b[3] > 55 ||
    b[0] >= b[2] ||
    b[1] >= b[3] ||
    b[2] - b[0] > 0.1 ||
    b[3] - b[1] > 0.1
  )
    return res.status(400).json({ error: "Invalid or oversized Polish bounding box" });
  const u = new URL(ENDPOINT);
  Object.entries({
    service: "WFS",
    version: "2.0.0",
    request: "GetFeature",
    typeNames: "gsa_public:uprawy_na_gruntach_ornych_2026",
    count: String(CAP),
    outputFormat: "application/json",
    srsName: CRS,
    bbox: `${b.join(",")},${CRS}`,
  }).forEach(([k, v]) => u.searchParams.set(k, v));
  try {
    const response = await fetch(u, {
      signal: AbortSignal.timeout(12000),
      headers: { Accept: "application/json" },
    });
    if (!response.ok || !response.headers.get("content-type")?.includes("json"))
      throw Error("Crop service unavailable");
    const data = await response.json();
    if (data.type !== "FeatureCollection" || !Array.isArray(data.features)) throw Error("Invalid crop response");
    const valid = (coords) =>
      Array.isArray(coords) &&
      (typeof coords[0] === "number"
        ? coords.length >= 2 &&
          Number.isFinite(coords[0]) &&
          Number.isFinite(coords[1]) &&
          coords[0] >= 13 &&
          coords[0] <= 26 &&
          coords[1] >= 48 &&
          coords[1] <= 56
        : coords.length > 0 && coords.every(valid));
    const features = data.features.map((f) => {
      if (!["Polygon", "MultiPolygon"].includes(f.geometry?.type) || !valid(f.geometry.coordinates))
        throw Error("Crop service returned invalid coordinates");
      return {
        type: "Feature",
        geometry: f.geometry,
        properties: { crop: String(f.properties?.roslina || ""), group: String(f.properties?.grupa_roslin || "") },
      };
    });
    res.setHeader("Cache-Control", "public, s-maxage=3600, stale-while-revalidate=86400");
    return res
      .status(200)
      .json({
        type: "FeatureCollection",
        features,
        truncated:
          features.length >= CAP || (Number.isFinite(data.numberMatched) && data.numberMatched > features.length),
        campaign: 2026,
        retrievedAt: new Date().toISOString(),
      });
  } catch {
    return res.status(502).json({ error: "Crop service unavailable or returned invalid data" });
  }
}
