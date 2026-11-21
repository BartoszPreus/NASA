import { useState } from "react";
import { NumberBox as N, Choice, TextBox, Confirmation } from "./Controls";
import { fetchLift } from "./feeds";
import type { Field, Machine, Source } from "./farm";
import { pl } from "./farm";

export function WaterForm({
  items,
  item,
  field,
  select,
  add,
  update,
  pin,
  editField,
}: {
  items: Source[];
  item?: Source;
  field: Field;
  select: (id: string) => void;
  add: () => void;
  update: (s: Partial<Source>) => void;
  pin: () => void;
  editField: (s: Partial<Field>) => void;
}) {
  const [terrain, setTerrain] = useState(""),
    [busy, setBusy] = useState(false);
  async function elevation() {
    if (!item?.pin) return;
    setBusy(true);
    try {
      const points = field.polygon.filter((_, i) => i % Math.ceil(field.polygon.length / 18) === 0);
      const delta = await fetchLift(item.pin, points);
      editField({ lift: Math.max(0, delta) });
      setTerrain(
        `GUGiK NMT · najwyższy z ${points.length} punktów granicy względem ujęcia: ${pl(delta)} m. Sprawdź przebieg węża i lustro wody.`,
      );
    } catch {
      setTerrain("Brak odczytu NMT. Wpisz zmierzone podnoszenie do najwyższej dyszy.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="farm-row">
        <Choice label="Ujęcie dla pola" value={item?.id ?? ""} set={select}>
          <option value="">Wybierz ujęcie</option>
          {items
            .filter((x) => field.example || !x.example)
            .map((x) => (
              <option key={x.id} value={x.id}>
                {x.name}
              </option>
            ))}
        </Choice>
        <button onClick={add}>Dodaj ujęcie</button>
      </div>
      {item && (
        <>
          <div className="farm-grid">
            <TextBox label="Nazwa ujęcia" value={item.name} set={(name) => update({ name })} />
            <Choice label="Rodzaj źródła" value={item.kind} set={(kind) => update({ kind })}>
              {["Studnia", "Staw", "Zbiornik deszczówki", "Ujęcie powierzchniowe", "Przyłącze", "Dostawa"].map(
                (t) => (
                  <option key={t}>{t}</option>
                ),
              )}
            </Choice>
            <N label="Wydajność ujęcia" value={item.flow} set={(flow) => update({ flow })} unit="m³/h" />
            <N label="Pozostały zasób / limit" value={item.stock} set={(stock) => update({ stock })} unit="m³" />
            <N label="Cena pobranej wody" value={item.rate} set={(rate) => update({ rate })} unit="zł/m³" />
            <N label="Podnoszenie do dyszy" value={field.lift} set={(lift) => editField({ lift })} unit="m" />
          </div>
          <div className="farm-actions">
            <button onClick={pin}>{item.pin ? "Przenieś punkt poboru" : "Wskaż punkt poboru"}</button>
            <button disabled={!item.pin || busy} onClick={elevation}>
              {busy ? "Pobieranie NMT…" : "Oblicz podnoszenie z NMT"}
            </button>
          </div>
          {item.pin && <p className="farm-note">Punkt poboru {item.pin.map((n) => pl(n, 5)).join(" / ")}</p>}
          {terrain && (
            <p className="farm-note" role="status">
              {terrain}
            </p>
          )}
          <Confirmation checked={item.confirmed} set={(confirmed) => update({ confirmed })}>
            Potwierdzam dostęp, dopuszczalny pobór i dostępny zasób tego ujęcia.
          </Confirmation>
        </>
      )}
    </>
  );
}
export function MachineForm({
  items,
  item,
  field,
  select,
  add,
  update,
}: {
  items: Machine[];
  item?: Machine;
  field: Field;
  select: (id: string) => void;
  add: () => void;
  update: (s: Partial<Machine>) => void;
}) {
  const equip = item?.type === "reel" ? item.reel : item?.sprinkler;
  function change(key: string, value: number) {
    if (item && equip)
      update(
        item.type === "reel"
          ? { reel: { ...item.reel, [key]: value } }
          : { sprinkler: { ...item.sprinkler, [key]: value } },
      );
  }
  return (
    <>
      <div className="farm-row">
        <Choice label="Zestaw dla pola" value={item?.id ?? ""} set={select}>
          <option value="">Wybierz zestaw</option>
          {items
            .filter((x) => field.example || !x.example)
            .map((x) => (
              <option key={x.id} value={x.id}>
                {x.name}
              </option>
            ))}
        </Choice>
        <button onClick={add}>Dodaj zestaw</button>
      </div>
      {item && equip && (
        <>
          <div className="farm-grid">
            <TextBox label="Nazwa zestawu" value={item.name} set={(name) => update({ name })} />
            <Choice label="Urządzenie" value={item.type} set={(type) => update({ type: type as Machine["type"] })}>
              <option value="sprinkler">Zraszacz przenośny</option>
              <option value="reel">Deszczownia szpulowa</option>
            </Choice>
            <N
              label="Wydatek dyszy / szpuli"
              value={equip.flowM3h}
              set={(v) => change("flowM3h", v)}
              unit="m³/h"
            />
            <N
              label="Wymagane ciśnienie"
              value={equip.pressureBar}
              set={(v) => change("pressureBar", v)}
              unit="bar"
            />
            {equip.kind === "sprinkler" ? (
              <>
                <N label="Promień zraszania" value={equip.radiusM} set={(v) => change("radiusM", v)} unit="m" />
                <N label="Rozstaw stanowisk" value={equip.spacingM} set={(v) => change("spacingM", v)} unit="m" />
              </>
            ) : (
              <>
                <N
                  label="Szerokość pasa"
                  value={equip.stripWidthM}
                  set={(v) => change("stripWidthM", v)}
                  unit="m"
                />
                <N
                  label="Długość rozwinięcia"
                  value={equip.maxLaneM}
                  set={(v) => change("maxLaneM", v)}
                  unit="m"
                />
                <N
                  label="Szczytowa intensywność"
                  value={equip.peakRateMmH ?? NaN}
                  set={(v) => change("peakRateMmH", v)}
                  unit="mm/h"
                />
              </>
            )}
            <N label="Przestawienie" value={equip.moveMinutes} set={(v) => change("moveMinutes", v)} unit="min" />
          </div>
          <details open>
            <summary>Pompa i przewody</summary>
            <p className="farm-note">
              Wpisz ciśnienie i przepływ zmierzone jednocześnie przy tej samej prędkości pompy.
            </p>
            <div className="farm-grid">
              <N
                label="Przepływ roboczy"
                value={item.pumpFlow}
                set={(pumpFlow) => update({ pumpFlow })}
                unit="m³/h"
              />
              <N
                label="Ciśnienie robocze"
                value={item.pressure}
                set={(pressure) => update({ pressure })}
                unit="bar"
              />
              <N label="Wąż zasilający" value={item.length} set={(length) => update({ length })} unit="m" />
              <N
                label="Straty w przewodzie"
                value={item.friction}
                set={(friction) => update({ friction })}
                unit="bar"
              />
              <N
                label="Straty na złączkach"
                value={item.fittings}
                set={(fittings) => update({ fittings })}
                unit="bar"
              />
            </div>
          </details>
          <details>
            <summary>Czas i koszty pracy</summary>
            <div className="farm-grid">
              <N
                label="Dopuszczalny wiatr"
                value={item.maxWindKmh}
                set={(maxWindKmh) => update({ maxWindKmh })}
                unit="km/h"
              />
              <N label="Dostępne okno pracy" value={item.hours} set={(hours) => update({ hours })} unit="h" />
              <N label="Pobór mocy" value={item.kw} set={(kw) => update({ kw })} unit="kW" />
              <N
                label="Cena energii"
                value={item.energyPrice}
                set={(energyPrice) => update({ energyPrice })}
                unit="zł/kWh"
              />
              <N
                label="Koszt godziny pracy"
                value={item.labour}
                set={(labour) => update({ labour })}
                unit="zł/h"
              />
            </div>
          </details>
          <Confirmation checked={item.confirmed} set={(confirmed) => update({ confirmed })}>
            Parametry odpowiadają mojej pompie, przewodom i dyszy.
          </Confirmation>
        </>
      )}
    </>
  );
}
