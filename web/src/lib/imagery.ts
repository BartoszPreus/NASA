// Live satellite imagery for any patch, loaded by the browser straight from an open WMS (no download step).
// Sentinel-2 cloudless 2016 by EOX (layer "s2cloudless", EPSG:4326), CC BY 4.0: cloud-free mosaic at 10 m,
// CORS enabled, no key. Chosen over NASA GIBS after a comparison at Peary Land, Putorana, Puna, Tibet and
// Atacama: Landsat WELD has no data north of about 80 N and scan stripes, MODIS true colour is cloudy and
// 250 m, Blue Marble is 500 m. The later EOX years (2018+) are CC BY-NC-SA, so they are not used.

export const LIVE_IMAGE_CREDIT =
  "Sentinel-2 cloudless 2016 by EOX IT Services GmbH (contains modified Copernicus Sentinel data 2016), CC BY 4.0";
export const LIVE_IMAGE_URL = "https://s2maps.eu";

const WMS = "https://tiles.maps.eox.at/wms";
const KM_PER_DEG = 111.32;

/** [latMin, lonMin, latMax, lonMax] of a square of `km` on the ground centred on lat, lon (north up). */
export function squareBbox(lat: number, lon: number, km: number): [number, number, number, number] {
  const dLat = km / 2 / KM_PER_DEG;
  const dLon = dLat / Math.max(0.05, Math.cos((lat * Math.PI) / 180));
  return [lat - dLat, lon - dLon, lat + dLat, lon + dLon];
}

export function liveImageUrl(lat: number, lon: number, km: number, px: number): string {
  const [a, b, c, d] = squareBbox(lat, lon, km);
  // WMS 1.1.1 with EPSG:4326 takes the bbox as lon,lat order
  const bbox = [b, a, d, c].map((v) => v.toFixed(5)).join(",");
  const q = new URLSearchParams({
    SERVICE: "WMS",
    REQUEST: "GetMap",
    VERSION: "1.1.1",
    LAYERS: "s2cloudless",
    STYLES: "",
    SRS: "EPSG:4326",
    BBOX: bbox,
    WIDTH: String(px),
    HEIGHT: String(px),
    FORMAT: "image/jpeg",
  });
  return `${WMS}?${q.toString()}`;
}
