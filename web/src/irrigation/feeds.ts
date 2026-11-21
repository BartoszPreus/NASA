/** Public map layers and modelled weather. User observations remain separate. */
export type Geometry = { type: "Polygon" | "MultiPolygon"; coordinates: number[][][] | number[][][][] };
export type MapFeature = {
  type: "Feature";
  geometry: Geometry;
  properties: { crop?: string; group?: string; kind?: string };
};
export type MapCollection = {
  type: "FeatureCollection";
  features: MapFeature[];
  truncated?: boolean;
  campaign?: number;
  retrievedAt?: string;
};
export type DailyWeather = { date: string; rainMm: number | null; et0Mm: number | null; windKmh: number | null };
export type Weather = { timezone: string; past: DailyWeather[]; forecast: DailyWeather[] };
export type SatelliteScene = { id: string; date: string; cloudPercent: number; url: string };
export const PILOT_BBOX = [16.7, 52.28, 16.74, 52.32] as const;
const json = async (url: string) => {
  const response = await fetch(url, { signal: AbortSignal.timeout(15000) });
  if (!response.ok) throw new Error("Data service unavailable");
  return response.json();
};
export async function loadPilotLayers(): Promise<{ crops: MapCollection; water: MapCollection }> {
  const [crops, water] = await Promise.all([json("/irrigation/crops.geojson"), json("/irrigation/water.geojson")]);
  return { crops, water };
}
export async function fetchCrops(bbox: readonly number[]): Promise<MapCollection> {
  return json(`/api/irrigation-crops?bbox=${encodeURIComponent(bbox.join(","))}`);
}
export async function fetchSatellite(lat: number, lon: number): Promise<SatelliteScene | null> {
  const result = await json(
    `/api/irrigation-satellite?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}`,
  );
  return result.scene;
}
export async function fetchWeather(lat: number, lon: number): Promise<Weather> {
  if (!Number.isFinite(lat) || !Number.isFinite(lon) || lat < 49 || lat > 55 || lon < 14 || lon > 25)
    throw new Error("Invalid coordinates");
  const url = new URL("https://api.open-meteo.com/v1/forecast");
  Object.entries({
    latitude: String(lat),
    longitude: String(lon),
    daily: "rain_sum,et0_fao_evapotranspiration,wind_speed_10m_max",
    past_days: "7",
    forecast_days: "4",
    timezone: "Europe/Warsaw",
  }).forEach(([k, v]) => url.searchParams.set(k, v));
  const result = await json(url.toString());
  const d = result.daily;
  if (
    !d ||
    !Array.isArray(d.time) ||
    !Array.isArray(d.rain_sum) ||
    !Array.isArray(d.et0_fao_evapotranspiration) ||
    !Array.isArray(d.wind_speed_10m_max)
  )
    throw new Error("Invalid weather response");
  const numeric = (n: unknown): number | null => (typeof n === "number" && Number.isFinite(n) ? n : null);
  const days: DailyWeather[] = d.time.map((date: string, i: number) => ({
    date,
    rainMm: numeric(d.rain_sum[i]),
    et0Mm: numeric(d.et0_fao_evapotranspiration[i]),
    windKmh: numeric(d.wind_speed_10m_max[i]),
  }));
  const today = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Europe/Warsaw",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
  return {
    timezone: result.timezone,
    past: days.filter((x) => x.date < today),
    forecast: days.filter((x) => x.date >= today),
  };
}

/** Approximate static lift from sampled ground elevations, metres; excludes pressure and friction. */
export async function fetchLift(
  intake: readonly [number, number],
  fieldPoints: readonly (readonly [number, number])[],
): Promise<number> {
  if (!fieldPoints.length || fieldPoints.length > 20) throw new Error("Provide 1–20 field points");
  const { default: proj4 } = await import("proj4");
  const elevations = await Promise.all(
    [intake, ...fieldPoints].map(async ([lat, lon]) => {
      if (!Number.isFinite(lat) || !Number.isFinite(lon) || lat < 49 || lat > 55 || lon < 14 || lon > 25)
        throw new Error("Invalid coordinates");
      const [east, north] = proj4(
        "EPSG:4326",
        "+proj=tmerc +lat_0=0 +lon_0=19 +k=0.9993 +x_0=500000 +y_0=-5300000 +ellps=GRS80 +units=m +no_defs",
        [lon, lat],
      );
      const result = await json(`/api/irrigation-elevation?x=${north.toFixed(2)}&y=${east.toFixed(2)}`);
      if (typeof result.elevation !== "number" || !Number.isFinite(result.elevation))
        throw new Error("Elevation unavailable");
      return result.elevation as number;
    }),
  );
  return Math.max(...elevations.slice(1)) - elevations[0];
}
