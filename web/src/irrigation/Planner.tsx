import { useEffect, useMemo, useRef, useState } from "react";
import FieldMap, { fromGeoJSON } from "./FieldMap";
import { MachineForm, WaterForm } from "./AssetForms";
import { Choice, Confirmation, NumberBox as N, TextBox } from "./Controls";
import { WeatherForm, weatherInputs } from "./WeatherForm";
import {
  calculateBalance,
  dailyDepletion,
  planIrrigation,
  type LatLng,
  type BalanceResult,
  type PlanResult,
} from "./engine";
import {
  areaM2,
  cropDefaults,
  cropProfiles,
  exampleFarm,
  localDay,
  newField,
  newMachine,
  newSource,
  pl,
  readFarm,
  storageKey,
  uid,
  type Farm,
  type Field,
  type Machine,
  type Source,
} from "./farm";
import { fetchWeather } from "./feeds";
import "./planner.css";

const tabs = ["Pole", "Woda", "Sprzęt", "Pogoda"] as const;
type Tab = (typeof tabs)[number];
function initialFarm() {
  try {
    return { farm: readFarm() ?? exampleFarm(), error: "" };
  } catch {
    return {
      farm: exampleFarm(),
      error: "Nie można odczytać pamięci przeglądarki. Zmiany w tej sesji mogą nie zostać zapisane.",
    };
  }
}
export default function Planner() {
  const [initial] = useState(initialFarm),
    [farm, setFarm] = useState(initial.farm);
  const current = useRef(farm);
  const memoryOnly = useRef(Boolean(initial.error));
  current.current = farm;
  const [warning, setWarning] = useState(initial.error),
    [notice, setNotice] = useState("");
  const [tab, setTab] = useState<Tab>("Pole"),
    [mark, setMark] = useState<"draw" | "pin" | "exclude" | null>(null);
  const [scenario, setScenario] = useState<"dry" | "rain">("dry"),
    [meter, setMeter] = useState("");
  const upload = useRef<HTMLInputElement>(null),
    mapArea = useRef<HTMLDivElement>(null);
  const formArea = useRef<HTMLDivElement>(null);
  const field = farm.fields.find((f) => f.id === farm.active)!;
  const source = farm.sources.find((x) => x.id === field.source);
  const machine = farm.machines.find((x) => x.id === field.machine);
  const area = areaM2(field.polygon) - field.holes.reduce((a, r) => a + areaM2(r), 0);
  useEffect(() => {
    scrollTo(0, 0);
    const listener = (e: StorageEvent) => {
      if (e.key !== storageKey || memoryOnly.current) return;
      try {
        const saved = readFarm();
        if (saved) {
          current.current = saved;
          setFarm(saved);
        }
      } catch {
        setWarning("Zmiana z drugiej karty ma nieprawidłowy format.");
      }
    };
    addEventListener("storage", listener);
    return () => removeEventListener("storage", listener);
  }, []);
  function mutate(fn: (s: Farm) => Farm) {
    let base = current.current;
    try {
      if (!memoryOnly.current) base = readFarm() ?? base;
    } catch {
      /* Keep the current session if local storage fails. */
    }
    const next = fn(base);
    current.current = next;
    setFarm(next);
    if (memoryOnly.current) return;
    try {
      localStorage.setItem(storageKey, JSON.stringify(next));
    } catch {
      memoryOnly.current = true;
      setWarning("Brak miejsca lub dostępu do pamięci. Zmiany zachowano tylko w otwartej karcie.");
    }
  }
  function edit(patch: Partial<Field>) {
    mutate((s) => ({ ...s, fields: s.fields.map((f) => (f.id === field.id ? { ...f, ...patch } : f)) }));
  }
  function focusMap(action: "draw" | "pin" | "exclude") {
    setMark(action);
    mapArea.current?.scrollIntoView({ block: "start" });
  }
  function addRing(polygon: LatLng[], crop: string, origin: string, holes: LatLng[][] = []) {
    if (
      polygon.length < 3 ||
      polygon.some(([lat, lon]) => lat < 48.9 || lat > 55 || lon < 14 || lon > 24.3) ||
      areaM2(polygon) < 1
    ) {
      setNotice("Wskaż co najmniej trzy różne narożniki pola w Polsce.");
      return;
    }
    if (mark === "exclude") {
      edit({ holes: [...field.holes, polygon] });
      setMark(null);
      setNotice("Dodano wyłączenie. Stanowiska zraszające ten obszar są pomijane.");
      return;
    }
    const f = newField(polygon, crop, origin, holes);
    f.mode = "feed";
    f.name = `Pole ${farm.fields.filter((x) => !x.example).length + 1}`;
    f.source = farm.sources.find((x) => !x.example)?.id ?? "";
    f.machine = farm.machines.find((x) => !x.example)?.id ?? "";
    mutate((s) => ({ ...s, fields: [...s.fields, f], active: f.id }));
    setMark(null);
    setTab("Pole");
    setNotice("Dodano pole. Uzupełnij uprawę, glebę, ujęcie i zestaw.");
    setMeter("");
    formArea.current?.scrollIntoView({ block: "start" });
    const center = polygon.reduce(
      ([lat, lon], p) => [lat + p[0] / polygon.length, lon + p[1] / polygon.length],
      [0, 0],
    );
    void fetchWeather(center[0], center[1])
      .then((weather) => {
        mutate((s) => ({
          ...s,
          fields: s.fields.map((item) =>
            item.id === f.id && !item.weather
              ? { ...item, weather: { ...weather, retrieved: new Date().toISOString() } }
              : item,
          ),
        }));
      })
      .catch(() => {
        if (current.current.active === f.id)
          setNotice("Pogoda niedostępna. W zakładce Pogoda możesz ponowić pobranie lub wpisać dane ręcznie.");
      });
  }
  const calc = useMemo(() => {
    let balance: BalanceResult | undefined, plan: PlanResult | undefined;
    let gross = 0,
      net = 0,
      waiting = false;
    try {
      const w = weatherInputs(field, farm.runs);
      balance = calculateBalance({
        fieldCapacity: field.fc,
        wiltingPoint: field.wp,
        rootDepthM: field.root,
        depletionFraction: field.p,
        initialDepletionMm: field.depletion,
        kc: field.kc,
        observations: w.observed,
        forecastEt0Mm: w.et,
        forecastRainMm: w.rain,
        efficiency: field.efficiency,
        targetDepletionMm: field.target,
      });
      const deficit = scenario === "dry" ? balance.dryDepletionMm : balance.wetDepletionMm;
      waiting = deficit < balance.rawMm;
      net = waiting ? 0 : Math.max(0, deficit - field.target);
      if (!waiting && net === 0) throw new Error("Ustaw docelowy deficyt poniżej progu podlewania.");
      gross = net / field.efficiency;
      if (!field.confirmed || !field.crop.trim())
        throw new Error("Potwierdź uprawę i parametry gleby w zakładce Pole.");
      if (waiting) return { balance, plan, gross, net, waiting, error: "" };
      if (!source?.confirmed || !source.pin || (!field.example && source.example))
        throw new Error("Dodaj potwierdzone ujęcie z punktem poboru w zakładce Woda.");
      if (!machine?.confirmed || (!field.example && machine.example))
        throw new Error("Dodaj i potwierdź parametry zestawu w zakładce Sprzęt.");
      if (
        w.wind == null ||
        !Number.isFinite(w.wind) ||
        w.wind < 0 ||
        !Number.isFinite(machine.maxWindKmh) ||
        machine.maxWindKmh <= 0
      )
        throw new Error("Podaj wiatr w oknie pracy i dopuszczalny wiatr zestawu.");
      if (w.wind > machine.maxWindKmh)
        throw new Error(
          `Wiatr ${pl(w.wind)} km/h przekracza limit zestawu ${pl(machine.maxWindKmh)} km/h. Wybierz spokojniejsze okno i wpisz jego prognozę.`,
        );
      const equipment = machine.type === "sprinkler" ? machine.sprinkler : machine.reel;
      plan = planIrrigation({
        polygon: field.polygon,
        holes: field.holes,
        equipment,
        intake: source.pin,
        hoseLengthM: machine.length,
        grossDoseMm: gross,
        infiltrationMmH: field.infiltration,
        supply: {
          flowM3h: Math.min(source.flow, machine.pumpFlow),
          pressureBar: machine.pressure,
          liftM: field.lift,
          frictionBar: machine.friction,
          fittingsBar: machine.fittings,
          availableM3: source.stock,
          availableHours: machine.hours,
          powerKw: machine.kw,
        },
        waterPriceM3: source.rate,
        energyPriceKwh: machine.energyPrice,
        labourPriceH: machine.labour,
      });
      return { balance, plan, gross, net, waiting, error: "" };
    } catch (e) {
      return { balance, plan, gross, net, waiting, error: (e as Error).message };
    }
  }, [field, source, machine, scenario, farm.runs]);
  const { plan, balance } = calc;
  const hours = plan?.steps.reduce((a, s) => a + s.minutes / 60, 0) ?? 0;
  const runs = farm.runs.filter((r) => r.fieldId === field.id);
  async function record() {
    const volume = Number(meter),
      token = uid(),
      date = localDay(),
      id = field.id;
    if (
      !source ||
      !Number.isFinite(volume) ||
      volume <= 0 ||
      area <= 0 ||
      !(field.efficiency > 0 && field.efficiency <= 1)
    ) {
      setNotice("Podaj dodatni odczyt zużycia, sprawność i prawidłową granicę pola.");
      return;
    }
    const save = () => {
      mutate((s) => {
        const intake = s.sources.find((x) => x.id === source.id);
        if (!intake?.confirmed || volume > intake.stock) {
          setNotice("Zużycie przekracza zapisany zasób lub ujęcie wymaga potwierdzenia.");
          return s;
        }
        const run = {
          id: token,
          fieldId: id,
          sourceId: intake.id,
          date,
          m3: volume,
          netMm: ((volume * 1000) / area) * field.efficiency,
        };
        setNotice("Zapisano zużycie i przeliczono bilans pola oraz zasób ujęcia.");
        setMeter("");
        return {
          ...s,
          runs: [...s.runs, run],
          sources: s.sources.map((x) => (x.id === intake.id ? { ...x, stock: x.stock - volume } : x)),
        };
      });
    };
    if (navigator.locks) await navigator.locks.request(storageKey, save);
    else save();
  }
  return (
    <article className="farm">
      <header className="farm-heading">
        <div>
          <h1>Planer nawadniania</h1>
          <p>Dobierz dawkę, ujęcie i ustawienie deszczowni na swoim polu.</p>
        </div>
        <button className="farm-primary farm-add" onClick={() => focusMap("draw")}>
          ＋ Narysuj pole
        </button>
      </header>
      {warning && (
        <p className="farm-alert" role="alert">
          {warning}
        </p>
      )}
      {notice && (
        <p className="farm-notice" role="status">
          {notice}
          <button aria-label="Zamknij komunikat" onClick={() => setNotice("")}>
            ×
          </button>
        </p>
      )}
      <div className="farm-work">
        <div className="farm-left">
          <div ref={mapArea} className="farm-anchor">
            <FieldMap
              field={field}
              source={source}
              plan={plan}
              radius={machine?.sprinkler.radiusM ?? 0}
              drawing={mark === "draw" || mark === "exclude"}
              excluding={mark === "exclude"}
              locating={mark === "pin"}
              onCancel={() => setMark(null)}
              onRing={addRing}
              onSource={(pin) => {
                if (source)
                  mutate((s) => ({
                    ...s,
                    sources: s.sources.map((x) => (x.id === source.id ? { ...x, pin, confirmed: false } : x)),
                  }));
                setMark(null);
                setTab("Woda");
                formArea.current?.scrollIntoView({ block: "start" });
              }}
            />
          </div>
          <section className="farm-result" id="farm-result">
            <h2>Plan dla pola</h2>
            <div className="farm-scenarios" aria-label="Scenariusz opadów">
              {(
                [
                  ["dry", "Bez deszczu"],
                  ["rain", "Z prognozowanym opadem"],
                ] as const
              ).map(([s, title]) => (
                <button key={s} aria-pressed={scenario === s} onClick={() => setScenario(s)}>
                  {title}
                </button>
              ))}
            </div>
            <h3>
              {calc.error
                ? "Potrzebne dane"
                : calc.waiting
                  ? "Można odłożyć podlewanie"
                  : plan?.feasible
                    ? "Plan mieści się w podanych limitach"
                    : "Sprawdź ograniczenia zestawu"}
            </h3>
            {calc.error && <p role="status">{calc.error}</p>}
            {balance && (
              <p>
                Deficyt po dobie {pl(scenario === "dry" ? balance.dryDepletionMm : balance.wetDepletionMm)} mm przy
                progu {pl(balance.rawMm)} mm.
              </p>
            )}
            {!calc.error && (
              <div className="farm-metrics">
                <div>
                  <strong>{pl(calc.gross)}</strong>
                  <span>mm brutto · {pl(calc.net)} netto</span>
                </div>
                <div>
                  <strong>{pl(plan?.requiredM3 ?? 0)}</strong>
                  <span>m³ potrzeba</span>
                </div>
                <div>
                  <strong>{pl(hours)}</strong>
                  <span>h pompowania</span>
                </div>
                <div>
                  <strong>{pl(plan?.costPln ?? 0)}</strong>
                  <span>zł za możliwy przebieg</span>
                </div>
              </div>
            )}
            {!calc.error && source && machine && field.usualMm > 0 && (calc.waiting || plan?.feasible) && (
              <details>
                <summary>Porównaj ze zwykłą dawką {pl(field.usualMm)} mm</summary>
                <PassComparison
                  area={area}
                  baseline={field.usualMm}
                  machine={machine}
                  source={source}
                  plan={plan}
                  waiting={calc.waiting}
                />
              </details>
            )}
            {balance && field.mode === "feed" && field.weather && !calc.error && (
              <details>
                <summary>Deficyt na kolejne dni bez podlewania</summary>
                <ForecastTable field={field} balance={balance} />
              </details>
            )}
            {plan && (
              <>
                <p>
                  Geometryczny zasięg {pl(100 * plan.coverageFraction, 0)}% pola. Poza granicą ok.{" "}
                  {pl(plan.oversprayM2, 0)} m². Po poborze pozostaje {pl(plan.remainingM3)} m³.
                </p>
                <ul>
                  {plan.explanations.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
                {plan.steps.length > 0 && (
                  <details>
                    <summary>
                      Kolejność pracy · {plan.steps.length} {machine?.type === "reel" ? "pasów" : "stanowisk"}
                    </summary>
                    <div className="farm-scroll">
                      <table>
                        <thead>
                          <tr>
                            <th>Poz.</th>
                            <th>Współrzędne / trasa</th>
                            <th>min</th>
                            <th>m³</th>
                          </tr>
                        </thead>
                        <tbody>
                          {plan.steps.map((s, i) => (
                            <tr key={i}>
                              <td>{i + 1}</td>
                              <td>
                                {(s.position ? [s.position] : (s.lane ?? []))
                                  .map((p) => p.map((n) => n.toFixed(5)).join(", "))
                                  .join(" → ")}
                              </td>
                              <td>{pl(s.minutes)}</td>
                              <td>{pl(s.volumeM3)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </details>
                )}
              </>
            )}
            <details>
              <summary>Dziennik podlewania · {runs.length}</summary>
              {runs.length > 0 && (
                <ul>
                  {runs
                    .slice(-20)
                    .reverse()
                    .map((r) => (
                      <li key={r.id}>
                        {r.date} · {pl(r.m3)} m³ · {pl(r.netMm)} mm netto
                      </li>
                    ))}
                </ul>
              )}
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  void record();
                }}
                className="farm-row"
              >
                <label className="farm-input">
                  <span>Dzisiejsze zużycie z licznika (m³)</span>
                  <input
                    type="number"
                    min="0.001"
                    step="any"
                    required
                    value={meter}
                    onChange={(e) => setMeter(e.target.value)}
                  />
                </label>
                <button disabled={!source?.confirmed}>Zapisz zużycie</button>
              </form>
            </details>
          </section>
        </div>
        <section ref={formArea} className="farm-panel farm-anchor">
          <div className="farm-context">
            <Choice
              label="Moje pola"
              value={field.id}
              set={(active) => {
                mutate((s) => ({ ...s, active }));
                setMark(null);
                setMeter("");
                setNotice("");
              }}
            >
              {farm.fields.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.name}
                </option>
              ))}
            </Choice>
            <div className="farm-size">
              {pl(area / 10000, 2)} <small>ha</small>
            </div>
          </div>
          {field.example && (
            <p className="farm-demo">
              Przykład obliczeniowy. Narysuj własne pole lub kliknij deklarację na mapie.
            </p>
          )}
          <div className="farm-tabs" aria-label="Dane planu">
            {tabs.map((t) => (
              <button
                key={t}
                aria-pressed={tab === t}
                onClick={() => {
                  setTab(t);
                  setMark(null);
                }}
              >
                {t}
              </button>
            ))}
          </div>
          <div className="farm-form">
            {tab === "Pole" && (
              <>
                <h2>Uprawa i gleba</h2>
                <div className="farm-grid">
                  <TextBox label="Nazwa pola" value={field.name} set={(name) => edit({ name })} />
                  <N
                    label="Rok zbioru"
                    value={field.season}
                    step={1}
                    set={(season) => edit({ season, confirmed: false })}
                  />
                  <label className="farm-input">
                    <span>Uprawa</span>
                    <input
                      aria-label="Uprawa"
                      list="farm-crops"
                      value={field.crop}
                      onChange={(e) => edit(cropDefaults(e.target.value, field.stage))}
                    />
                    <datalist id="farm-crops">
                      {cropProfiles.map((c) => (
                        <option key={c.name}>{c.name}</option>
                      ))}
                    </datalist>
                  </label>
                  <Choice label="Faza rozwoju" value={field.stage} set={(s) => edit(cropDefaults(field.crop, s))}>
                    {["Początkowa", "Pełnia sezonu", "Końcowa"].map((s) => (
                      <option key={s}>{s}</option>
                    ))}
                  </Choice>
                </div>
                <p className="farm-note">
                  {field.origin} · {field.polygon.length} wierzchołków. Sprawdź uprawę po siewie i po zbiorach.
                </p>
                <div className="farm-actions">
                  <button onClick={() => upload.current?.click()}>Importuj pole GeoJSON</button>
                  <button onClick={() => focusMap("exclude")}>Narysuj wyłączenie</button>
                  {field.holes.length > 0 && (
                    <button onClick={() => edit({ holes: field.holes.slice(0, -1) })}>
                      Cofnij ostatnie wyłączenie
                    </button>
                  )}
                  <input
                    hidden
                    type="file"
                    ref={upload}
                    accept=".json,.geojson,application/geo+json"
                    onChange={async (e) => {
                      const file = e.target.files?.[0];
                      e.target.value = "";
                      if (!file) return;
                      try {
                        if (file.size > 2000000) throw new Error("Plik powinien mieć mniej niż 2 MB.");
                        const [ring, ...holes] = fromGeoJSON(JSON.parse(await file.text()));
                        addRing(ring, "", "Import GeoJSON", holes);
                      } catch (err) {
                        setNotice((err as Error).message);
                      }
                    }}
                  />
                </div>
                <details open>
                  <summary>Bilans wody w glebie</summary>
                  <div className="farm-grid">
                    <N
                      label="Deficyt początkowy"
                      value={field.depletion}
                      set={(depletion) => edit({ depletion })}
                      unit="mm"
                    />
                    <N
                      label="Deficyt po nawodnieniu"
                      value={field.target}
                      set={(target) => edit({ target })}
                      unit="mm"
                    />
                    <N label="Głębokość korzeni" value={field.root} set={(root) => edit({ root })} unit="m" />
                    <N label="Współczynnik uprawy Kc" value={field.kc} set={(kc) => edit({ kc })} />
                  </div>
                </details>
                <details>
                  <summary>Parametry gleby i sprawność</summary>
                  <p className="farm-note">Dostosuj wartości początkowe do pomiarów na polu.</p>
                  <div className="farm-grid">
                    <N label="Pojemność polowa" value={field.fc} set={(fc) => edit({ fc })} max={1} unit="m³/m³" />
                    <N label="Punkt więdnięcia" value={field.wp} set={(wp) => edit({ wp })} max={1} unit="m³/m³" />
                    <N
                      label="Zwykła dawka brutto"
                      value={field.usualMm}
                      set={(usualMm) => edit({ usualMm })}
                      unit="mm"
                    />
                    <N label="Frakcja wyczerpania p" value={field.p} set={(p) => edit({ p })} max={1} />
                    <N
                      label="Sprawność aplikacji"
                      value={field.efficiency}
                      set={(efficiency) => edit({ efficiency })}
                      max={1}
                    />
                    <N
                      label="Udział opadu wsiąkającego"
                      value={field.rainFraction}
                      set={(rainFraction) => edit({ rainFraction })}
                      max={1}
                    />
                    <N
                      label="Infiltracja gleby"
                      value={field.infiltration}
                      set={(infiltration) => edit({ infiltration })}
                      unit="mm/h"
                    />
                  </div>
                </details>
                <Confirmation checked={field.confirmed} set={(confirmed) => edit({ confirmed })}>
                  Potwierdzam uprawę, fazę i parametry glebowe dla tego pola.
                </Confirmation>
              </>
            )}
            {tab === "Woda" && (
              <>
                <h2>Źródła wody</h2>
                <WaterForm
                  key={field.id + field.source}
                  items={farm.sources}
                  item={source}
                  field={field}
                  select={(id) => edit({ source: id, lift: 0 })}
                  add={() => {
                    const x = newSource();
                    mutate((s) => ({
                      ...s,
                      sources: [...s.sources, x],
                      fields: s.fields.map((f) => (f.id === field.id ? { ...f, source: x.id, lift: 0 } : f)),
                    }));
                  }}
                  update={(patch) =>
                    mutate((s) => ({
                      ...s,
                      sources: s.sources.map((x) => (x.id === field.source ? { ...x, ...patch } : x)),
                    }))
                  }
                  pin={() => focusMap("pin")}
                  editField={edit}
                />
              </>
            )}
            {tab === "Sprzęt" && (
              <>
                <h2>Wyposażenie gospodarstwa</h2>
                <MachineForm
                  items={farm.machines}
                  item={machine}
                  field={field}
                  select={(machine) => edit({ machine })}
                  add={() => {
                    const m = newMachine();
                    mutate((s) => ({
                      ...s,
                      machines: [...s.machines, m],
                      fields: s.fields.map((f) => (f.id === field.id ? { ...f, machine: m.id } : f)),
                    }));
                  }}
                  update={(patch) =>
                    mutate((s) => ({
                      ...s,
                      machines: s.machines.map((x) => (x.id === field.machine ? { ...x, ...patch } : x)),
                    }))
                  }
                />
              </>
            )}
            {tab === "Pogoda" && (
              <>
                <h2>Pogoda i pomiary</h2>
                <WeatherForm key={field.id} field={field} edit={edit} />
              </>
            )}
            <a
              className="farm-to-result"
              href="#farm-result"
              onClick={(e) => {
                e.preventDefault();
                document.getElementById("farm-result")?.scrollIntoView();
              }}
            >
              Pokaż wynik obliczeń
            </a>
          </div>
          <p className="farm-private">
            Pola, sprzęt i dziennik zapisują się w tej przeglądarce. Pobranie danych przestrzennych wysyła
            współrzędne do dostawcy.
          </p>
        </section>
      </div>
    </article>
  );
}

