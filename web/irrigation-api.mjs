import crops from "../api/irrigation-crops.mjs";
import satellite from "../api/irrigation-satellite.mjs";
import elevation from "../api/irrigation-elevation.mjs";
const routes = {
  "/api/irrigation-crops": crops,
  "/api/irrigation-satellite": satellite,
  "/api/irrigation-elevation": elevation,
};
export function irrigationApi(req, res, next) {
  const url = new URL(req.url, "http://localhost");
  const handler = routes[url.pathname];
  if (!handler) return next();
  if (req.method !== "GET") {
    res.statusCode = 405;
    return res.end();
  }
  const request = { query: Object.fromEntries(url.searchParams) };
  const response = {
    setHeader: (key, value) => res.setHeader(key, value),
    status(code) {
      res.statusCode = code;
      return this;
    },
    json(data) {
      res.setHeader("Content-Type", "application/json");
      res.end(JSON.stringify(data));
    },
  };
  Promise.resolve(handler(request, response)).catch(() => {
    if (!res.headersSent) {
      res.statusCode = 500;
      res.end();
    }
  });
}
