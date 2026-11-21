import { useState } from "react";
import { NumberBox as N, Choice, TextBox } from "./Controls";
import { fetchSatellite, fetchWeather, type SatelliteScene } from "./feeds";
import { localDay, pl, type Field } from "./farm";
import type { Observation } from "./engine";
import type { Run } from "./farm";

export function replayDates(start: string, today = localDay()) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(start) || start > today)
    throw new Error("Podaj datę początkową najpóźniej z dzisiaj.");
  const dates: string[] = [];
  const t = new Date(start + "T12:00:00Z");
  for (; t.toISOString().slice(0, 10) < today; t.setUTCDate(t.getUTCDate() + 1)) {
    if (dates.length >= 30) throw new Error("Podaj stan gleby z ostatnich 30 dni.");
    dates.push(t.toISOString().slice(0, 10));
  }
  return dates;
}
export function weatherInputs(f: Field, runs: Run[]) {
  const today = localDay();
  if (!Number.isFinite(f.rainFraction) || f.rainFraction < 0 || f.rainFraction > 1)
    throw new Error("Udział opadu wsiąkającego musi być w zakresie 0–1.");
  const dates = replayDates(f.initialDate, today);
  const observed: Observation[] = dates.map((date) => {
    const daily = f.mode === "feed" ? f.weather?.past.find((d) => d.date === date) : undefined;
    const rain = f.rainObserved[date] ?? daily?.rainMm;
    const et = f.etObserved[date] ?? daily?.et0Mm;
    if (rain == null || et == null) throw new Error(`Uzupełnij opad i ET₀ za ${date} w zakładce Pogoda.`);
    return {
      date,
      rainMm: rain * f.rainFraction,
      et0Mm: et,
      irrigationNetMm: runs.filter((r) => r.fieldId === f.id && r.date === date).reduce((v, r) => v + r.netMm, 0),
    };
  });
  const applied = runs.filter((r) => r.fieldId === f.id && r.date === today).reduce((v, r) => v + r.netMm, 0);
  if (applied > 0) observed.push({ date: today, et0Mm: 0, rainMm: 0, irrigationNetMm: applied });
  if (f.mode === "manual") {
    if (f.manualDate !== today) throw new Error("Zaktualizuj datę i ręczną prognozę na dzisiaj.");
    if (!Number.isFinite(f.rain) || f.rain < 0) throw new Error("Uzupełnij prognozę opadu w mm.");
    return { observed, et: f.et0, rain: f.rain * f.rainFraction, wind: f.windKmh };
  }
  const day = f.weather?.forecast.find((d) => d.date === today);
  if (
    !day ||
    day.et0Mm == null ||
    day.rainMm == null ||
    !f.weather ||
    Date.now() - Date.parse(f.weather.retrieved) > 24 * 3600000
  )
    throw new Error("Pobierz aktualną prognozę albo wpisz dane ręcznie.");
  return { observed, et: day.et0Mm, rain: day.rainMm * f.rainFraction, wind: day.windKmh };
}