function PassComparison({
  area,
  baseline,
  machine,
  source,
  plan,
  waiting,
}: {
  area: number;
  baseline: number;
  machine: Machine;
  source: Source;
  plan?: PlanResult;
  waiting: boolean;
}) {
  const volume = (area * baseline) / 1000;
  const e = machine.type === "reel" ? machine.reel : machine.sprinkler;
  const time = volume / e.flowM3h;
  const comparable = Boolean(plan && plan.steps.length && !waiting);
  const moves = (Math.max(0, (plan?.steps.length ?? 0) - 1) * e.moveMinutes) / 60;
  const cost = volume * source.rate + time * machine.kw * machine.energyPrice + (time + moves) * machine.labour;
  return (
    <p>
      Zwykły przejazd wymaga {pl(volume)} m³. Różnica poboru względem planu wynosi{" "}
      {pl(volume - (plan?.requiredM3 ?? 0))} m³.
      {comparable && volume <= source.stock && time + moves <= machine.hours
        ? ` Przy tych samych stanowiskach i stawkach koszt zwykłej dawki wynosi ${pl(cost)} zł, a różnica ${pl(cost - plan!.costPln)} zł.`
        : " Koszt porównaj dla wykonalnego przejazdu o znanej liczbie przestawień."}{" "}
      To porównanie jednego zabiegu. Wynik sezonowy zależy od następnych podlewań i plonu.
    </p>
  );
}
function ForecastTable({ field, balance }: { field: Field; balance: BalanceResult }) {
  let d = balance.observedDepletionMm;
  const rows = [];
  for (const day of field.weather?.forecast ?? []) {
    if (day.date < localDay()) continue;
    if (day.et0Mm == null || day.rainMm == null) break;
    d = dailyDepletion(d, balance.tawMm, balance.rawMm, day.et0Mm * field.kc, day.rainMm * field.rainFraction);
    rows.push(
      <tr key={day.date}>
        <td>{day.date}</td>
        <td>{pl(d)}</td>
        <td>{d >= balance.rawMm ? "Osiągnięty" : "Poniżej"}</td>
      </tr>,
    );
  }
  return (
    <table>
      <thead>
        <tr>
          <th>Dzień</th>
          <th>Deficyt mm</th>
          <th>Próg podlewania</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
  );
}
