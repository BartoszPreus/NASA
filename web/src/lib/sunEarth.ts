// Sun geometry of a place on Earth from its latitude alone (no terrain, no atmosphere), for the "low sun"
// criterion. At the lunar south pole the Sun never rises more than about 1.5° above the horizon plus the
// local latitude offset (lunar obliquity 1.54°), so the candidate regions at 84–89.8° S see it at 0–7°:
// long shadows, a horizon-grazing light that rovers and cameras must cope with (NASA VIPER, Artemis).

const D2R = Math.PI / 180;
const OBLIQUITY_EARTH = 23.44;
export const OBLIQUITY_MOON = 1.54;
export const LOW_SUN_DEG = 10;

export interface SunStats {
  /** share of daylight hours over a year with the Sun below LOW_SUN_DEG */
  lowShare: number;
  /** median Sun elevation over daylight hours, degrees */
  medianElev: number;
  /** highest noon elevation of the year (summer solstice), degrees */
  maxNoon: number;
  /** lowest noon elevation of the year, degrees (negative = polar night) */
  minNoon: number;
  /** shadow length of a 1 m object at the median daylight elevation, metres */
  shadowAtMedian: number;
  /** noon elevation for each of 73 five-day steps through the year */
  noonCurve: number[];
}

function elev(latR: number, decR: number, hourAngleR: number) {
  return Math.asin(Math.sin(latR) * Math.sin(decR) + Math.cos(latR) * Math.cos(decR) * Math.cos(hourAngleR)) / D2R;
}

const cache = new Map<number, SunStats>();

export function sunStats(lat: number): SunStats {
  const key = Math.round(lat * 10) / 10;
  const hit = cache.get(key);
  if (hit) return hit;
  const latR = key * D2R;
  const elevs: number[] = [];
  const noonCurve: number[] = [];
  for (let d = 0; d < 365; d += 5) {
    const dec = OBLIQUITY_EARTH * Math.sin((2 * Math.PI * (d - 80)) / 365); // 0 at the March equinox
    const decR = dec * D2R;
    noonCurve.push(elev(latR, decR, 0));
    for (let h = 0; h < 24; h += 0.5) {
      const e = elev(latR, decR, ((h - 12) * 15) * D2R);
      if (e > 0) elevs.push(e);
    }
  }
  elevs.sort((a, b) => a - b);
  const median = elevs.length ? elevs[Math.floor(elevs.length / 2)] : 0;
  const low = elevs.length ? elevs.filter((e) => e < LOW_SUN_DEG).length / elevs.length : 0;
  const s: SunStats = {
    lowShare: low,
    medianElev: median,
    maxNoon: Math.max(...noonCurve),
    minNoon: Math.min(...noonCurve),
    shadowAtMedian: median > 0.5 ? 1 / Math.tan(median * D2R) : Infinity,
    noonCurve,
  };
  cache.set(key, s);
  return s;
}

/** Highest Sun elevation over the lunar year at a lunar latitude (degrees, south negative). */
export const lunarMaxSun = (lat: number) => 90 - Math.abs(lat) + OBLIQUITY_MOON;
