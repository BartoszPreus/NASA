import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { fetchCrops, loadPilotLayers, type MapCollection, type MapFeature } from "./feeds";
import type { LatLng, PlanResult } from "./engine";
import type { Field, Source } from "./farm";
import { pl } from "./farm";

type Props = {
  field: Field;
  source?: Source;
  plan?: PlanResult;
  radius: number;
  drawing: boolean;
  locating: boolean;
  excluding: boolean;
  onCancel: () => void;
  onRing: (ring: LatLng[], crop: string, origin: string, holes?: LatLng[][]) => void;
  onSource: (pin: LatLng) => void;
};
const orthoUrl = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/StandardResolution";
const label = (s: string) => {
  const el = document.createElement("span");
  el.textContent = s;
  return el;
};

export function fromGeoJSON(raw: unknown): LatLng[][] {
  const item = raw as { type?: string; geometry?: unknown; coordinates?: unknown; features?: unknown[] };
  if (item?.type === "Feature") return fromGeoJSON(item.geometry);
  if (item?.type === "FeatureCollection" && item.features?.length === 1) return fromGeoJSON(item.features[0]);
  if (item?.type !== "Polygon" || !Array.isArray(item.coordinates) || !item.coordinates.length) {
    throw new Error("Wybierz jeden wielokąt GeoJSON w układzie WGS84.");
  }
  return item.coordinates.map((ring: unknown) => {
    if (!Array.isArray(ring) || ring.length < 4 || ring.length > 1001)
      throw new Error("Niepoprawna granica pola lub ponad 1000 wierzchołków.");
    const points: LatLng[] = ring.map((p) => {
      if (
        !Array.isArray(p) ||
        !Number.isFinite(p[0]) ||
        !Number.isFinite(p[1]) ||
        p[0] < 14 ||
        p[0] > 24.3 ||
        p[1] < 48.9 ||
        p[1] > 55
      )
        throw new Error("Sprawdź współrzędne pola w Polsce.");
      return [p[1], p[0]];
    });
    if (points[0][0] !== points.at(-1)![0] || points[0][1] !== points.at(-1)![1])
      throw new Error("Pierścień GeoJSON powinien być zamknięty.");
    return points.slice(0, -1);
  });
}
export default function FieldMap(props: Props) {
  const box = useRef<HTMLDivElement>(null),
    map = useRef<L.Map | null>(null);
  const latest = useRef(props);
  latest.current = props;
  const [pilot, setPilot] = useState<{ crops: MapCollection; water: MapCollection }>();
  const [live, setLive] = useState<MapCollection>();
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false),
    [draft, setDraft] = useState<LatLng[]>([]);
  const [parcels, setParcels] = useState(true),
    [water, setWater] = useState(true),
    [layout, setLayout] = useState(true);
  const [choice, setChoice] = useState<MapFeature>(),
    [coords, setCoords] = useState("");
  useEffect(() => {
    let active = true;
    const m = L.map(box.current!, {
      zoomControl: false,
      preferCanvas: true,
      maxZoom: 20,
      minZoom: 6,
      scrollWheelZoom: false,
    });
    map.current = m;
    const ortho = L.tileLayer
      .wms(orthoUrl, {
        layers: "Raster",
        format: "image/jpeg",
        version: "1.1.1",
        maxZoom: 20,
        attribution: 'Ortofotomapa © <a href="https://www.geoportal.gov.pl/pl/dane/ortofotomapa-orto/">GUGiK</a>',
      })
      .addTo(m);
    let tileLoaded = false;
    ortho.on("tileload", () => {
      tileLoaded = true;
    });
    ortho.on("tileerror", () => {
      if (!tileLoaded && active)
        setMessage("Ortofotomapa jest chwilowo niedostępna. Granice pól są nadal widoczne.");
    });
    L.control.zoom({ position: "topright", zoomInTitle: "Przybliż", zoomOutTitle: "Oddal" }).addTo(m);
    L.control.scale({ imperial: false, position: "bottomleft" }).addTo(m);
    m.on("click", (e: L.LeafletMouseEvent) => {
      if (latest.current.drawing) {
        setDraft((points) => (points.length < 500 ? [...points, [e.latlng.lat, e.latlng.lng]] : points));
      } else if (latest.current.locating) latest.current.onSource([e.latlng.lat, e.latlng.lng]);
    });
    const resize = new ResizeObserver(() => m.invalidateSize());
    resize.observe(box.current!);
    loadPilotLayers()
      .then((data) => {
        if (active) setPilot(data);
      })
      .catch(() => {
        if (active) setMessage("Nie udało się wczytać warstw pilotażowych.");
      });
    return () => {
      active = false;
      resize.disconnect();
      m.remove();
      map.current = null;
    };
  }, []);
  useEffect(() => {
    setChoice(undefined);
    map.current?.fitBounds(L.latLngBounds(props.field.polygon).pad(0.55), { animate: false, maxZoom: 17 });
  }, [props.field.id]);
  useEffect(() => {
    setDraft([]);
    setChoice(undefined);
  }, [props.drawing, props.locating]);
  useEffect(() => {
    const m = map.current;
    if (!m) return;
    const g = L.layerGroup().addTo(m);
    const active = !props.drawing && !props.locating;
    const display = (collection: MapCollection | undefined, wet: boolean) => {
      for (const feature of collection?.features ?? []) {
        const geometry = feature.geometry;
        const polys =
          geometry.type === "Polygon"
            ? [geometry.coordinates as number[][][]]
            : (geometry.coordinates as number[][][][]);
        for (const rings of polys) {
          const outline = rings.map((r) => r.map(([x, y]) => [y, x] as LatLng));
          const shape = L.polygon(outline, {
            color: wet ? "#3293db" : "#f4d394",
            weight: wet ? 2 : 1,
            fillColor: wet ? "#258ed0" : "#d0aa5f",
            fillOpacity: wet ? 0.65 : 0.18,
            interactive: active,
            bubblingMouseEvents: false,
          }).addTo(g);
          if (active)
            shape.bindTooltip(
              label(wet ? "Woda stojąca · BDOT10k" : feature.properties.crop || "Deklaracja ARiMR"),
            );
          shape.on("click", () => {
            if (!active) return;
            if (wet) {
              setMessage(
                "Zbiornik BDOT10k. Aby wykorzystać go w planie, dodaj własne ujęcie i potwierdź dostęp oraz wydajność.",
              );
              return;
            }
            setChoice({ ...feature, geometry: { type: "Polygon", coordinates: rings } });
          });
        }
      }
    };
    if (parcels) display(live ?? pilot?.crops, false);
    if (water) display(pilot?.water, true);
    L.polygon([props.field.polygon, ...props.field.holes], {
      color: "#235735",
      weight: 5,
      fillOpacity: 0,
      interactive: false,
    }).addTo(g);
    L.polygon([props.field.polygon, ...props.field.holes], {
      color: "#d3fa85",
      weight: 2.5,
      fillColor: "#8bb34b",
      fillOpacity: 0.24,
      interactive: false,
    }).addTo(g);
    if (layout && !props.drawing && !props.locating) {
      props.plan?.steps.forEach((s, i) => {
        if (s.position) {
          L.circle(s.position, {
            radius: props.radius,
            color: "#e7f2ff",
            weight: 1,
            dashArray: "4 5",
            fillColor: "#8ad2ed",
            fillOpacity: 0.11,
            interactive: false,
          }).addTo(g);
          L.circleMarker(s.position, {
            radius: 4.5,
            color: "#12495a",
            weight: 2,
            fillColor: "#d5f3ff",
            fillOpacity: 1,
            bubblingMouseEvents: false,
          })
            .addTo(g)
            .bindTooltip(label(`Stanowisko ${i + 1} · ${pl(s.minutes, 0)} min`));
        } else if (s.lane)
          L.polyline(s.lane, { color: "#bdebf9", weight: 4 })
            .addTo(g)
            .bindTooltip(label(`Pas ${i + 1} · ${pl(s.minutes, 0)} min`));
      });
    }
    if (props.source?.pin)
      L.circleMarker(props.source.pin, {
        radius: 7,
        color: "#fff",
        weight: 2.5,
        fillColor: "#096bba",
        fillOpacity: 1,
        interactive: active,
      })
        .addTo(g)
        .bindTooltip(label(props.source.name));
    if (draft.length) {
      L.polyline(draft, { color: "#f9efba", dashArray: "5 4", interactive: false }).addTo(g);
      for (const p of draft)
        L.circleMarker(p, {
          radius: 4,
          color: "#252b1d",
          fillColor: "#fff6b4",
          fillOpacity: 1,
          interactive: false,
        }).addTo(g);
    }
    return () => {
      g.remove();
    };
  }, [
    pilot,
    live,
    props.field.polygon,
    props.field.holes,
    props.source,
    props.plan,
    props.radius,
    draft,
    props.drawing,
    props.locating,
    parcels,
    water,
    layout,
  ]);
  async function search() {
    if (!map.current || busy) return;
    const b = map.current.getBounds();
    if (b.getEast() - b.getWest() > 0.099 || b.getNorth() - b.getSouth() > 0.099) {
      setMessage("Przybliż mapę do okolicy pola i ponów pobieranie.");
      return;
    }
    setBusy(true);
    setChoice(undefined);
    try {
      const data = await fetchCrops([b.getWest(), b.getSouth(), b.getEast(), b.getNorth()]);
      setLive(data);
      setParcels(true);
      setMessage(
        `ARiMR · kampania 2026 · pobrano ${data.features.length} deklaracji.${data.truncated ? " Przybliż mapę, aby pobrać pozostałe." : ""}`,
      );
    } catch {
      setMessage("Brak odpowiedzi ARiMR. Możesz narysować pole lub zaimportować GeoJSON.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="farm-map">
      <div className="farm-map-head">
        <h2>Mapa pól</h2>
        <button onClick={() => map.current?.fitBounds(L.latLngBounds(props.field.polygon).pad(0.55))}>
          Pokaż moje pole
        </button>
      </div>
      <div className="farm-canvas-wrap">
        <div
          ref={box}
          className={"farm-canvas" + (props.drawing || props.locating ? " marking" : "")}
          aria-label="Mapa pól i ujęć wody"
        />
        {(props.drawing || props.locating) && (
          <div className="farm-map-prompt" role="status">
            {props.drawing
              ? `Klikaj narożniki ${props.excluding ? "wyłączenia" : "pola"} (${draft.length}).`
              : "Kliknij punkt poboru wody."}
            {props.drawing && (
              <>
                <button disabled={!draft.length} onClick={() => setDraft((d) => d.slice(0, -1))}>
                  Cofnij punkt
                </button>
                <button disabled={draft.length < 3} onClick={() => props.onRing(draft, "", "Granica narysowana")}>
                  Zapisz granicę
                </button>
              </>
            )}
            <button onClick={props.onCancel}>Anuluj</button>
          </div>
        )}
        {choice && (
          <div className="farm-map-prompt">
            <span>{choice.properties.crop} · ARiMR 2026</span>
            <button
              onClick={() => {
                try {
                  const [ring, ...holes] = fromGeoJSON(choice);
                  props.onRing(ring, choice.properties.crop ?? "", "ARiMR · kampania 2026", holes);
                  setChoice(undefined);
                } catch (e) {
                  setMessage((e as Error).message);
                }
              }}
            >
              Dodaj to pole
            </button>
            <button onClick={() => setChoice(undefined)}>Zamknij</button>
          </div>
        )}
      </div>
      <div className="farm-layers">
        {(
          [
            [parcels, setParcels, "Uprawy ARiMR"],
            [water, setWater, "Wody BDOT10k"],
            [layout, setLayout, "Rozstaw"],
          ] as const
        ).map(([on, set, name]) => (
          <label key={name}>
            <input type="checkbox" checked={on} onChange={(e) => set(e.target.checked)} />
            {name}
          </label>
        ))}
      </div>
      <div className="farm-map-controls">
        <button disabled={busy} onClick={search}>
          {busy ? "Pobieranie…" : "Pobierz uprawy w widoku"}
        </button>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const p = coords
              .trim()
              .split(/[,;\s]+/)
              .map(Number);
            if (
              p.length !== 2 ||
              p[0] < 48.9 ||
              p[0] > 55 ||
              p[1] < 14 ||
              p[1] > 24.3 ||
              p.some((n) => !Number.isFinite(n))
            ) {
              setMessage("Wpisz szerokość i długość geograficzną w Polsce, np. 52.30, 16.72.");
              return;
            }
            map.current?.setView([p[0], p[1]], 16);
            setMessage("");
          }}
        >
          <input
            aria-label="Współrzędne pola"
            placeholder="52.30, 16.72"
            value={coords}
            onChange={(e) => setCoords(e.target.value)}
          />
          <button>Szukaj</button>
        </form>
      </div>
      {message && (
        <p className="farm-note" role="status">
          {message}
        </p>
      )}
      <p className="farm-credit">
        Granice upraw ARiMR 2026. Wody stojące BDOT10k w obszarze pilotażowym pod Poznaniem. Dane pilotażowe
        pobrano {pilot?.crops.retrievedAt ?? "2026-11-21"} i przeliczono do WGS84.{" "}
        <a href="https://wody.isok.gov.pl/hydroportal.html" target="_blank" rel="noreferrer">
          Hydroportal Polski
        </a>
      </p>
    </section>
  );
}
