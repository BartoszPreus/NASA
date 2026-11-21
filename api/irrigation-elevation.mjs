export default async function handler(req, res) {
  const x = Number(req.query.x),
    y = Number(req.query.y);
  if (!Number.isFinite(x) || !Number.isFinite(y) || x < 100000 || x > 900000 || y < 100000 || y > 900000)
    return res.status(400).json({ error: "Invalid Polish projected coordinates" });
  try {
    const u = new URL("https://services.gugik.gov.pl/nmt/");
    u.searchParams.set("request", "GetHByXY");
    u.searchParams.set("x", String(x));
    u.searchParams.set("y", String(y));
    const response = await fetch(u, { signal: AbortSignal.timeout(12000) });
    if (!response.ok) throw Error();
    const raw = (await response.text()).trim();
    if (!/^-?\d+(?:\.\d+)?$/.test(raw)) throw Error();
    const elevation = Number(raw);
    if (!Number.isFinite(elevation) || elevation < -100 || elevation > 3000) throw Error();
    res.setHeader("Cache-Control", "public, s-maxage=86400");
    return res.status(200).json({ elevation });
  } catch {
    return res.status(502).json({ error: "Elevation unavailable or outside coverage" });
  }
}