export function WeatherForm({ field: f, edit }: { field: Field; edit: (patch: Partial<Field>) => void }) {
  const [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false);
  const [scene, setScene] = useState<SatelliteScene | null>(),
    [sr, setSr] = useState(""),
    [sb, setSb] = useState(false);
  const center = f.polygon.reduce(
    ([lat, lon], p) => [lat + p[0] / f.polygon.length, lon + p[1] / f.polygon.length],
    [0, 0],
  );
  async function getWeather() {
    setBusy(true);
    try {
      const w = await fetchWeather(center[0], center[1]);
      edit({ weather: { ...w, retrieved: new Date().toISOString() }, mode: "feed" });
      setMessage("Pobrano historię modelową i prognozę dla pola.");
    } catch {
      setMessage("Pogoda niedostępna. Ponów pobieranie lub wpisz prognozę ręcznie.");
    } finally {
      setBusy(false);
    }
  }
  async function satellite() {
    setSb(true);
    setSr("");
    try {
      const s = await fetchSatellite(center[0], center[1]);
      setScene(s);
      if (!s) setSr("Brak niedawnej sceny spełniającej kryterium zachmurzenia.");
    } catch {
      setSr("Katalog Copernicus nie odpowiedział.");
    } finally {
      setSb(false);
    }
  }
  let days: string[] = [];
  try {
    days = replayDates(f.initialDate);
  } catch {
    /* The balance reports invalid dates. */
  }
  return (
    <>
      <div className="farm-actions">
        <button className="farm-primary" onClick={getWeather} disabled={busy}>
          {busy ? "Pobieranie…" : "Pobierz pogodę dla pola"}
        </button>
      </div>
      <Choice label="Dane do bilansu" value={f.mode} set={(m) => edit({ mode: m as Field["mode"] })}>
        <option value="manual">Wpis własny</option>
        <option value="feed">Open-Meteo</option>
      </Choice>
      {f.mode === "manual" && (
        <div className="farm-grid">
          <TextBox
            type="date"
            label="Data prognozy"
            value={f.manualDate}
            set={(manualDate) => edit({ manualDate })}
          />
          <N label="Wiatr w oknie pracy" value={f.windKmh} set={(windKmh) => edit({ windKmh })} unit="km/h" />
          <N label="Przewidywany deszcz" value={f.rain} set={(rain) => edit({ rain })} unit="mm/d" />
          <N label="Przewidywana ET₀" value={f.et0} set={(et0) => edit({ et0 })} unit="mm/d" />
        </div>
      )}
      {message && <p role="status">{message}</p>}
      {f.weather && (
        <>
          <p className="farm-note">
            <a href="https://open-meteo.com/" target="_blank" rel="noreferrer">
              Open-Meteo
            </a>{" "}
            · ostatnie pobranie {new Date(f.weather.retrieved).toLocaleString("pl-PL")}. Historia jest estymacją
            modelową.
          </p>
          <table>
            <caption>Prognoza dla środka pola</caption>
            <thead>
              <tr>
                <th>Dzień</th>
                <th>Deszcz mm</th>
                <th>ET₀ mm</th>
                <th>Wiatr maks. km/h</th>
              </tr>
            </thead>
            <tbody>
              {f.weather.forecast.map((d) => (
                <tr key={d.date}>
                  <td>{d.date.slice(5)}</td>
                  {[d.rainMm, d.et0Mm, d.windKmh].map((v, i) => (
                    <td key={i}>{pl(v ?? NaN)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          <details>
            <summary>Opady i ET₀ w ostatnim tygodniu</summary>
            <table>
              <thead>
                <tr>
                  <th>Dzień</th>
                  <th>Opad mm</th>
                  <th>ET₀ mm</th>
                </tr>
              </thead>
              <tbody>
                {f.weather.past.map((d) => (
                  <tr key={d.date}>
                    <td>{d.date}</td>
                    <td>{pl(d.rainMm ?? NaN)}</td>
                    <td>{pl(d.et0Mm ?? NaN)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </details>
        </>
      )}
      <TextBox
        label="Data pomiaru początkowego (rano)"
        type="date"
        value={f.initialDate}
        set={(initialDate) => edit({ initialDate })}
      />
      {days.length > 0 && (
        <details>
          <summary>Korekty danych dobowych ({days.length})</summary>
          {days.map((date) => {
            const model = f.mode === "feed" ? f.weather?.past.find((d) => d.date === date) : undefined;
            return (
              <div key={date}>
                <strong>{date}</strong>
                <div className="farm-grid">
                  <N
                    label="Opad z deszczomierza"
                    value={f.rainObserved[date] ?? model?.rainMm ?? NaN}
                    set={(v) => edit({ rainObserved: { ...f.rainObserved, [date]: v } })}
                    unit="mm"
                  />
                  <N
                    label="ET₀"
                    value={f.etObserved[date] ?? model?.et0Mm ?? NaN}
                    set={(v) => edit({ etObserved: { ...f.etObserved, [date]: v } })}
                    unit="mm"
                  />
                </div>
              </div>
            );
          })}
        </details>
      )}
      <p className="farm-note">
        Bilans sumuje opad i wykonane podlewanie od daty pomiaru. Dwa warianty na dziś pokazują wpływ
        prognozowanego deszczu.
      </p>
      <details>
        <summary>Obserwacja satelitarna Sentinel-2</summary>
        <button onClick={satellite} disabled={sb}>
          {sb ? "Wyszukiwanie…" : "Sprawdź ostatnią scenę"}
        </button>
        {scene && (
          <p>
            {scene.date.slice(0, 10)} · zachmurzenie całej sceny {pl(scene.cloudPercent)}%.{" "}
            <a href={scene.url} target="_blank" rel="noreferrer">
              Otwórz obszar w Copernicus Browser
            </a>
          </p>
        )}
        {sr && <p role="status">{sr}</p>}
        <p className="farm-note">
          Stan roślin oceń na zdjęciu i w terenie. Bilans korzysta z danych o wodzie w glebie.
        </p>
      </details>
    </>
  );
}
