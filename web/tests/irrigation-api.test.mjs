import { test } from "node:test";
import assert from "node:assert/strict";
import { irrigationApi } from "../irrigation-api.mjs";
import crops from "../../api/irrigation-crops.mjs";
import elevation from "../../api/irrigation-elevation.mjs";

function response() {
  return {
    headers: {},
    setHeader(k, v) {
      this.headers[k] = v;
    },
    status(n) {
      this.statusCode = n;
      return this;
    },
    json(v) {
      this.value = v;
    },
    end(v) {
      this.value = v;
    },
  };
}
test("adapter passes unknown routes through and rejects non-GET", () => {
  let next = false;
  irrigationApi({ url: "/other", method: "GET" }, response(), () => {
    next = true;
  });
  assert.equal(next, true);
  const res = response();
  irrigationApi({ url: "/api/irrigation-crops", method: "POST" }, res, () => {});
  assert.equal(res.statusCode, 405);
});
test("rejects oversized crop requests and invalid elevations before networking", async () => {
  const a = response();
  await crops({ query: { bbox: "16,52,17,53" } }, a);
  assert.equal(a.statusCode, 400);
  const b = response();
  await elevation({ query: { x: "NaN", y: "1" } }, b);
  assert.equal(b.statusCode, 400);
});
test("elevation handler rejects non-numeric service response", async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async () => ({ ok: true, text: async () => "<html>login</html>" });
  try {
    const res = response();
    await elevation({ query: { x: "495114", y: "344582" } }, res);
    assert.equal(res.statusCode, 502);
  } finally {
    globalThis.fetch = original;
  }
});
